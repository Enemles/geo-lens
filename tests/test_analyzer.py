"""Analyzer fan-out, aggregation, prompt building, and streaming."""

import asyncio

from app.config import Settings
from app.providers.base import LLMProvider
from app.schemas import AnalyzeRequest
from app.services.analyzer import Analyzer, aggregate, build_prompts
from app.services.cache import TTLCache


class FakeProvider(LLMProvider):
    """Returns scripted text and counts calls — no network, fully deterministic."""

    def __init__(self, name: str, answer: str):
        self.name = name
        self._answer = answer
        self.calls = 0

    async def complete(self, prompt: str) -> str:
        self.calls += 1
        await asyncio.sleep(0)
        return self._answer


def _analyzer(providers, *, max_concurrent=5):
    settings = Settings(max_concurrent_calls=max_concurrent)
    return Analyzer(providers, TTLCache(60), settings)


def test_build_prompts_with_category_includes_direct_and_open():
    req = AnalyzeRequest(brand="Yolando", category="AI SEO tools", domain="yolando.ai")
    prompts = build_prompts(req)
    assert any("alternatives" in p.lower() for p in prompts)
    assert any("what do you know about" in p.lower() for p in prompts)
    assert any("yolando.ai" in p for p in prompts)


def test_build_prompts_respects_override():
    req = AnalyzeRequest(brand="X", prompts=["only this"])
    assert build_prompts(req) == ["only this"]


async def test_analyze_fans_out_over_prompts_and_models():
    p1 = FakeProvider("a", "1. Yolando\n2. Other")
    p2 = FakeProvider("b", "Nothing relevant here.")
    analyzer = _analyzer([p1, p2])
    req = AnalyzeRequest(brand="Yolando", category="AI tools")

    summary, results = await analyzer.analyze(req)

    n_prompts = len(build_prompts(req))
    assert len(results) == n_prompts * 2  # 2 providers
    assert p1.calls == n_prompts and p2.calls == n_prompts
    assert {r.model for r in results} == {"a", "b"}


async def test_perfect_provider_scores_100():
    provider = FakeProvider("a", "1. Yolando\n2. Other")
    summary, results = await _analyzer([provider]).analyze(
        AnalyzeRequest(brand="Yolando", category="AI tools")
    )
    assert summary.visibility_score == 100.0
    assert summary.mention_rate == 1.0
    assert summary.recommendation_rate == 1.0


async def test_invisible_brand_scores_zero():
    provider = FakeProvider("a", "1. SomethingElse\n2. Another")
    summary, _ = await _analyzer([provider]).analyze(
        AnalyzeRequest(brand="Yolando", category="AI tools")
    )
    assert summary.visibility_score == 0.0
    assert summary.mention_rate == 0.0


async def test_cache_dedupes_repeated_calls():
    provider = FakeProvider("a", "1. Yolando")
    analyzer = _analyzer([provider])
    req = AnalyzeRequest(brand="Yolando", prompts=["same prompt", "same prompt"])
    await analyzer.analyze(req)
    # Two identical prompts collapse to a single provider call via the cache.
    assert provider.calls == 1


async def test_stream_yields_each_result_then_summary():
    provider = FakeProvider("a", "1. Yolando")
    analyzer = _analyzer([provider])
    req = AnalyzeRequest(brand="Yolando", category="AI tools")
    total_calls = len(build_prompts(req))

    progress, summary = [], None
    async for result, summ, done, total in analyzer.analyze_stream(req):
        if result is not None:
            progress.append((done, total))
        if summ is not None:
            summary = summ

    assert len(progress) == total_calls
    assert progress[-1] == (total_calls, total_calls)
    assert summary is not None and summary.visibility_score > 0


def test_aggregate_handles_empty_results():
    summary = aggregate(AnalyzeRequest(brand="X"), [])
    assert summary.visibility_score == 0.0
    assert summary.mention_rate == 0.0

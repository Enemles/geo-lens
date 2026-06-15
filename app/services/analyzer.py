"""The analyzer: fan out one analysis across prompts x models, then aggregate.

This is where the performance story lives:

* An analysis is N buyer-intent prompts times M assistants. Run sequentially
  that's painfully slow (each LLM call is seconds), so the calls are launched
  concurrently with asyncio.gather / as_completed.
* But you can't fire all of them at once — providers rate-limit and you'll eat
  429s. A single shared Semaphore caps how many calls are in flight at any
  moment, across the whole fan-out.
* Identical (provider, prompt) pairs are de-duplicated through the TTL cache,
  which also collapses stampedes (see cache.py).
"""

import asyncio
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from ..config import Settings
from ..providers.base import LLMProvider
from ..schemas import AnalysisSummary, AnalyzeRequest, MentionResult
from .cache import TTLCache
from .scoring import score_mention


def build_prompts(req: AnalyzeRequest) -> list[str]:
    """Default buyer-intent prompts: a mix of open-category questions (does the
    brand surface unprompted?) and direct questions (does the model know it?)."""
    if req.prompts:
        return req.prompts

    brand = req.brand
    prompts: list[str] = []
    if req.category:
        cat = req.category
        prompts += [
            f"What are the best {cat} available today? List the top options.",
            f"I run marketing for a startup. Which {cat} would you recommend, and why?",
            f"Compare the leading {cat}. Which ones stand out?",
            f"What are the main alternatives to '{brand}' for {cat}?",
        ]
    else:
        prompts += [
            f"What are the main alternatives to '{brand}'?",
            f"Would you recommend '{brand}' to someone in its space? Why or why not?",
        ]

    prompts += [
        f"What do you know about '{brand}'? What does it do and is it well regarded?",
    ]
    if req.domain:
        prompts.append(f"What can you tell me about the company behind {req.domain}?")
    return prompts


class Analyzer:
    def __init__(self, providers: list[LLMProvider], cache: TTLCache, settings: Settings):
        self._providers = providers
        self._cache = cache
        # One shared semaphore => a global ceiling on concurrent LLM calls.
        self._sem = asyncio.Semaphore(settings.max_concurrent_calls)

    def _select(self, names: list[str] | None) -> list[LLMProvider]:
        if not names:
            return self._providers
        wanted = set(names)
        chosen = [p for p in self._providers if p.name in wanted]
        return chosen or self._providers

    async def _one(
        self, req: AnalyzeRequest, prompt: str, provider: LLMProvider
    ) -> MentionResult:
        cache_key = f"{provider.name}::{prompt}"
        async with self._sem:  # hold a concurrency slot for the duration
            start = time.perf_counter()
            text, cached = await self._cache.get_or_set(
                cache_key, lambda: provider.complete(prompt)
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
        return score_mention(
            brand=req.brand,
            aliases=req.aliases,
            prompt=prompt,
            model=provider.name,
            text=text,
            latency_ms=latency_ms,
            cached=cached,
        )

    def _tasks(self, req: AnalyzeRequest):
        prompts = build_prompts(req)
        providers = self._select(req.models)
        return [self._one(req, p, pr) for p in prompts for pr in providers]

    async def analyze(self, req: AnalyzeRequest) -> tuple[AnalysisSummary, list[MentionResult]]:
        results = await asyncio.gather(*self._tasks(req))
        return aggregate(req, results), results

    async def analyze_stream(
        self, req: AnalyzeRequest
    ) -> AsyncIterator[tuple[MentionResult | None, AnalysisSummary | None, int, int]]:
        """Yield each result as it lands (for SSE progress), then a final summary.

        Each yield is (result, summary, done, total): result set while streaming,
        summary set on the final tick.
        """
        tasks = self._tasks(req)
        total = len(tasks)
        results: list[MentionResult] = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            yield result, None, len(results), total
        yield None, aggregate(req, results), total, total


def aggregate(req: AnalyzeRequest, results: list[MentionResult]) -> AnalysisSummary:
    n = len(results) or 1  # guard against an empty run
    visibility = round(sum(r.score for r in results) / n * 100, 1)
    mention_rate = round(sum(r.mentioned for r in results) / n, 3)
    reco_rate = round(sum(r.recommended for r in results) / n, 3)
    return AnalysisSummary(
        id=None,
        brand=req.brand,
        domain=req.domain,
        category=req.category,
        visibility_score=visibility,
        mention_rate=mention_rate,
        recommendation_rate=reco_rate,
        created_at=datetime.now(timezone.utc),
    )

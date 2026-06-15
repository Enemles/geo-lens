"""Turn a model's free-text answer into a visibility score.

Kept deliberately deterministic and dependency-free: the expensive,
nondeterministic part (the LLM) lives in the providers, and everything here is
pure functions that are cheap to run and easy to unit-test. The heuristics are
v1 — the obvious next step is to ask the model for structured output and score
that, but transparent string logic is the right place to start.
"""

import re

from ..schemas import MentionResult

_LIST_ITEM = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+(.*)$")
_RECO_WORDS = (
    "recommend",
    "best",
    "top",
    "great",
    "excellent",
    "leading",
    "popular",
    "strong",
    "ideal",
    "go with",
    "stand out",
    "standout",
)


def _names(brand: str, aliases: list[str]) -> list[str]:
    return [n.lower() for n in (brand, *aliases) if n]


def _mentioned(text_lower: str, names: list[str]) -> bool:
    return any(n in text_lower for n in names)


def _first_rank(text: str, names: list[str]) -> int | None:
    """1-based position of the brand when the answer is a ranked/bulleted list."""
    rank = 0
    for line in text.splitlines():
        m = _LIST_ITEM.match(line)
        if not m:
            continue
        rank += 1
        item = m.group(1).lower()
        if any(n in item for n in names):
            return rank
    return None


def _recommended(text: str, names: list[str], rank: int | None) -> bool:
    # Appearing in a ranked list is itself a recommendation signal...
    if rank is not None:
        return True
    # ...otherwise look for praise within the sentence that names the brand.
    lowered = text.lower()
    for sentence in re.split(r"(?<=[.!?])\s+", lowered):
        if any(n in sentence for n in names) and any(w in sentence for w in _RECO_WORDS):
            return True
    return False


def _excerpt(text: str, names: list[str], width: int = 180) -> str | None:
    lowered = text.lower()
    idx = min((lowered.find(n) for n in names if n in lowered), default=-1)
    if idx < 0:
        return None
    start = max(0, idx - width // 3)
    snippet = text[start : start + width].strip()
    return ("…" if start > 0 else "") + snippet


def _score(mentioned: bool, recommended: bool, rank: int | None) -> float:
    if not mentioned:
        return 0.0
    score = 0.4
    if recommended:
        score += 0.3
    score += {1: 0.3, 2: 0.2, 3: 0.1}.get(rank, 0.05 if rank else 0.0)
    return round(min(score, 1.0), 3)


def score_mention(
    *,
    brand: str,
    aliases: list[str],
    prompt: str,
    model: str,
    text: str,
    latency_ms: int,
    cached: bool,
) -> MentionResult:
    names = _names(brand, aliases)
    text_lower = text.lower()
    mentioned = _mentioned(text_lower, names)
    rank = _first_rank(text, names) if mentioned else None
    recommended = _recommended(text, names, rank) if mentioned else False
    return MentionResult(
        prompt=prompt,
        model=model,
        mentioned=mentioned,
        recommended=recommended,
        rank=rank,
        excerpt=_excerpt(text, names) if mentioned else None,
        score=_score(mentioned, recommended, rank),
        latency_ms=latency_ms,
        cached=cached,
    )

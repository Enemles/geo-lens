"""Deterministic offline provider.

Lets the whole service run with zero API keys and makes tests/demos
reproducible: the same prompt always yields the same answer (seeded by a hash,
not a random source). It mimics how a real assistant behaves — it readily
echoes a brand when asked about it directly, but recommends from a generic pool
when asked an open category question. That gap is exactly the GEO signal:
"models know you when asked, but won't surface you unprompted."
"""

import asyncio
import hashlib
import re

from .base import LLMProvider

_POOL = [
    "BrightRank",
    "Searchlight AI",
    "Mentionable",
    "PromptPeak",
    "Citadel SEO",
    "EchoMetrics",
    "Beacon",
    "Northstar Analytics",
]

# A "Proper Noun" or a 'quoted phrase' in the prompt is treated as the brand
# under test, so direct questions ("What do you know about Yolando?") surface it.
_BRANDISH = re.compile(r"'([^']+)'|\b([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)?)\b")
_STOPWORDS = {"What", "Which", "Is", "Are", "I", "Would", "Compare", "List", "AI"}


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def _brand_in(prompt: str) -> str | None:
    for quoted, proper in _BRANDISH.findall(prompt):
        candidate = (quoted or proper).strip()
        if candidate and candidate.split()[0] not in _STOPWORDS:
            return candidate
    return None


class MockProvider(LLMProvider):
    name = "mock"

    async def complete(self, prompt: str) -> str:
        # Tiny await so it exercises the same async path as real providers.
        await asyncio.sleep(0)
        seed = _seed(prompt)
        picks = [_POOL[(seed >> (i * 3)) % len(_POOL)] for i in range(3)]
        picks = list(dict.fromkeys(picks))  # de-dupe, keep order

        brand = _brand_in(prompt)
        # Surface the brand ~60% of the time *only* when it's named in the prompt.
        if brand and seed % 10 < 6:
            picks.insert(seed % (len(picks) + 1), brand)

        listing = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(picks))
        return (
            "Based on what's commonly discussed, here are some options to consider:\n"
            f"{listing}\n"
            f"The first is generally seen as the strongest fit for most teams."
        )

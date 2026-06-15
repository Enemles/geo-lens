"""Provider abstraction.

GEO means a brand has to be visible across many AI assistants, not one. So the
analyzer never talks to a vendor SDK directly — it talks to this interface, and
each model (Claude, GPT, a deterministic mock) is one implementation. Adding a
new assistant is one new subclass.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    #: Stable label used as a cache key and surfaced in results.
    name: str

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Answer a buyer-intent prompt the way a real assistant would."""

    async def aclose(self) -> None:
        """Release any held resources (HTTP clients). No-op by default."""

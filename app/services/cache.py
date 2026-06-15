"""In-memory TTL cache with stampede protection.

LLM calls are slow and metered, so identical (provider, prompt) lookups are
cached. The non-obvious part is the per-key lock: without it, ten concurrent
requests for a cold key would all miss and all hit the API at once (a cache
stampede). The per-key lock means the first caller fills the entry and the
rest wait and read it. The shape is intentionally Redis-swappable.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

    async def get_or_set(
        self, key: str, factory: Callable[[], Awaitable[Any]]
    ) -> tuple[Any, bool]:
        """Return (value, cached). `cached` is False when `factory` was run."""
        fresh = self._get_fresh(key)
        if fresh is not None:
            return fresh, True

        lock = await self._lock_for(key)
        async with lock:
            # Double-checked: another coroutine may have populated it while we
            # waited for the lock.
            fresh = self._get_fresh(key)
            if fresh is not None:
                return fresh, True
            value = await factory()
            self._store[key] = (time.monotonic() + self._ttl, value)
            return value, False

    def _get_fresh(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def _lock_for(self, key: str) -> asyncio.Lock:
        async with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock

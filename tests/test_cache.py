"""The cache's job is correctness under concurrency, so that's what we test."""

import asyncio

from app.services.cache import TTLCache


async def test_caches_after_first_call():
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return "value"

    v1, cached1 = await TTLCache(60).get_or_set("k", factory)
    assert v1 == "value" and cached1 is False
    assert calls == 1


async def test_second_read_is_cached():
    cache = TTLCache(60)
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return calls

    v1, c1 = await cache.get_or_set("k", factory)
    v2, c2 = await cache.get_or_set("k", factory)
    assert (v1, c1) == (1, False)
    assert (v2, c2) == (1, True)  # same value, served from cache
    assert calls == 1


async def test_stampede_runs_factory_once():
    """Ten concurrent cold reads must hit the factory exactly once."""
    cache = TTLCache(60)
    calls = 0

    async def slow():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return "v"

    results = await asyncio.gather(*[cache.get_or_set("k", slow) for _ in range(10)])
    assert calls == 1
    assert all(v == "v" for v, _ in results)
    assert sum(1 for _, cached in results if not cached) == 1  # one filled it


async def test_expired_entry_refetches():
    cache = TTLCache(0)  # everything expires immediately
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return calls

    await cache.get_or_set("k", factory)
    await asyncio.sleep(0.01)
    _, cached = await cache.get_or_set("k", factory)
    assert cached is False
    assert calls == 2

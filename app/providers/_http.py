"""Shared async HTTP helper with timeout + bounded retries.

Retries on the failures worth retrying — 429s and 5xx and timeouts — with
exponential backoff. Used by every real provider so the resilience policy
lives in exactly one place.
"""

import asyncio

import httpx


async def post_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str],
    payload: dict,
    timeout: float,
    max_retries: int,
) -> dict:
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = await client.post(url, headers=headers, json=payload, timeout=timeout)
            # Retry transient server/rate-limit errors; surface the rest.
            if resp.status_code in (429, 500, 502, 503, 504):
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt == max_retries:
                break
            # 0.5s, 1s, 2s, ... — back off before trying again.
            await asyncio.sleep(0.5 * (2**attempt))
    assert last_exc is not None
    raise last_exc

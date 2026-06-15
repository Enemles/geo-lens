"""Anthropic (Claude) provider — one assistant a buyer might ask."""

import httpx

from ._http import post_json
from .base import LLMProvider

_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, *, timeout: float, max_retries: int):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        # One pooled client per provider — reused across every call so we get
        # connection reuse instead of a fresh TCP+TLS handshake per request.
        self._client = httpx.AsyncClient()

    async def complete(self, prompt: str) -> str:
        data = await post_json(
            self._client,
            _API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload={
                "model": self._model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self._timeout,
            max_retries=self._max_retries,
        )
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")

    async def aclose(self) -> None:
        await self._client.aclose()

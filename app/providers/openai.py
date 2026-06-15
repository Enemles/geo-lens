"""OpenAI (GPT) provider — a second assistant, same interface.

Two real providers behind one interface is the point: GEO visibility differs
per model, so the analyzer queries all of them and compares.
"""

import httpx

from ._http import post_json
from .base import LLMProvider

_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, *, timeout: float, max_retries: int):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient()

    async def complete(self, prompt: str) -> str:
        data = await post_json(
            self._client,
            _API_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
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
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    async def aclose(self) -> None:
        await self._client.aclose()

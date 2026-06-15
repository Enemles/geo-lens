"""Provider registry / factory.

Builds the list of assistants to query from config: the mock is always present
so the service runs offline, and each real provider is added only when its
credentials exist.
"""

from ..config import Settings
from .anthropic import AnthropicProvider
from .base import LLMProvider
from .mock import MockProvider
from .openai import OpenAIProvider

__all__ = ["LLMProvider", "build_providers", "MockProvider"]


def build_providers(settings: Settings) -> list[LLMProvider]:
    providers: list[LLMProvider] = [MockProvider()]
    if settings.anthropic_api_key:
        providers.append(
            AnthropicProvider(
                settings.anthropic_api_key,
                settings.anthropic_model,
                timeout=settings.request_timeout_seconds,
                max_retries=settings.max_retries,
            )
        )
    if settings.openai_api_key:
        providers.append(
            OpenAIProvider(
                settings.openai_api_key,
                settings.openai_model,
                timeout=settings.request_timeout_seconds,
                max_retries=settings.max_retries,
            )
        )
    return providers

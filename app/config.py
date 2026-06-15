"""Application configuration, loaded from environment / .env.

Uses pydantic-settings so config is validated and type-safe — the same
Pydantic foundation the rest of the app is built on.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the default SQLite file to the repo root, so it's the same database no
# matter which directory the server is launched from (a relative path would
# silently create a different db per working directory).
_DEFAULT_SQLITE = Path(__file__).resolve().parent.parent / "geo_lens.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "GEO Lens"
    environment: str = "development"

    # Which providers to query. Any provider with credentials present is
    # registered automatically; "mock" is always available so the service
    # runs offline out of the box.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Concurrency + resilience. An analysis fans out to N prompts x M models,
    # so these guardrails are what keep it fast without tripping rate limits.
    max_concurrent_calls: int = 5
    request_timeout_seconds: float = 30.0
    max_retries: int = 2

    # Cache TTL for (provider, prompt) results. LLM calls are slow and cost
    # money, so identical queries are served from cache within this window.
    cache_ttl_seconds: int = 3600

    # SQLite by default (zero setup); swap to Postgres in prod with one env var.
    database_url: str = f"sqlite:///{_DEFAULT_SQLITE}"

    # Allowed origins for the browser frontend (Next.js dev server by default).
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env is parsed once per process."""
    return Settings()

"""FastAPI application factory + lifespan wiring."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .database import init_db
from .providers import build_providers
from .routers import analysis, stream
from .services.analyzer import Analyzer
from .services.cache import TTLCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()

    # Built once and shared across all requests: the HTTP clients are pooled,
    # the cache is process-wide, and the analyzer's semaphore enforces a single
    # global concurrency ceiling.
    providers = build_providers(settings)
    cache = TTLCache(settings.cache_ttl_seconds)
    app.state.settings = settings
    app.state.providers = providers
    app.state.analyzer = Analyzer(providers, cache, settings)
    try:
        yield
    finally:
        for provider in providers:
            await provider.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="Measure how visible a brand is to AI assistants (GEO).",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(analysis.router)
    app.include_router(stream.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "version": __version__}

    return app


app = create_app()

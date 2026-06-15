"""FastAPI dependency providers.

The Analyzer (and its shared cache + concurrency semaphore) is built once at
startup and stored on app.state, so every request reuses the same pools and the
global rate limit actually holds. These thin functions expose it to routes via
Depends, which is also what makes the routes trivial to test with overrides.
"""

from fastapi import Request

from .services.analyzer import Analyzer


def get_analyzer(request: Request) -> Analyzer:
    return request.app.state.analyzer

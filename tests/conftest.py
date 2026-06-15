"""Test configuration.

Env vars are set BEFORE the app is imported so the engine binds to a throwaway
SQLite file and no real provider keys are picked up (tests run fully offline on
the mock provider). Tables are reset before each test for isolation.
"""

import os
import tempfile

# --- must run before any `app.*` import ---
_db_fd, _DB_PATH = tempfile.mkstemp(suffix=".db", prefix="geo_lens_test_")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402

get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db_file():
    yield
    try:
        os.remove(_DB_PATH)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _fresh_tables():
    """Each test starts from an empty schema."""
    from app import models  # noqa: F401  (register tables on metadata)
    from app.database import engine

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


@pytest.fixture()
def client():
    # `with` triggers the lifespan: builds providers + analyzer onto app.state.
    with TestClient(create_app()) as c:
        yield c

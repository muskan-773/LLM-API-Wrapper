import os

# Must happen BEFORE app is imported.
# Tests should never use your real API key.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import cache, config
from app.main import app
from app.services import usage_store


@pytest.fixture
def client():
    # No "with": we don't want the lifespan
    # to connect to PostgreSQL during tests.
    return TestClient(app)


@pytest.fixture(autouse=True)
def fake_infra(monkeypatch):
    """Replace Redis and Postgres with in-memory fakes."""

    cache_store = {}
    records = []

    async def fake_get(key):
        return cache_store.get(key)

    async def fake_set(key, data, ttl_seconds):
        cache_store[key] = data

    async def fake_add(record):
        records.append(record)

    monkeypatch.setattr(
        cache,
        "get_json",
        fake_get,
    )

    monkeypatch.setattr(
        cache,
        "set_json",
        fake_set,
    )

    monkeypatch.setattr(
        usage_store,
        "add_record",
        fake_add,
    )

    # No retry delays during route tests.
    monkeypatch.setattr(
        config,
        "MAX_RETRIES",
        0,
    )

    return SimpleNamespace(
        cache=cache_store,
        records=records,
    )
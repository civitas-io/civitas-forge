"""Real-Postgres tests for PostgresSpanStore + PostgresStateStore."""

from __future__ import annotations

import time

from civitas_contrib.plugins.postgres_span_store import PostgresSpanStore
from civitas_contrib.plugins.postgres_store import PostgresStateStore
from tests.support import assert_matches_memory, handle, llm, requires_docker


def _hour_aligned() -> float:
    return float((int(time.time()) // 3600) * 3600)


@requires_docker
async def test_postgres_span_store_matches_memory(clean_postgres: str) -> None:
    store = PostgresSpanStore(clean_postgres, retention_days=None)
    try:
        await assert_matches_memory(store, _hour_aligned())
    finally:
        await store.shutdown()


@requires_docker
async def test_postgres_span_store_retention_deletes_old(clean_postgres: str) -> None:
    store = PostgresSpanStore(clean_postgres, retention_days=1)
    try:
        now = time.time()
        old = now - 5 * 86400  # older than 1-day retention
        await store.export([llm("a", "gpt", 0.1, old), handle("a", now)])
        # the old span is swept on export; the recent one survives
        recent = await store.recent_spans(now - 3600, now + 3600, limit=100)
        assert len(recent) == 1
        assert recent[0].agent_name == "a"
    finally:
        await store.shutdown()


@requires_docker
async def test_postgres_state_store_crud(clean_postgres: str) -> None:
    store = PostgresStateStore(clean_postgres)
    try:
        assert await store.get("agent_a") is None
        await store.set("agent_a", {"count": 42, "data": [1, 2, 3]})
        assert await store.get("agent_a") == {"count": 42, "data": [1, 2, 3]}
        await store.set("agent_a", {"count": 43})  # upsert
        assert await store.get("agent_a") == {"count": 43}
        await store.set("agent_b", {"x": 1})
        assert await store.list_agents() == ["agent_a", "agent_b"]
        await store.delete("agent_a")
        assert await store.get("agent_a") is None
        assert await store.list_agents() == ["agent_b"]
    finally:
        await store.close()

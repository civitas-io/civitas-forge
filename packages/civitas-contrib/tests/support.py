"""Shared SpanStore test dataset + equivalence checker.

The strongest proof a driver-backed SpanStore is correct is that it returns the
SAME results as core's reference InMemorySpanStore for identical input -- so each
DB test exports this dataset and asserts every query matches InMemorySpanStore.
"""

from __future__ import annotations

from typing import Any

import pytest
from civitas.observability import InMemorySpanStore
from civitas.observability.span_queue import SpanData

try:
    import testcontainers.mysql  # noqa: F401
    import testcontainers.postgres  # noqa: F401

    _HAS_TESTCONTAINERS = True
except ImportError:
    _HAS_TESTCONTAINERS = False

requires_docker = pytest.mark.skipif(
    not _HAS_TESTCONTAINERS,
    reason="testcontainers not installed (pip install civitas-contrib[dev])",
)


def llm(agent: str, model: str, cost: float, t: float) -> SpanData:
    return SpanData(
        name="civitas.llm.chat",
        trace_id="a" * 32,
        span_id=f"{int(t):016d}",
        parent_span_id=None,
        start_time=t,
        end_time=t + 1.0,
        attributes={
            "civitas.agent.name": agent,
            "civitas.llm.model": model,
            "civitas.llm.tokens_in": 100,
            "civitas.llm.tokens_out": 50,
            "civitas.llm.cost_usd": cost,
        },
        status="ok",
    )


def handle(agent: str, t: float) -> SpanData:
    return SpanData(
        name="civitas.agent.handle",
        trace_id="b" * 32,
        span_id=f"h{int(t):015d}",
        parent_span_id=None,
        start_time=t,
        end_time=t + 0.1,
        attributes={"civitas.agent.name": agent},
        status="ok",
    )


def dataset(now: float) -> list[SpanData]:
    return [
        llm("chatty", "gpt-4o", 0.01, now + 10),
        llm("chatty", "gpt-4o", 0.02, now + 70),  # next minute bucket
        llm("chatty", "claude", 0.05, now + 15),
        llm("other", "gpt-4o", 0.03, now + 20),
        handle("chatty", now + 5),
        handle("chatty", now + 8),
        handle("other", now + 65),
    ]


def _cost_key(b: Any) -> tuple:
    return (b.bucket_start, b.agent_name or "", b.model or "")


def _rate_key(b: Any) -> tuple:
    return (b.bucket_start, b.agent_name or "")


async def assert_matches_memory(store: Any, now: float) -> None:
    """Export the dataset to `store` and assert every query equals the
    InMemorySpanStore reference. `now` is hour-aligned by the caller so the
    minute buckets are deterministic."""
    mem = InMemorySpanStore()
    await store.export(dataset(now))
    await mem.export(dataset(now))

    since, until = now, now + 100

    assert await store.cost_by_agent(since, until) == await mem.cost_by_agent(since, until)
    assert await store.cost_by_model(since, until) == await mem.cost_by_model(since, until)

    s_cost = sorted(await store.cost_over_time(since, until, 60), key=_cost_key)
    m_cost = sorted(await mem.cost_over_time(since, until, 60), key=_cost_key)
    assert [(_cost_key(b), b.total_cost_usd, b.total_tokens_in) for b in s_cost] == [
        (_cost_key(b), b.total_cost_usd, b.total_tokens_in) for b in m_cost
    ]

    s_rate = sorted(await store.message_rate_over_time(since, until, 60), key=_rate_key)
    m_rate = sorted(await mem.message_rate_over_time(since, until, 60), key=_rate_key)
    assert [(_rate_key(b), b.message_count) for b in s_rate] == [
        (_rate_key(b), b.message_count) for b in m_rate
    ]

    s_recent = await store.recent_spans(since, until, limit=3)
    m_recent = await mem.recent_spans(since, until, limit=3)
    assert [r.start_time for r in s_recent] == [r.start_time for r in m_recent]
    assert len(s_recent) == 3

    s_trace = await store.spans_in_trace("a" * 32, since, until)
    m_trace = await mem.spans_in_trace("a" * 32, since, until)
    assert [r.start_time for r in s_trace] == [r.start_time for r in m_trace]
    assert all(r.trace_id == "a" * 32 for r in s_trace)

"""PostgresSpanStore — durable, queryable telemetry store backed by PostgreSQL.

A driver-backed ``SpanStore`` (civitas B4) for deployments that already run
Postgres and want cross-process telemetry aggregation in one place, instead of
core's per-process ``SQLiteSpanStore`` file sets. Requires ``civitas-contrib[postgres]``.

Design (mirrors core's ``SQLiteSpanStore`` semantics so results are identical):

- **Single ``civitas_spans`` table** — no window files. Postgres handles a large
  single table fine; cross-window ATTACH machinery isn't needed, so queries are
  plain time-range ``WHERE`` + ``GROUP BY``.
- **``start_time``/``end_time`` as ``DOUBLE PRECISION``** (epoch seconds), so the
  bucketing math ``FLOOR(start_time / bucket) * bucket`` matches SQLite's
  ``CAST(start_time / bucket AS INTEGER) * bucket`` exactly.
- **Promoted columns** identical to core (``agent_name``/``llm_model``/
  ``llm_tokens_in``/``_out``/``llm_cost_usd``) via the shared, public
  ``civitas.observability.normalize_span`` — never reimplemented here. Full
  attributes kept as ``JSONB`` for drill-down.
- **Retention**: ``retention_days`` (default 180, ~SQLite's 6×30d) piggybacks a
  ``DELETE ... WHERE start_time < cutoff`` on each ``export``; ``None`` disables
  it (operator manages via partitioning/ops).

Usage::

    store = PostgresSpanStore("postgresql://user:pass@host/db")
    runtime = Runtime(supervisor=..., exporters=[store])
"""

from __future__ import annotations

import json
import time
from typing import Any

from civitas.observability import CostBucket, MessageRateBucket, SpanRecord, normalize_span
from civitas.observability.span_queue import SpanData

_TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS civitas_spans (
        id              BIGSERIAL PRIMARY KEY,
        name            TEXT NOT NULL,
        trace_id        TEXT NOT NULL,
        span_id         TEXT NOT NULL,
        parent_span_id  TEXT,
        start_time      DOUBLE PRECISION NOT NULL,
        end_time        DOUBLE PRECISION NOT NULL,
        status          TEXT NOT NULL,
        error_message   TEXT,
        agent_name      TEXT,
        llm_model       TEXT,
        llm_tokens_in   BIGINT,
        llm_tokens_out  BIGINT,
        llm_cost_usd    DOUBLE PRECISION,
        attributes      JSONB NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_civitas_spans_start_time ON civitas_spans(start_time);
    CREATE INDEX IF NOT EXISTS idx_civitas_spans_trace_id ON civitas_spans(trace_id);
    CREATE INDEX IF NOT EXISTS idx_civitas_spans_agent_name ON civitas_spans(agent_name);
"""

# Columns in SpanRecord order -- one place so SELECT and unpacking can't drift.
_SPAN_COLS = (
    "name, trace_id, span_id, parent_span_id, start_time, end_time, status, "
    "error_message, agent_name, llm_model, llm_tokens_in, llm_tokens_out, llm_cost_usd"
)


class PostgresSpanStore:
    """asyncpg-backed ``SpanStore`` (write + query over one schema)."""

    def __init__(
        self,
        url: str,
        min_size: int = 1,
        max_size: int = 10,
        timeout: float = 30.0,
        retention_days: int | None = 180,
    ) -> None:
        self._url = url
        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        self._retention_days = retention_days
        self._pool: Any = None

    # ------------------------------------------------------------------
    # Pool lifecycle (lazy — construction is always safe pre-event-loop)
    # ------------------------------------------------------------------

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            try:
                import asyncpg
            except ImportError as exc:
                raise ImportError(
                    "PostgresSpanStore requires asyncpg. "
                    "Install it with: pip install civitas-contrib[postgres]"
                ) from exc
            self._pool = await asyncpg.create_pool(
                self._url, min_size=self._min_size, max_size=self._max_size, timeout=self._timeout
            )
            async with self._pool.acquire() as conn:
                await conn.execute(_TABLE_DDL)
        return self._pool

    # ------------------------------------------------------------------
    # Write side (ExportBackend contract)
    # ------------------------------------------------------------------

    async def export(self, spans: list[SpanData]) -> None:
        if not spans:
            return
        pool = await self._ensure_pool()
        rows = []
        for span in spans:
            n = normalize_span(span)
            rows.append(
                (
                    span.name,
                    span.trace_id,
                    span.span_id,
                    span.parent_span_id,
                    span.start_time,
                    span.end_time,
                    span.status,
                    span.error_message,
                    n["agent_name"],
                    n["llm_model"],
                    n["llm_tokens_in"],
                    n["llm_tokens_out"],
                    n["llm_cost_usd"],
                    json.dumps(span.attributes),
                )
            )
        async with pool.acquire() as conn:
            await conn.executemany(
                f"""
                INSERT INTO civitas_spans ({_SPAN_COLS}, attributes)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::jsonb)
                """,
                rows,
            )
        await self._sweep_retention()

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _sweep_retention(self) -> None:
        if self._retention_days is None:
            return
        cutoff = time.time() - self._retention_days * 86400
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM civitas_spans WHERE start_time < $1", cutoff)

    # ------------------------------------------------------------------
    # Read side (SpanStore query surface)
    # ------------------------------------------------------------------

    async def cost_over_time(
        self, since: float, until: float, bucket_seconds: int = 86400
    ) -> list[CostBucket]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT FLOOR(start_time / {int(bucket_seconds)}) * {int(bucket_seconds)}
                           AS bucket_start,
                       agent_name, llm_model,
                       SUM(llm_cost_usd), SUM(llm_tokens_in), SUM(llm_tokens_out)
                FROM civitas_spans
                WHERE llm_cost_usd IS NOT NULL AND start_time >= $1 AND start_time <= $2
                GROUP BY bucket_start, agent_name, llm_model
                ORDER BY bucket_start
                """,
                since,
                until,
            )
        return [
            CostBucket(
                bucket_start=r[0],
                agent_name=r[1],
                model=r[2],
                total_cost_usd=r[3] or 0.0,
                total_tokens_in=r[4] or 0,
                total_tokens_out=r[5] or 0,
            )
            for r in rows
        ]

    async def message_rate_over_time(
        self, since: float, until: float, bucket_seconds: int = 3600
    ) -> list[MessageRateBucket]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT FLOOR(start_time / {int(bucket_seconds)}) * {int(bucket_seconds)}
                           AS bucket_start,
                       agent_name, COUNT(*)
                FROM civitas_spans
                WHERE name = 'civitas.agent.handle' AND start_time >= $1 AND start_time <= $2
                GROUP BY bucket_start, agent_name
                ORDER BY bucket_start
                """,
                since,
                until,
            )
        return [
            MessageRateBucket(bucket_start=r[0], agent_name=r[1], message_count=r[2] or 0)
            for r in rows
        ]

    async def cost_by_agent(self, since: float, until: float) -> dict[str, float]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT agent_name, SUM(llm_cost_usd)
                FROM civitas_spans
                WHERE llm_cost_usd IS NOT NULL AND agent_name IS NOT NULL
                  AND start_time >= $1 AND start_time <= $2
                GROUP BY agent_name
                """,
                since,
                until,
            )
        return {r[0]: r[1] or 0.0 for r in rows}

    async def cost_by_model(self, since: float, until: float) -> dict[str, float]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT llm_model, SUM(llm_cost_usd)
                FROM civitas_spans
                WHERE llm_cost_usd IS NOT NULL AND llm_model IS NOT NULL
                  AND start_time >= $1 AND start_time <= $2
                GROUP BY llm_model
                """,
                since,
                until,
            )
        return {r[0]: r[1] or 0.0 for r in rows}

    async def recent_spans(self, since: float, until: float, limit: int = 200) -> list[SpanRecord]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT {_SPAN_COLS} FROM civitas_spans
                WHERE start_time >= $1 AND start_time <= $2
                ORDER BY start_time DESC LIMIT {int(limit)}
                """,
                since,
                until,
            )
        return [SpanRecord(*r) for r in rows]

    async def spans_in_trace(self, trace_id: str, since: float, until: float) -> list[SpanRecord]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT {_SPAN_COLS} FROM civitas_spans
                WHERE trace_id = $1 AND start_time >= $2 AND start_time <= $3
                ORDER BY start_time ASC
                """,
                trace_id,
                since,
                until,
            )
        return [SpanRecord(*r) for r in rows]

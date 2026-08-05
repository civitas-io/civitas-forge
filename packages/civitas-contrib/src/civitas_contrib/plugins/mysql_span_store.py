"""MySQLSpanStore — durable, queryable telemetry store backed by MySQL/MariaDB.

A driver-backed ``SpanStore`` (civitas B4), the MySQL sibling of
``PostgresSpanStore``. Requires ``civitas-contrib[mysql]`` (aiomysql).

Same design as ``PostgresSpanStore`` (single ``civitas_spans`` table, ``DOUBLE``
epoch times so ``FLOOR(start_time / bucket) * bucket`` matches core's SQLite
bucketing exactly, promoted columns via the shared ``normalize_span``, JSON
attributes, ``retention_days`` piggyback sweep). Differences are driver-level:
aiomysql is cursor-based with ``%s`` placeholders and needs an explicit
``commit()`` on writes, and the connection URL is parsed into host/port/user/
password/db (aiomysql takes no DSN string).

Usage::

    store = MySQLSpanStore("mysql://user:pass@host:3306/db")
    runtime = Runtime(supervisor=..., exporters=[store])
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import unquote, urlparse

from civitas.observability import CostBucket, MessageRateBucket, SpanRecord, normalize_span
from civitas.observability.span_queue import SpanData

_TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS civitas_spans (
        id              BIGINT AUTO_INCREMENT PRIMARY KEY,
        name            VARCHAR(255) NOT NULL,
        trace_id        VARCHAR(64) NOT NULL,
        span_id         VARCHAR(64) NOT NULL,
        parent_span_id  VARCHAR(64),
        start_time      DOUBLE NOT NULL,
        end_time        DOUBLE NOT NULL,
        status          VARCHAR(32) NOT NULL,
        error_message   TEXT,
        agent_name      VARCHAR(255),
        llm_model       VARCHAR(255),
        llm_tokens_in   BIGINT,
        llm_tokens_out  BIGINT,
        llm_cost_usd    DOUBLE,
        attributes      JSON NOT NULL,
        INDEX idx_civitas_spans_start_time (start_time),
        INDEX idx_civitas_spans_trace_id (trace_id),
        INDEX idx_civitas_spans_agent_name (agent_name)
    )
"""

_SPAN_COLS = (
    "name, trace_id, span_id, parent_span_id, start_time, end_time, status, "
    "error_message, agent_name, llm_model, llm_tokens_in, llm_tokens_out, llm_cost_usd"
)


def _parse_url(url: str) -> dict[str, Any]:
    """mysql://user:pass@host:port/db -> aiomysql.create_pool kwargs."""
    p = urlparse(url)
    return {
        "host": p.hostname or "localhost",
        "port": p.port or 3306,
        "user": unquote(p.username) if p.username else None,
        "password": unquote(p.password) if p.password else None,
        "db": p.path.lstrip("/") or None,
    }


class MySQLSpanStore:
    """aiomysql-backed ``SpanStore`` (write + query over one schema)."""

    def __init__(
        self,
        url: str,
        min_size: int = 1,
        max_size: int = 10,
        retention_days: int | None = 180,
    ) -> None:
        self._conn_kwargs = _parse_url(url)
        self._min_size = min_size
        self._max_size = max_size
        self._retention_days = retention_days
        self._pool: Any = None

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            try:
                import aiomysql
            except ImportError as exc:
                raise ImportError(
                    "MySQLSpanStore requires aiomysql. "
                    "Install it with: pip install civitas-contrib[mysql]"
                ) from exc
            self._pool = await aiomysql.create_pool(
                minsize=self._min_size,
                maxsize=self._max_size,
                autocommit=True,
                **self._conn_kwargs,
            )
            async with self._pool.acquire() as conn, conn.cursor() as cur:
                await cur.execute(_TABLE_DDL)
        return self._pool

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
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.executemany(
                f"INSERT INTO civitas_spans ({_SPAN_COLS}, attributes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                rows,
            )
        await self._sweep_retention()

    async def shutdown(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def _sweep_retention(self) -> None:
        if self._retention_days is None:
            return
        cutoff = time.time() - self._retention_days * 86400
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute("DELETE FROM civitas_spans WHERE start_time < %s", (cutoff,))

    async def _fetch(self, sql: str, params: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(sql, params)
            return list(await cur.fetchall())

    async def cost_over_time(
        self, since: float, until: float, bucket_seconds: int = 86400
    ) -> list[CostBucket]:
        b = int(bucket_seconds)
        rows = await self._fetch(
            f"""
            SELECT FLOOR(start_time / {b}) * {b} AS bucket_start,
                   agent_name, llm_model,
                   SUM(llm_cost_usd), SUM(llm_tokens_in), SUM(llm_tokens_out)
            FROM civitas_spans
            WHERE llm_cost_usd IS NOT NULL AND start_time >= %s AND start_time <= %s
            GROUP BY bucket_start, agent_name, llm_model
            ORDER BY bucket_start
            """,
            (since, until),
        )
        return [
            CostBucket(
                bucket_start=float(r[0]),
                agent_name=r[1],
                model=r[2],
                total_cost_usd=float(r[3]) if r[3] is not None else 0.0,
                total_tokens_in=int(r[4]) if r[4] is not None else 0,
                total_tokens_out=int(r[5]) if r[5] is not None else 0,
            )
            for r in rows
        ]

    async def message_rate_over_time(
        self, since: float, until: float, bucket_seconds: int = 3600
    ) -> list[MessageRateBucket]:
        b = int(bucket_seconds)
        rows = await self._fetch(
            f"""
            SELECT FLOOR(start_time / {b}) * {b} AS bucket_start, agent_name, COUNT(*)
            FROM civitas_spans
            WHERE name = 'civitas.agent.handle' AND start_time >= %s AND start_time <= %s
            GROUP BY bucket_start, agent_name
            ORDER BY bucket_start
            """,
            (since, until),
        )
        return [
            MessageRateBucket(bucket_start=float(r[0]), agent_name=r[1], message_count=int(r[2]))
            for r in rows
        ]

    async def cost_by_agent(self, since: float, until: float) -> dict[str, float]:
        rows = await self._fetch(
            """
            SELECT agent_name, SUM(llm_cost_usd)
            FROM civitas_spans
            WHERE llm_cost_usd IS NOT NULL AND agent_name IS NOT NULL
              AND start_time >= %s AND start_time <= %s
            GROUP BY agent_name
            """,
            (since, until),
        )
        return {r[0]: float(r[1]) if r[1] is not None else 0.0 for r in rows}

    async def cost_by_model(self, since: float, until: float) -> dict[str, float]:
        rows = await self._fetch(
            """
            SELECT llm_model, SUM(llm_cost_usd)
            FROM civitas_spans
            WHERE llm_cost_usd IS NOT NULL AND llm_model IS NOT NULL
              AND start_time >= %s AND start_time <= %s
            GROUP BY llm_model
            """,
            (since, until),
        )
        return {r[0]: float(r[1]) if r[1] is not None else 0.0 for r in rows}

    async def recent_spans(self, since: float, until: float, limit: int = 200) -> list[SpanRecord]:
        rows = await self._fetch(
            f"SELECT {_SPAN_COLS} FROM civitas_spans "
            "WHERE start_time >= %s AND start_time <= %s "
            f"ORDER BY start_time DESC LIMIT {int(limit)}",
            (since, until),
        )
        return [SpanRecord(*r) for r in rows]

    async def spans_in_trace(self, trace_id: str, since: float, until: float) -> list[SpanRecord]:
        rows = await self._fetch(
            f"SELECT {_SPAN_COLS} FROM civitas_spans "
            "WHERE trace_id = %s AND start_time >= %s AND start_time <= %s "
            "ORDER BY start_time ASC",
            (trace_id, since, until),
        )
        return [SpanRecord(*r) for r in rows]

"""MySQLStateStore — persistent agent-state store backed by MySQL/MariaDB.

The MySQL sibling of ``PostgresStateStore``. Agent state survives crashes and
restarts, stored as a JSON blob keyed by agent name. Requires
``civitas-contrib[mysql]`` (aiomysql).

Usage::

    store = MySQLStateStore("mysql://user:pass@host:3306/db")
    runtime = Runtime(supervisor=..., state_store=store)

Or via topology YAML::

    plugins:
      state:
        type: mysql
        config:
          url: !ENV DATABASE_URL

``close()`` releases the connection pool; ``Runtime.stop()`` calls it.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import unquote, urlparse

_TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS civitas_agent_state (
        agent_name  VARCHAR(255) PRIMARY KEY,
        state       JSON NOT NULL,
        updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
    )
"""


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


class MySQLStateStore:
    """aiomysql-backed StateStore implementing the StateStore protocol.

    State is scoped per-agent; stateless agents incur zero overhead. The
    connection pool is created lazily on first use, so constructing this object
    is always safe even before the event loop starts.
    """

    def __init__(
        self,
        url: str,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        self._conn_kwargs = _parse_url(url)
        self._min_size = min_size
        self._max_size = max_size
        self._pool: Any = None

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            try:
                import aiomysql
            except ImportError as exc:
                raise ImportError(
                    "MySQLStateStore requires aiomysql. "
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

    async def close(self) -> None:
        """Close the connection pool. Authoritative cleanup path."""
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def get(self, agent_name: str) -> dict[str, Any] | None:
        """Load agent state from MySQL, or None if not found."""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT state FROM civitas_agent_state WHERE agent_name = %s",
                (agent_name,),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return json.loads(row[0])  # type: ignore[no-any-return]

    async def set(self, agent_name: str, state: dict[str, Any]) -> None:
        """Upsert agent state into MySQL."""
        pool = await self._ensure_pool()
        blob = json.dumps(state)
        async with pool.acquire() as conn, conn.cursor() as cur:
            # Pass the blob twice rather than VALUES(state): VALUES() in ON
            # DUPLICATE KEY UPDATE is deprecated on MySQL 8.0.20+, and the
            # newer `AS alias` form isn't supported by MariaDB. This is portable.
            await cur.execute(
                "INSERT INTO civitas_agent_state (agent_name, state) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE state = %s",
                (agent_name, blob, blob),
            )

    async def delete(self, agent_name: str) -> None:
        """Remove agent state from MySQL."""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM civitas_agent_state WHERE agent_name = %s",
                (agent_name,),
            )

    async def list_agents(self) -> list[str]:
        """Return all agent names with persisted state, sorted."""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute("SELECT agent_name FROM civitas_agent_state ORDER BY agent_name")
            rows = await cur.fetchall()
        return [r[0] for r in rows]

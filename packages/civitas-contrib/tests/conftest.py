"""Real-DB test fixtures — spin up Postgres/MySQL containers via testcontainers.

Skips cleanly (not fails) when Docker or testcontainers is unavailable, so the
rest of the suite still runs in a bare environment. Containers are session-scoped
(one per DB) since standing them up is the slow part.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

try:
    from testcontainers.mysql import MySqlContainer
    from testcontainers.postgres import PostgresContainer

    _HAS_TESTCONTAINERS = True
except ImportError:
    _HAS_TESTCONTAINERS = False


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    if not _HAS_TESTCONTAINERS:
        pytest.skip("testcontainers not installed")
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except Exception as exc:  # noqa: BLE001 -- Docker not running / unavailable
        pytest.skip(f"could not start Postgres container: {exc}")
    try:
        # asyncpg wants a plain postgresql:// URL (no +psycopg2 driver suffix).
        url = (
            f"postgresql://{container.username}:{container.password}"
            f"@{container.get_container_host_ip()}:{container.get_exposed_port(5432)}"
            f"/{container.dbname}"
        )
        yield url
    finally:
        container.stop()


@pytest.fixture
async def clean_postgres(postgres_url: str) -> str:
    """Drop the civitas tables so each test starts from a clean schema (the
    session container is shared; stores recreate tables via CREATE IF NOT
    EXISTS on first use)."""
    import asyncpg

    conn = await asyncpg.connect(postgres_url)
    try:
        await conn.execute("DROP TABLE IF EXISTS civitas_spans")
        await conn.execute("DROP TABLE IF EXISTS civitas_agent_state")
    finally:
        await conn.close()
    return postgres_url


@pytest.fixture(scope="session")
def mysql_url() -> Iterator[str]:
    if not _HAS_TESTCONTAINERS:
        pytest.skip("testcontainers not installed")
    try:
        container = MySqlContainer("mysql:8.0")
        container.start()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"could not start MySQL container: {exc}")
    try:
        url = (
            f"mysql://{container.username}:{container.password}"
            f"@{container.get_container_host_ip()}:{container.get_exposed_port(3306)}"
            f"/{container.dbname}"
        )
        yield url
    finally:
        container.stop()


@pytest.fixture
async def clean_mysql(mysql_url: str) -> str:
    """Drop the civitas tables so each test starts from a clean schema."""
    import aiomysql

    from civitas_contrib.plugins.mysql_store import _parse_url

    conn = await aiomysql.connect(autocommit=True, **_parse_url(mysql_url))
    try:
        async with conn.cursor() as cur:
            await cur.execute("DROP TABLE IF EXISTS civitas_spans")
            await cur.execute("DROP TABLE IF EXISTS civitas_agent_state")
    finally:
        conn.close()
    return mysql_url

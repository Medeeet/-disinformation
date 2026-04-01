"""
PostgreSQL connection pool (asyncpg).
Пул создаётся один раз при старте приложения и хранится в app.state.pool.
"""
import asyncpg

from app.config import DATABASE_URL

# Каждый DDL — отдельный запрос (asyncpg не поддерживает executescript)
_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS analyses (
        id            TEXT PRIMARY KEY,
        input_text    TEXT NOT NULL,
        input_url     TEXT,
        overall_score REAL NOT NULL,
        ml_score      REAL,
        rule_score    REAL,
        verdict       TEXT NOT NULL,
        details_json  TEXT,
        created_at    TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sources (
        domain            TEXT PRIMARY KEY,
        credibility_score REAL NOT NULL,
        category          TEXT,
        notes             TEXT,
        last_updated      TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_check_cache (
        query_hash    TEXT PRIMARY KEY,
        response_json TEXT NOT NULL,
        fetched_at    TIMESTAMPTZ DEFAULT NOW()
    )
    """,
]


async def create_pool() -> asyncpg.Pool:
    """Создаёт пул соединений и инициализирует схему БД."""
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        for stmt in _SCHEMA_STATEMENTS:
            await conn.execute(stmt)
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()

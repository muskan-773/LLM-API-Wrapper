import asyncpg

from app import config


pool: asyncpg.Pool | None = None


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS usage_records (
    id            BIGSERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ      NOT NULL DEFAULT now(),
    model         TEXT             NOT NULL,
    input_tokens  INTEGER          NOT NULL,
    output_tokens INTEGER          NOT NULL,
    cost_usd      DOUBLE PRECISION NOT NULL,
    latency_ms    DOUBLE PRECISION NOT NULL
);
"""


async def init_db() -> None:
    global pool

    pool = await asyncpg.create_pool(
        config.DATABASE_URL,
        min_size=1,
        max_size=5,
    )

    await pool.execute(CREATE_TABLE_SQL)


async def close_db() -> None:
    if pool is not None:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")

    return pool
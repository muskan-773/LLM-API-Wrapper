import json
import logging

import redis.asyncio as redis

from app import config


logger = logging.getLogger(__name__)


client = redis.from_url(
    config.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)


async def get_json(key: str) -> dict | None:
    try:
        value = await client.get(key)

    except Exception:
        logger.warning(
            "Cache read failed; continuing without cache",
            exc_info=True,
        )
        return None

    return json.loads(value) if value else None


async def set_json(
    key: str,
    data: dict,
    ttl_seconds: int,
) -> None:
    try:
        await client.set(
            key,
            json.dumps(data),
            ex=ttl_seconds,
        )

    except Exception:
        logger.warning(
            "Cache write failed; continuing without cache",
            exc_info=True,
        )


async def close_cache() -> None:
    await client.aclose()
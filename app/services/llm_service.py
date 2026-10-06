import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone

from app import cache, config
from app.model.schemas import ChatResponse, UsageRecord
from app.services import usage_store
from app.services.retry import call_with_retry


logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Generic failure from the LLM service."""


def _cache_key(message: str) -> str:
    raw = f"{config.MODEL_NAME}|{config.MAX_TOKENS}|{message.strip()}"

    return "llm:cache:" + hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


async def generate_reply(message: str) -> ChatResponse:

    # 1. Build cache key
    key = _cache_key(message)

    # 2. Check Redis
    cached_data = await cache.get_json(key)

    if cached_data is not None:
        logger.info(
            "Cache HIT key=...%s",
            key[-8:],
        )

        return ChatResponse(
            **cached_data,
            cost_usd=0.0,
            cached=True,
        )

    logger.info(
        "Cache MISS key=...%s",
        key[-8:],
    )

    async def _call():
        # Temporary mock LLM call
        await asyncio.sleep(0.2)

        return ChatResponse(
            reply=f"Mock response: You said '{message}'",
            model="mock-model",
            input_tokens=len(message.split()),
            output_tokens=5,
            cost_usd=0.0,
            cached=False,
        )

    try:
        # 3. Measure LLM latency
        start_time = time.perf_counter()

        response = await call_with_retry(
            _call,
            max_retries=config.MAX_RETRIES,
            base_delay=config.RETRY_BASE_DELAY,
        )

        # 4. Calculate latency
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # 5. Store successful response in Redis
        await cache.set_json(
            key,
            {
                "reply": response.reply,
                "model": response.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
            config.CACHE_TTL_SECONDS,
        )

        # 6. Store usage in PostgreSQL
        try:
            await usage_store.add_record(
                UsageRecord(
                    timestamp=datetime.now(timezone.utc),
                    model=response.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost_usd=response.cost_usd,
                    latency_ms=latency_ms,
                )
            )

        except Exception:
            logger.exception(
                "Failed to store usage record"
            )

        # 7. Return response
        return response

    except Exception as e:
        raise LLMServiceError(
            f"LLM service failed: {e}"
        ) from e
import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import AsyncIterator

from app import cache, config
from app.model.schemas import ChatResponse, UsageRecord
from app.services import usage_store
from app.services.retry import call_with_retry


logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Generic failure from the LLM service."""


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _record_usage(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    latency_ms: float,
) -> None:
    try:
        await usage_store.add_record(
            UsageRecord(
                timestamp=datetime.now(timezone.utc),
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
            )
        )

    except Exception:
        logger.exception("Failed to store usage record")


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
        await _record_usage(
            response.model,
            response.input_tokens,
            response.output_tokens,
            response.cost_usd,
            latency_ms,
        )

        # 7. Return response
        return response

    except Exception as e:
        raise LLMServiceError(
            f"LLM service failed: {e}"
        ) from e


async def stream_reply(message: str) -> AsyncIterator[str]:

    # 1. Build cache key
    key = _cache_key(message)

    # 2. Check Redis cache
    cached = await cache.get_json(key)

    if cached is not None:
        logger.info(
            "Stream cache HIT key=...%s",
            key[-8:],
        )

        # Send complete cached response as one delta
        yield _sse(
            "delta",
            {
                "text": cached["reply"]
            },
        )

        # Then tell client the stream is complete
        yield _sse(
            "done",
            {
                "model": cached["model"],
                "input_tokens": cached["input_tokens"],
                "output_tokens": cached["output_tokens"],
                "cost_usd": 0.0,
                "cached": True,
            },
        )

        return

    logger.info(
        "Stream cache MISS key=...%s",
        key[-8:],
    )

    # 3. Start measuring latency
    start = time.perf_counter()

    # Time until first streamed chunk
    first_token_ms: float | None = None

    # Store all streamed pieces
    parts: list[str] = []

    try:
        # -----------------------------------------------------
        # Temporary mock streaming
        # -----------------------------------------------------

        full_text = f"Mock response: You said '{message}'"

        # Simulate the model producing pieces
        words = full_text.split(" ")

        for index, word in enumerate(words):

            # Simulate delay between chunks
            await asyncio.sleep(0.1)

            # Measure TTFT only once
            if first_token_ms is None:
                first_token_ms = (
                    time.perf_counter() - start
                ) * 1000

            text = word

            # Add spaces back between words
            if index < len(words) - 1:
                text += " "

            # Keep the piece
            parts.append(text)

            # Send chunk immediately to client
            yield _sse(
                "delta",
                {
                    "text": text
                },
            )

        # -----------------------------------------------------
        # Stream completed successfully
        # -----------------------------------------------------

        reply_text = "".join(parts)

        # Total latency
        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        input_tokens = len(message.split())
        output_tokens = len(words)

        model = "mock-model"
        cost = 0.0

        # 4. Cache ONLY after complete stream
        await cache.set_json(
            key,
            {
                "reply": reply_text,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            config.CACHE_TTL_SECONDS,
        )

        # 5. Store usage
        await _record_usage(
            model,
            input_tokens,
            output_tokens,
            cost,
            latency_ms,
        )

        logger.info(
            "LLM stream model=%s in=%d out=%d "
            "cost=$%.6f ttft=%.0fms total=%.0fms",
            model,
            input_tokens,
            output_tokens,
            cost,
            first_token_ms or 0.0,
            latency_ms,
        )

        # 6. Tell client stream is finished
        yield _sse(
            "done",
            {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "cached": False,
            },
        )

    except Exception:
        logger.exception("Stream failed")

        # Send SSE error event
        yield _sse(
            "error",
            {
                "detail": "LLM provider call failed"
            },
        )

        return
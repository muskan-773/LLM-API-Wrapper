import asyncio
import logging
import time
from datetime import datetime, timezone

from app import config
from app.model.schemas import ChatResponse, UsageRecord
from app.services import usage_store
from app.services.retry import call_with_retry


logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Generic failure from the LLM service."""


async def generate_reply(message: str) -> ChatResponse:

    async def _call():
        # Temporary mock LLM call
        await asyncio.sleep(0.2)

        return ChatResponse(
            reply=f"Mock response: You said '{message}'",
            model="mock-model",
            input_tokens=len(message.split()),
            output_tokens=5,
        )

    try:
        # Start measuring LLM call time
        start_time = time.perf_counter()

        response = await call_with_retry(
            _call,
            max_retries=config.MAX_RETRIES,
            base_delay=config.RETRY_BASE_DELAY,
        )

        # Calculate latency in milliseconds
        latency_ms = (time.perf_counter() - start_time) * 1000

        try:
            await usage_store.add_record(
                UsageRecord(
                    timestamp=datetime.now(timezone.utc),
                    model=response.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                )
            )
        except Exception:
            logger.exception("Failed to store usage record")

        return response

    except Exception as e:
        raise LLMServiceError(
            f"LLM service failed: {e}"
        ) from e
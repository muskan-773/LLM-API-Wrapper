import asyncio

from app import config
from app.model.schemas import ChatResponse
from app.services.retry import call_with_retry


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
        response = await call_with_retry(
            _call,
            max_retries=config.MAX_RETRIES,
            base_delay=config.RETRY_BASE_DELAY,
        )

        return response

    except Exception as e:
        raise LLMServiceError(
            f"LLM service failed: {e}"
        ) from e
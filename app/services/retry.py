import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

from anthropic import APIConnectionError, APIStatusError


logger = logging.getLogger(__name__)

T = TypeVar("T")


class MockRetryableError(Exception):
    """Temporary error used to test retry behavior."""


# HTTP errors that are temporary and safe to retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504, 529}


def is_retryable(error: Exception) -> bool:
    # Our local test error
    if isinstance(error, MockRetryableError):
        return True

    # Retry network/connection errors
    if isinstance(error, APIConnectionError):
        return True

    # Retry only temporary API errors
    if isinstance(error, APIStatusError):
        return error.status_code in RETRYABLE_STATUS_CODES

    # Don't retry other errors
    return False


async def call_with_retry(
    func: Callable[[], Awaitable[T]],
    *,
    max_retries: int,
    base_delay: float,
) -> T:

    # Number of retries already performed
    attempt = 0

    while True:
        try:
            # Execute the API/LLM call
            return await func()

        except Exception as e:
            # Stop if the error isn't retryable or retries are exhausted
            if not is_retryable(e) or attempt >= max_retries:
                raise

            # Exponential backoff with random jitter
            delay = random.uniform(
                0,
                base_delay * (2 ** attempt)
            )

            # Log the failure and next retry
            logger.warning(
                "LLM call failed (%s). Retry %d/%d in %.2fs",
                type(e).__name__,
                attempt + 1,
                max_retries,
                delay,
            )

            # Wait before retrying without blocking other async tasks
            await asyncio.sleep(delay)

            # Increment retry count
            attempt += 1
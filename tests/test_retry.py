import pytest

from app.services.retry import (
    MockRetryableError,
    call_with_retry,
)


@pytest.mark.anyio
async def test_successful_call_does_not_retry():
    calls = 0

    async def successful_call():
        nonlocal calls
        calls += 1
        return "success"

    result = await call_with_retry(
        successful_call,
        max_retries=3,
        base_delay=0,
    )

    assert result == "success"
    assert calls == 1


@pytest.mark.anyio
async def test_retryable_error_is_retried():
    calls = 0

    async def failing_then_success():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise MockRetryableError("temporary failure")

        return "success"

    result = await call_with_retry(
        failing_then_success,
        max_retries=3,
        base_delay=0,
    )

    assert result == "success"

    # Failed twice, succeeded on third attempt.
    assert calls == 3


@pytest.mark.anyio
async def test_retry_stops_after_max_retries():
    calls = 0

    async def always_fails():
        nonlocal calls
        calls += 1

        raise MockRetryableError("temporary failure")

    with pytest.raises(MockRetryableError):
        await call_with_retry(
            always_fails,
            max_retries=2,
            base_delay=0,
        )

    # Initial attempt + 2 retries.
    assert calls == 3


@pytest.mark.anyio
async def test_non_retryable_error_is_not_retried():
    calls = 0

    async def bad_call():
        nonlocal calls
        calls += 1

        raise ValueError("permanent failure")

    with pytest.raises(ValueError):
        await call_with_retry(
            bad_call,
            max_retries=3,
            base_delay=0,
        )

    # ValueError is not retryable.
    assert calls == 1
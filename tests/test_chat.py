import pytest

from app.services import llm_service


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"message": ""},
    ],
)
def test_chat_rejects_invalid_body(client, body):
    response = client.post(
        "/chat",
        json=body,
    )

    assert response.status_code == 422


def test_chat_returns_mock_response_and_records_usage(
    client,
    fake_infra,
):
    response = client.post(
        "/chat",
        json={"message": "hello"},
    )

    data = response.json()

    assert response.status_code == 200
    assert data["reply"] == "Mock response: You said 'hello'"
    assert data["model"] == "mock-model"
    assert data["input_tokens"] == 1
    assert data["output_tokens"] == 5
    assert data["cost_usd"] == 0.0
    assert data["cached"] is False

    assert len(fake_infra.records) == 1


def test_second_identical_request_is_cache_hit(
    client,
    fake_infra,
):
    first = client.post(
        "/chat",
        json={"message": "hello"},
    )

    second = client.post(
        "/chat",
        json={"message": "hello"},
    )

    first_data = first.json()
    second_data = second.json()

    assert first.status_code == 200
    assert second.status_code == 200

    assert first_data["cached"] is False
    assert second_data["cached"] is True

    assert second_data["reply"] == first_data["reply"]
    assert second_data["cost_usd"] == 0.0

    # Cache hit should not create another usage record.
    assert len(fake_infra.records) == 1


def test_different_message_is_cache_miss(
    client,
    fake_infra,
):
    first = client.post(
        "/chat",
        json={"message": "hello"},
    )

    second = client.post(
        "/chat",
        json={"message": "goodbye"},
    )

    assert first.json()["cached"] is False
    assert second.json()["cached"] is False

    # Two different messages = two usage records.
    assert len(fake_infra.records) == 2


def test_chat_service_error_returns_502(
    client,
    monkeypatch,
):
    async def failing_generate_reply(message):
        raise llm_service.LLMServiceError(
            "LLM service failed"
        )

    monkeypatch.setattr(
        llm_service,
        "generate_reply",
        failing_generate_reply,
    )

    response = client.post(
        "/chat",
        json={"message": "hello"},
    )

    assert response.status_code == 502

    assert response.json()["detail"] == (
        "LLM service temporarily unavailable"
    )

    # Internal error details must not reach the client.
    assert "LLM service failed" not in response.text


def test_stream_emits_deltas_and_done(
    client,
    fake_infra,
):
    response = client.post(
        "/chat/stream",
        json={"message": "hello"},
    )

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )

    assert "event: delta" in response.text
    assert "event: done" in response.text

    # Streaming sends the response in separate chunks.
    assert '"text": "Mock "' in response.text
    assert '"text": "response: "' in response.text

    assert len(fake_infra.records) == 1


def test_stream_cache_hit(
    client,
    fake_infra,
):
    first = client.post(
        "/chat/stream",
        json={"message": "hello"},
    )

    second = client.post(
        "/chat/stream",
        json={"message": "hello"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert '"cached": false' in first.text
    assert '"cached": true' in second.text

    # Cache hit should not create another usage record.
    assert len(fake_infra.records) == 1


def test_stream_different_message_is_cache_miss(
    client,
    fake_infra,
):
    first = client.post(
        "/chat/stream",
        json={"message": "hello"},
    )

    second = client.post(
        "/chat/stream",
        json={"message": "world"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert '"cached": false' in first.text
    assert '"cached": false' in second.text

    # Two different messages = two usage records.
    assert len(fake_infra.records) == 2
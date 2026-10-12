# LLM API Wrapper Service

A FastAPI backend demonstrating backend engineering patterns around LLM
APIs: retries, Redis caching, Server-Sent Events (SSE) streaming,
PostgreSQL usage persistence, and error handling.

> **Current provider:** This project uses a mock LLM implementation. It
> does not make real or paid LLM API calls. Token counts, latency, and
> cost values are illustrative, not provider-billed metrics.

## Live Demo

-   **Live service:** https://llm-api-wrapper.onrender.com
-   **Health check:** https://llm-api-wrapper.onrender.com/health
-   **Interactive API docs:** https://llm-api-wrapper.onrender.com/docs
-   **Usage dashboard:** https://llm-api-wrapper.onrender.com/dashboard
-   **GitHub repository:** https://github.com/muskan-773/LLM-API-Wrapper

The root URL (`/`) may return `404 Not Found` because a homepage route
is not currently defined. Use `/health` to check service health and
`/docs` to explore the API. Hosted services may sleep or be temporarily
unavailable depending on the hosting plan and configured services.

## Features

-   `POST /chat` --- JSON chat response
-   `POST /chat/stream` --- Server-Sent Events (SSE) streaming
-   Retry logic with exponential backoff and jitter for retryable errors
-   Redis response caching with configurable TTL
-   Cache-aside pattern and graceful handling of cache failures
-   PostgreSQL usage persistence
-   Input/output token-count fields, latency, and cost fields
-   Daily and per-model usage summaries
-   Usage dashboard
-   Configuration validation
-   Client-safe error responses
-   Automated pytest test suite

## Architecture

``` text
Client
  |
  v
FastAPI application
  |
  +-----------------------------+
  |                             |
  v                             v
Chat routes                Usage/dashboard routes
  |
  v
LLM service
  |
  +-----------------------------+
  |                             |
  v                             v
Redis cache                 Mock LLM
  |                             |
  +--------------+--------------+
                 |
                 v
            Usage store
                 |
                 v
             PostgreSQL
```

The code separates HTTP routes, service logic, caching, database access,
and request/response schemas.

### Request flow

1.  A client sends a request to `POST /chat` or `POST /chat/stream`.
2.  The service checks Redis for a cached response.
3.  On a cache miss, the mock provider generates a response. The
    non-streaming path uses the retry wrapper.
4.  The response is cached for the configured TTL.
5.  Successful non-cached requests attempt to save usage information to
    PostgreSQL.
6.  The API returns JSON or SSE events.

## Project Structure

``` text
llm-api-wrapper/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── cache.py
│   ├── model/
│   │   └── schemas.py
│   ├── routes/
│   │   ├── chat.py
│   │   ├── usage.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── retry.py
│   │   └── usage_store.py
│   └── static/
│       └── dashboard.html
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_chat.py
│   └── test_retry.py
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── README.md
```

The real `.env` file is intentionally excluded from the repository.
Create your own local `.env` file as described below.

## Technology Stack

-   **Language:** Python
-   **API framework:** FastAPI
-   **ASGI server:** Uvicorn
-   **Database:** PostgreSQL with `asyncpg`
-   **Cache:** Redis with `redis-py` asyncio API
-   **Testing:** pytest, AnyIO, HTTPX
-   **Configuration:** `python-dotenv`

## Requirements

-   Python 3.10+
-   PostgreSQL
-   Redis
-   `pip`
-   A Python virtual environment

## Local Setup

``` bash
git clone https://github.com/muskan-773/LLM-API-Wrapper.git
cd LLM-API-Wrapper
python3 -m venv venv
```

Activate the environment:

**macOS / Linux**

``` bash
source venv/bin/activate
```

**Windows**

``` powershell
venv\\Scripts\\activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Environment Configuration

Create a `.env` file in the project root with your own local connection
settings:

``` env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/llm_wrapper
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600
```

Replace `YOUR_PASSWORD` with your local PostgreSQL password. Never
commit real passwords, tokens, or API keys. Additional settings and
defaults are defined in `app/config.py`. The mock implementation does
**not** require an Anthropic or OpenAI API key.

## Database

PostgreSQL persists usage records. The example local database name is
`llm_wrapper`. At startup, the service creates the `usage_records` table
if it does not already exist. A database migration tool is not currently
used.

## Redis Caching

Redis caches responses to avoid repeating the same mock generation for
identical requests.

-   Cache TTL is controlled by `CACHE_TTL_SECONDS` (default: `3600`
    seconds).
-   The cache key uses the configured model, maximum-token setting, and
    normalized message.
-   Cache hits return `cached: true` and `cost_usd: 0.0`.
-   Cache hits do not create another usage record.
-   If a cache read or write fails, the service logs the issue and
    continues without relying on the cache.

## Running Locally

``` bash
uvicorn app.main:app --reload
```

-   API: http://127.0.0.1:8000
-   Interactive docs: http://127.0.0.1:8000/docs
-   Dashboard: http://127.0.0.1:8000/dashboard

## API Endpoints

  Method   Endpoint          Purpose
  -------- ----------------- ----------------------------------
  `GET`    `/health`         Health check
  `POST`   `/chat`           JSON chat response
  `POST`   `/chat/stream`    SSE streaming response
  `GET`    `/usage`          Usage summary and recent records
  `GET`    `/usage/daily`    Usage aggregated by day
  `GET`    `/usage/models`   Usage grouped by model
  `GET`    `/dashboard`      Usage dashboard

### Health Check

``` http
GET /health
```

Example response:

``` json
{
  "status": "ok",
  "app_name": "LLM API Wrapper Service",
  "environment": "development"
}
```

### Chat

``` http
POST /chat
Content-Type: application/json
```

Request:

``` json
{
  "message": "Hello"
}
```

Example response:

``` json
{
  "reply": "Mock response: You said 'Hello'",
  "model": "mock-model",
  "input_tokens": 1,
  "output_tokens": 5,
  "cost_usd": 0.0,
  "cached": false
}
```

### Streaming Chat

``` http
POST /chat/stream
Content-Type: application/json
```

The endpoint uses Server-Sent Events. It emits one or more `delta`
events followed by a `done` event. A stream failure can produce an
`error` event.

Example event sequence:

``` text
event: delta
data: {"text": "Mock "}

event: delta
data: {"text": "response: "}

event: done
data: {"model": "mock-model", "input_tokens": 1, "output_tokens": 5, "cost_usd": 0.0, "cached": false}
```

### Usage Summary

`GET /usage` returns total requests, input/output tokens, total cost,
average latency, and recent records.

### Daily Usage

`GET /usage/daily` returns request counts, token counts, and cost
aggregated by day.

### Usage by Model

`GET /usage/models` returns per-model request count, total cost, average
latency, and p95 latency.

### Dashboard

Open `http://127.0.0.1:8000/dashboard` locally, or use the hosted
dashboard link in the Live Demo section.

## Retry Strategy

The retry implementation is in `app/services/retry.py`. It uses
exponential backoff with jitter and retries selected temporary errors,
including connection errors and configured retryable HTTP status codes
such as `429`, `500`, `502`, `503`, `504`, and `529`.

The maximum retry count and base delay are configurable through
environment variables. The current provider is mocked; the retry module
is structured to support retryable provider exceptions.

## Usage Tracking

Successful non-cached requests attempt to save usage data to PostgreSQL.
Each record contains a timestamp, model name, input/output token counts,
cost field, and latency in milliseconds. Since the provider is mocked,
cost values are `0.0`, and token counts are approximations rather than
provider-reported usage.

## Error Handling

Internal service errors are logged on the server. The chat endpoint
returns a generic client-facing error rather than exposing internal
implementation details.

Example:

``` json
{
  "detail": "LLM service temporarily unavailable"
}
```

## Configuration Validation

The application validates important settings during startup, including
`MAX_TOKENS`, `MAX_RETRIES`, `RETRY_BASE_DELAY`, `REQUEST_TIMEOUT`, and
`CACHE_TTL_SECONDS`. Invalid configuration values cause startup
validation to fail.

## Testing

The test suite uses pytest and replaces Redis/PostgreSQL operations with
in-memory fakes for route tests, so it does not require live Redis or
PostgreSQL services.

``` bash
python -m pytest -v
```

The latest verified local test run completed with **14 passed**.

Tests cover health checks, request validation, chat responses, usage
recording, cache hits/misses, error handling, SSE streaming, retry
success, retryable errors, maximum retry attempts, and non-retryable
errors.

## Example Requests

### Chat

``` bash
curl -X POST http://127.0.0.1:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Explain REST in one sentence."}'
```

### Streaming

``` bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Write a haiku about caching."}'
```

## Known Limitations

-   The LLM provider is mocked; no real model inference occurs.
-   Streaming emits simulated chunks from mock text.
-   Cost values are `0.0` and do not represent provider billing.
-   Token counts are illustrative, not provider-reported usage.
-   No authentication or authorization.
-   No rate limiting.
-   Cache hits are not recorded as new usage records.
-   PostgreSQL schema creation occurs at startup; no migration tool is
    used.
-   No distributed tracing or dedicated production monitoring.
-   No CI/CD pipeline is configured.

## Future Improvements

-   Integrate a real LLM provider behind the existing service
    abstraction.
-   Support multiple providers.
-   Add authentication, authorization, and rate limiting.
-   Add request IDs, metrics, and distributed tracing.
-   Add database migrations.
-   Add CI/CD automation.
-   Improve monitoring and alerting.
-   Add production containerization.

## Project Goal

This project demonstrates backend engineering concepts used when
building an LLM-facing API: API design, caching, retries, streaming,
usage tracking, PostgreSQL persistence, testing, error handling, and
configuration validation.

The mock provider keeps development and testing independent of paid LLM
API usage while these backend concepts are explored.

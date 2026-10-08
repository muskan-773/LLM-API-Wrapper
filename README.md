# LLM API Wrapper Service

A FastAPI backend that demonstrates how to build an LLM API wrapper
with production-style features such as retries, caching, streaming,
usage tracking, database persistence, and error handling.

The current implementation uses a **mock LLM provider**, so the project
can run locally without requiring a paid LLM API.

---

## Features

- `POST /chat` — generate a JSON response
- `POST /chat/stream` — Server-Sent Events (SSE) streaming
- Retry logic with exponential backoff and jitter
- Redis caching with TTL
- Cache-aside pattern
- Graceful cache failure handling
- PostgreSQL usage tracking
- Input and output token tracking
- Request latency tracking
- Cost tracking
- Daily usage statistics
- Per-model usage statistics
- Usage dashboard
- Configuration validation
- Secure error handling
- Automated pytest test suite

---

## Architecture

```text
Client
  |
  v
FastAPI
  |
  +-------------------------+
  |                         |
  v                         v
Chat Routes             Dashboard Routes
  |
  v
LLM Service
  |
  +------------------+
  |                  |
  v                  v
Mock LLM          Redis Cache
  |
  v
Usage Store
  |
  v
PostgreSQL
```

The main responsibilities are separated into routes, services,
caching, database access, and data schemas.

---

## Project Structure

```text
llm-api-wrapper/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── cache.py
│   │
│   ├── model/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── usage.py
│   │   └── dashboard.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py
│   │   ├── retry.py
│   │   └── usage_store.py
│   │
│   └── static/
│       └── dashboard.html
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_chat.py
│   └── test_retry.py
│
├── .env
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── README.md
```

---

## Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Database

- PostgreSQL
- asyncpg

### Cache

- Redis
- redis-py asyncio API

### Testing

- pytest
- pytest-anyio
- httpx

### Configuration

- python-dotenv

---

## Requirements

Before running the project, make sure you have:

- Python 3.10+
- PostgreSQL
- Redis
- pip
- Virtual environment

---

## Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install the application dependencies:

```bash
pip install -r requirements.txt
```

For development and testing:

```bash
pip install -r requirements-dev.txt
```

---

## Environment Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/llm_wrapper
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600
```

The application also supports additional configuration values through
environment variables. Defaults are defined in:

```text
app/config.py
```

The current implementation uses a mock LLM, so an Anthropic API key
is **not required**.

---

## Database

The application uses PostgreSQL to persist usage information.

The database name used in the example configuration is:

```text
llm_wrapper
```

The application automatically creates the required usage table during
startup.

---

## Redis

Redis is used for response caching.

Default Redis configuration:

```text
redis://localhost:6379/0
```

The cache TTL is controlled by:

```env
CACHE_TTL_SECONDS=3600
```

If Redis is unavailable, the application logs the cache failure and
continues without caching.

---

## Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "app_name": "LLM API Wrapper Service",
  "environment": "development"
}
```

---

### Chat

```http
POST /chat
```

Request:

```json
{
  "message": "Hello"
}
```

Example response:

```json
{
  "reply": "Mock response: You said 'Hello'",
  "model": "mock-model",
  "input_tokens": 1,
  "output_tokens": 5,
  "cost_usd": 0.0,
  "cached": false
}
```

---

### Streaming Chat

```http
POST /chat/stream
```

This endpoint uses Server-Sent Events (SSE).

The response is delivered in multiple `delta` events followed by a
`done` event.

Example:

```text
event: delta
data: {"text": "Mock "}

event: delta
data: {"text": "response: "}

event: delta
data: {"text": "You "}

event: delta
data: {"text": "said "}

event: done
data: {"model": "mock-model", "input_tokens": 1, "output_tokens": 5, "cost_usd": 0.0, "cached": false}
```

---

### Usage Summary

```http
GET /usage
```

Returns overall usage information including:

- Total requests
- Input tokens
- Output tokens
- Total cost
- Average latency
- Recent usage records

---

### Daily Usage

```http
GET /usage/daily
```

Returns usage aggregated by day.

The response includes:

- Date
- Request count
- Input tokens
- Output tokens
- Cost

---

### Usage by Model

```http
GET /usage/models
```

Returns usage grouped by model.

The response includes:

- Model
- Request count
- Cost
- Average latency
- P95 latency

---

### Dashboard

Open:

```text
http://127.0.0.1:8000/dashboard
```

The dashboard provides a simple interface for viewing usage information.

---

## Caching

The application uses a cache-aside strategy.

### Cache Miss

```text
Request
   |
   v
Check Redis
   |
   +---- MISS
          |
          v
       Mock LLM
          |
          v
      Store result
          |
          v
       PostgreSQL
          |
          v
       Response
```

### Cache Hit

```text
Request
   |
   v
Check Redis
   |
   +---- HIT
          |
          v
    Return cached response
```

The cache key is based on the model, maximum token configuration, and
message.

Cached responses return:

```json
{
  "cached": true,
  "cost_usd": 0.0
}
```

Cache hits do not create another usage record.

---

## Retry Strategy

Temporary failures are handled using retry logic with exponential
backoff and jitter.

Retryable errors include:

- Connection errors
- HTTP 429
- HTTP 500
- HTTP 502
- HTTP 503
- HTTP 504
- HTTP 529

The retry implementation is located at:

```text
app/services/retry.py
```

The number of retries and base delay can be configured through
environment variables.

---

## Usage Tracking

Successful non-cached requests record usage information in PostgreSQL.

Each usage record contains:

- Timestamp
- Model
- Input tokens
- Output tokens
- Cost
- Latency

This information is later used by:

```text
GET /usage
GET /usage/daily
GET /usage/models
```

and the dashboard.

---

## Error Handling

The application separates internal errors from client-facing errors.

For example, an internal service error may be:

```text
LLM service failed
```

The detailed error is logged by the server.

The client instead receives:

```json
{
  "detail": "LLM service temporarily unavailable"
}
```

This prevents internal implementation details from being exposed through
the API.

---

## Configuration Validation

The application validates important configuration values during startup.

Examples include:

- `MAX_TOKENS`
- `MAX_RETRIES`
- `RETRY_BASE_DELAY`
- `REQUEST_TIMEOUT`
- `CACHE_TTL_SECONDS`

Invalid configuration causes startup validation to fail rather than
allowing the application to run with unsafe or invalid settings.

---

## Testing

The project uses pytest for automated testing.

The tests use:

- A mock LLM
- In-memory cache fakes
- In-memory usage storage fakes

This means the test suite does not require Redis or PostgreSQL to be
running.

Run all tests:

```bash
python -m pytest -v
```

Current test suite:

```text
14 passed
```

### Tests cover

- Health endpoint
- Request validation
- Chat responses
- Usage recording
- Cache hits
- Cache misses
- Different-message cache behavior
- Chat error handling
- Secure error responses
- SSE streaming
- Streaming cache
- Retry success
- Retryable failures
- Maximum retry behavior
- Non-retryable failures

---

## Development Workflow

Run the test suite before making a commit:

```bash
python -m pytest -v
```

A successful run should show:

```text
14 passed
```

Start the application locally:

```bash
uvicorn app.main:app --reload
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

Open the dashboard:

```text
http://127.0.0.1:8000/dashboard
```

---

## Example Requests

### Chat

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain REST in one sentence."}'
```

### Streaming

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a haiku about caching."}'
```

---

## Known Limitations

- No authentication or authorization
- No rate limiting
- Current LLM implementation is a mock provider
- Cache hits are not recorded as usage records
- Streaming currently uses mock token generation
- Costs are currently `0.0` because no paid LLM provider is being used
- No distributed tracing
- No production monitoring system
- PostgreSQL schema is created at startup
- No database migration tool is currently used
- No CI/CD pipeline yet

---

## Future Improvements

Possible future improvements include:

- Real LLM provider integration
- Multiple LLM provider support
- Authentication and authorization
- Rate limiting
- Request IDs
- Distributed tracing
- Prometheus metrics
- Production Docker setup
- CI/CD pipeline
- Database migrations
- Better monitoring and alerting

---

## Project Goal

The goal of this project is to demonstrate practical backend engineering
concepts involved in building an LLM-powered API.

The project focuses on:

```text
API Design
    +
Caching
    +
Retries
    +
Streaming
    +
Usage Tracking
    +
PostgreSQL
    +
Redis
    +
Testing
    +
Error Handling
    +
Configuration Validation
```

The project intentionally uses a mock LLM provider so that these backend
engineering concepts can be developed and tested without requiring paid
LLM API usage.
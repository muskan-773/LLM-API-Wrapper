import os

from dotenv import load_dotenv


load_dotenv()


APP_NAME = os.getenv(
    "APP_NAME",
    "LLM API Wrapper Service",
)

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
)

# Kept for future real-provider integration.
# The current project uses a mock LLM.
ANTHROPIC_API_KEY = os.getenv(
    "ANTHROPIC_API_KEY"
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "claude-haiku-4-5-20251001",
)

MAX_TOKENS = int(
    os.getenv("MAX_TOKENS", "512")
)

MAX_RETRIES = int(
    os.getenv("MAX_RETRIES", "3")
)

RETRY_BASE_DELAY = float(
    os.getenv("RETRY_BASE_DELAY", "1.0")
)

REQUEST_TIMEOUT = float(
    os.getenv("REQUEST_TIMEOUT", "30")
)

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

CACHE_TTL_SECONDS = int(
    os.getenv("CACHE_TTL_SECONDS", "3600")
)


def validate() -> None:
    """Validate application configuration."""

    if MAX_TOKENS <= 0:
        raise ValueError(
            "MAX_TOKENS must be greater than 0"
        )

    if MAX_RETRIES < 0:
        raise ValueError(
            "MAX_RETRIES cannot be negative"
        )

    if RETRY_BASE_DELAY < 0:
        raise ValueError(
            "RETRY_BASE_DELAY cannot be negative"
        )

    if REQUEST_TIMEOUT <= 0:
        raise ValueError(
            "REQUEST_TIMEOUT must be greater than 0"
        )

    if CACHE_TTL_SECONDS <= 0:
        raise ValueError(
            "CACHE_TTL_SECONDS must be greater than 0"
        )
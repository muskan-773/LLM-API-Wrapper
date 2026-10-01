import os

from dotenv import load_dotenv

load_dotenv()


APP_NAME = os.getenv("APP_NAME", "LLM API Wrapper Service")
APP_ENV = os.getenv("APP_ENV", "development")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-haiku-4-5-20251001")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
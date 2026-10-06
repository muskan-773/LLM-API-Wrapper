import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import cache, config, database
from app.model.schemas import HealthResponse
from app.routes.chat import router as chat_router
from app.routes.usage import router as usage_router


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield
    await cache.close_cache()
    await database.close_db()


app = FastAPI(
    title=config.APP_NAME,
    version="0.2.0",
    lifespan=lifespan,
)


app.include_router(chat_router)
app.include_router(usage_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        app_name=config.APP_NAME,
        environment=config.APP_ENV,
    )


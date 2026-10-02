from fastapi import FastAPI

from app.model.schemas import HealthResponse
from app import config
from app.routes.chat import router as chat_router


app = FastAPI(
    title=config.APP_NAME,
    version="0.2.0"
)


app.include_router(chat_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        app_name=config.APP_NAME,
        environment=config.APP_ENV
    )
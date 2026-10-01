from fastapi import FastAPI
from app.model.schemas import HealthResponse
from app.routes.chat import router as chat_router

app = FastAPI()

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}


app.include_router(chat_router)

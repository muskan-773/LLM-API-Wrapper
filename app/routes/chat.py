from fastapi import APIRouter

from app.model.schemas import ChatRequest, ChatResponse
from app.services import llm_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await llm_service.generate_reply(request.message)

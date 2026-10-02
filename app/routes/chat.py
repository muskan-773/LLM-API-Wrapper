from fastapi import APIRouter, HTTPException

from app.model.schemas import ChatRequest, ChatResponse
from app.services import llm_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        return await llm_service.generate_reply(request.message)

    except llm_service.LLMServiceError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        ) from e
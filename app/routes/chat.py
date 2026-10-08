from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.model.schemas import ChatRequest, ChatResponse
from app.services import llm_service


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        return await llm_service.generate_reply(
            request.message
        )

    except llm_service.LLMServiceError as e:
        # Log the detailed internal error.
        # Do not expose internal details to the client.
        import logging

        logging.getLogger(__name__).exception(
            "Chat request failed"
        )

        raise HTTPException(
            status_code=502,
            detail="LLM service temporarily unavailable",
        ) from e


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        llm_service.stream_reply(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
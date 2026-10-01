from app.model.schemas import ChatResponse


async def generate_reply(message: str) -> ChatResponse:
    return ChatResponse(
        reply=f"Mock response: You said '{message}'",
        model="mock-model",
        input_tokens=len(message.split()),
        output_tokens=5
    )
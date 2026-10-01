from pydantic import BaseModel,Field

class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    reply: str
    model: str
    input_tokens: int
    output_tokens: int

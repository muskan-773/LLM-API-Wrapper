from datetime import datetime

from pydantic import BaseModel, Field


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
    cost_usd: float = 0.0
    cached: bool = False


class UsageRecord(BaseModel):
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float


class UsageSummary(BaseModel):
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    average_latency_ms: float
    recent: list[UsageRecord]
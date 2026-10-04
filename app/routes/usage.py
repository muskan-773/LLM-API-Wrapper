from fastapi import APIRouter

from app.model.schemas import UsageSummary
from app.services import usage_store


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageSummary)
async def get_usage():
    return await usage_store.get_summary()
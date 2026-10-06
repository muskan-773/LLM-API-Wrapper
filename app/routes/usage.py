from fastapi import APIRouter, Query

from app.model.schemas import DailyUsage, ModelUsage, UsageSummary
from app.services import usage_store


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageSummary)
async def get_usage():
    return await usage_store.get_summary()


@router.get("/daily", response_model=list[DailyUsage])
async def get_daily_usage(
    days: int = Query(7, ge=1, le=90),
):
    return await usage_store.get_daily(days)


@router.get("/by-model", response_model=list[ModelUsage])
async def get_usage_by_model():
    return await usage_store.get_by_model()
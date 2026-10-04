from app.database import get_pool
from app.model.schemas import UsageRecord, UsageSummary

async def add_record(record: UsageRecord) -> None:
    await get_pool().execute(
        """
        INSERT INTO usage_records
            (created_at, model, input_tokens, output_tokens, cost_usd, latency_ms)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        record.timestamp,
        record.model,
        record.input_tokens,
        record.output_tokens,
        record.cost_usd,
        record.latency_ms,
    )

async def get_summary(recent_limit: int = 10) -> UsageSummary:
    pool = get_pool()

    totals = await pool.fetchrow(
        """
        SELECT
            COUNT(*) AS total_requests,
            COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
            COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
            COALESCE(SUM(cost_usd), 0) AS total_cost_usd,
            COALESCE(AVG(latency_ms), 0) AS average_latency_ms
        FROM usage_records
        """
    )

    rows = await pool.fetch(
        """
        SELECT
            created_at,
            model,
            input_tokens,
            output_tokens,
            cost_usd,
            latency_ms
        FROM usage_records
        ORDER BY created_at DESC
        LIMIT $1
        """,
        recent_limit,
    )

    recent = [
        UsageRecord(
            timestamp=row["created_at"],
            model=row["model"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cost_usd=row["cost_usd"],
            latency_ms=row["latency_ms"],
        )
        for row in rows
    ]

    return UsageSummary(
        total_requests=totals["total_requests"],
        total_input_tokens=totals["total_input_tokens"],
        total_output_tokens=totals["total_output_tokens"],
        total_cost_usd=totals["total_cost_usd"],
        average_latency_ms=totals["average_latency_ms"],
        recent=recent,
    )
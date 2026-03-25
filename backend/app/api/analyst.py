"""AI Analyst API endpoints — briefings, company summaries, risk alerts."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyst.briefing_generator import generate_daily_briefing
from app.analyst.company_summarizer import generate_company_summary
from app.dependencies import get_db
from app.models.ai_briefing import AIBriefing
from app.schemas.analyst import (
    BriefingItem,
    BriefingListResponse,
    BriefingResponse,
    CompanySummaryResponse,
)

router = APIRouter(prefix="/analyst", tags=["analyst"])


@router.get("/briefing", response_model=BriefingResponse)
async def get_latest_briefing(db: AsyncSession = Depends(get_db)):
    """Get the latest AI market briefing."""
    result = await db.execute(
        select(AIBriefing)
        .where(AIBriefing.briefing_type == "daily_market")
        .order_by(AIBriefing.generated_at.desc())
        .limit(1)
    )
    briefing = result.scalar_one_or_none()
    if not briefing:
        return BriefingResponse(briefing=None)

    return BriefingResponse(
        briefing=BriefingItem(
            id=str(briefing.id),
            briefing_type=briefing.briefing_type,
            title=briefing.title,
            content=briefing.content,
            key_insights=briefing.key_insights,
            risk_factors=briefing.risk_factors,
            items_analyzed=briefing.items_analyzed,
            generated_at=briefing.generated_at,
        )
    )


@router.get("/briefings", response_model=BriefingListResponse)
async def list_briefings(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """List recent briefings."""
    result = await db.execute(
        select(AIBriefing)
        .where(AIBriefing.briefing_type == "daily_market")
        .order_by(AIBriefing.generated_at.desc())
        .limit(limit)
    )
    briefings = result.scalars().all()

    return BriefingListResponse(
        briefings=[
            BriefingItem(
                id=str(b.id),
                briefing_type=b.briefing_type,
                title=b.title,
                content=b.content,
                key_insights=b.key_insights,
                risk_factors=b.risk_factors,
                items_analyzed=b.items_analyzed,
                generated_at=b.generated_at,
            )
            for b in briefings
        ]
    )


@router.get("/summary/{symbol}", response_model=CompanySummaryResponse)
async def get_company_summary(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get the latest cached AI summary for a company. Use POST to generate a new one."""
    result = await db.execute(
        select(AIBriefing)
        .where(AIBriefing.briefing_type == "company_deep_dive")
        .order_by(AIBriefing.generated_at.desc())
        .limit(50)
    )
    for b in result.scalars().all():
        if symbol.upper() in b.title:
            return CompanySummaryResponse(
                symbol=symbol.upper(),
                summary=b.content,
                generated_at=b.generated_at,
            )

    return CompanySummaryResponse(
        symbol=symbol.upper(),
        summary="No summary available yet. Trigger generation via POST.",
    )


@router.post("/summary/{symbol}", response_model=CompanySummaryResponse)
async def generate_summary(symbol: str):
    """Generate a new AI summary for a company (mutating operation)."""
    briefing_id = await generate_company_summary(symbol)
    if not briefing_id:
        return CompanySummaryResponse(
            symbol=symbol.upper(),
            summary="No data available for this company.",
        )

    from app.core.database import get_session_factory
    async with get_session_factory()() as session:
        b = (await session.execute(
            select(AIBriefing).where(AIBriefing.id == briefing_id)
        )).scalar_one_or_none()

    return CompanySummaryResponse(
        symbol=symbol.upper(),
        summary=b.content if b else "Generation failed.",
        generated_at=b.generated_at if b else None,
    )


@router.post("/briefing/generate")
async def trigger_briefing():
    """Manually trigger a new daily briefing."""
    briefing_id = await generate_daily_briefing()
    return {"briefing_id": briefing_id, "status": "generated"}

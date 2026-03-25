"""Industry API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.company import Company
from app.models.company_industry import company_industries
from app.models.industry import Industry
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore
from app.schemas.industry import (
    HeatmapCompany,
    HeatmapResponse,
    IndustryBase,
    IndustryListResponse,
    IndustryWithSentiment,
    RadarCompany,
    RadarResponse,
    RadarSource,
)

router = APIRouter(prefix="/industries", tags=["industries"])


@router.get("", response_model=IndustryListResponse)
async def list_industries(db: AsyncSession = Depends(get_db)):
    """List all industries with latest aggregate sentiment (single query)."""
    # Subquery: latest daily aggregate per industry
    latest_agg_sq = (
        select(
            SentimentAggregate.industry_id,
            func.max(SentimentAggregate.period_start).label("max_start"),
        )
        .where(
            SentimentAggregate.industry_id.isnot(None),
            SentimentAggregate.period_type == "daily",
        )
        .group_by(SentimentAggregate.industry_id)
        .subquery()
    )

    result = await db.execute(
        select(Industry, SentimentAggregate)
        .outerjoin(
            latest_agg_sq,
            Industry.id == latest_agg_sq.c.industry_id,
        )
        .outerjoin(
            SentimentAggregate,
            (SentimentAggregate.industry_id == Industry.id)
            & (SentimentAggregate.period_start == latest_agg_sq.c.max_start)
            & (SentimentAggregate.period_type == "daily"),
        )
        .order_by(Industry.name)
    )
    rows = result.all()

    items = [
        IndustryWithSentiment(
            id=ind.id,
            name=ind.name,
            slug=ind.slug,
            display_color=ind.display_color,
            avg_score=agg.avg_score if agg else None,
            volume=agg.volume if agg else 0,
            momentum=agg.momentum if agg else None,
            confidence=agg.confidence if agg else None,
        )
        for ind, agg in rows
    ]

    return IndustryListResponse(industries=items)


@router.get("/{slug}/heatmap", response_model=HeatmapResponse)
async def get_industry_heatmap(slug: str, db: AsyncSession = Depends(get_db)):
    """Get treemap heatmap data for an industry (companies + scores)."""
    # Get industry
    result = await db.execute(select(Industry).where(Industry.slug == slug))
    industry = result.scalar_one_or_none()
    if not industry:
        raise HTTPException(status_code=404, detail=f"Industry '{slug}' not found")

    # Get companies in this industry
    comp_result = await db.execute(
        select(Company)
        .join(company_industries, Company.id == company_industries.c.company_id)
        .where(company_industries.c.industry_id == industry.id)
    )
    companies = comp_result.scalars().all()

    heatmap_items = []
    for comp in companies:
        # Get latest sentiment score stats for this company
        score_result = await db.execute(
            select(
                func.avg(SentimentScore.ensemble_score).label("avg_score"),
                func.count(SentimentScore.id).label("volume"),
            ).where(SentimentScore.company_id == comp.id)
        )
        row = score_result.one_or_none()

        heatmap_items.append(
            HeatmapCompany(
                symbol=comp.symbol,
                name=comp.name,
                score=float(row.avg_score) if row and row.avg_score else 0.0,
                volume=int(row.volume) if row and row.volume else 0,
            )
        )

    return HeatmapResponse(
        industry=IndustryBase(
            id=industry.id,
            name=industry.name,
            slug=industry.slug,
            display_color=industry.display_color,
        ),
        companies=heatmap_items,
    )


@router.get("/{slug}/radar", response_model=RadarResponse)
async def get_industry_radar(slug: str, db: AsyncSession = Depends(get_db)):
    """Get per-source sentiment breakdown for radar chart."""
    result = await db.execute(select(Industry).where(Industry.slug == slug))
    industry = result.scalar_one_or_none()
    if not industry:
        raise HTTPException(status_code=404, detail=f"Industry '{slug}' not found")

    comp_result = await db.execute(
        select(Company)
        .join(company_industries, Company.id == company_industries.c.company_id)
        .where(company_industries.c.industry_id == industry.id)
    )
    companies = comp_result.scalars().all()

    radar_items = []
    for comp in companies:
        sources = {}
        for source in ("reddit", "news", "stocktwits"):
            src_result = await db.execute(
                select(func.avg(SentimentScore.ensemble_score)).where(
                    SentimentScore.company_id == comp.id,
                    SentimentScore.source == source,
                )
            )
            avg = src_result.scalar_one_or_none()
            sources[source] = float(avg) if avg else None

        radar_items.append(
            RadarCompany(
                symbol=comp.symbol,
                name=comp.name,
                sources=RadarSource(**sources),
            )
        )

    return RadarResponse(
        industry=IndustryBase(
            id=industry.id,
            name=industry.name,
            slug=industry.slug,
            display_color=industry.display_color,
        ),
        companies=radar_items,
    )

"""Sentiment feed API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.anomaly_alert import AnomalyAlert
from app.models.company import Company
from app.models.industry import Industry
from app.models.raw_content import RawContent
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore
from app.schemas.sentiment import MarketOverview, SentimentFeedItem, SentimentFeedResponse

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/feed", response_model=SentimentFeedResponse)
async def get_sentiment_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str = Query("all", pattern="^(all|reddit|news|stocktwits)$"),
    label: str = Query("all"),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated sentiment feed with optional filters."""
    query = (
        select(SentimentScore, RawContent, Company)
        .join(RawContent, SentimentScore.raw_content_id == RawContent.id)
        .outerjoin(Company, SentimentScore.company_id == Company.id)
        .order_by(SentimentScore.scored_at.desc())
    )

    if source != "all":
        query = query.where(SentimentScore.source == source)

    if label != "all":
        query = query.where(SentimentScore.ensemble_label == label)

    # Count total
    count_query = select(func.count(SentimentScore.id))
    if source != "all":
        count_query = count_query.where(SentimentScore.source == source)
    if label != "all":
        count_query = count_query.where(SentimentScore.ensemble_label == label)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for score, content, company in rows:
        body = content.body or ""
        items.append(
            SentimentFeedItem(
                id=score.id,
                source=score.source,
                company_symbol=company.symbol if company else None,
                company_name=company.name if company else None,
                title=content.title,
                body_excerpt=body[:200] + ("..." if len(body) > 200 else ""),
                ensemble_score=score.ensemble_score,
                ensemble_label=score.ensemble_label,
                ensemble_confidence=score.ensemble_confidence,
                finbert_label=score.finbert_label,
                llm_reasoning=score.llm_reasoning,
                scored_at=score.scored_at,
            )
        )

    return SentimentFeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/overview", response_model=MarketOverview)
async def get_market_overview(db: AsyncSession = Depends(get_db)):
    """Get overall market sentiment overview for the dashboard."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Overall score today
    score_result = await db.execute(
        select(func.avg(SentimentScore.ensemble_score)).where(
            SentimentScore.scored_at >= today
        )
    )
    overall_score = score_result.scalar() or 0.0

    # Total items today
    count_result = await db.execute(
        select(func.count(SentimentScore.id)).where(
            SentimentScore.scored_at >= today
        )
    )
    total_items = count_result.scalar() or 0

    # Active alerts
    alerts_result = await db.execute(
        select(func.count(AnomalyAlert.id)).where(AnomalyAlert.is_active == True)  # noqa: E712
    )
    active_alerts = alerts_result.scalar() or 0

    # Source count
    sources_result = await db.execute(
        select(func.count(func.distinct(SentimentScore.source))).where(
            SentimentScore.scored_at >= today
        )
    )
    sources_active = sources_result.scalar() or 0

    # Per-industry breakdown
    industries_result = await db.execute(select(Industry).order_by(Industry.name))
    industries = industries_result.scalars().all()

    industry_data = []
    for ind in industries:
        agg_result = await db.execute(
            select(SentimentAggregate)
            .where(
                SentimentAggregate.industry_id == ind.id,
                SentimentAggregate.period_type == "daily",
            )
            .order_by(SentimentAggregate.period_start.desc())
            .limit(1)
        )
        agg = agg_result.scalar_one_or_none()
        industry_data.append({
            "slug": ind.slug,
            "name": ind.name,
            "color": ind.display_color,
            "score": agg.avg_score if agg else None,
            "volume": agg.volume if agg else 0,
        })

    # Label
    if overall_score > 0.2:
        label = "bullish"
    elif overall_score < -0.2:
        label = "bearish"
    else:
        label = "neutral"

    return MarketOverview(
        overall_score=float(overall_score),
        overall_label=label,
        total_items_today=total_items,
        active_alerts=active_alerts,
        sources_active=sources_active,
        industries=industry_data,
    )

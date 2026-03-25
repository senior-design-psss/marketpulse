"""Company API endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.company import Company
from app.models.company_industry import company_industries
from app.models.industry import Industry
from app.models.price_data import PriceData
from app.models.raw_content import RawContent
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore
from app.schemas.company import (
    CompanyBase,
    CompanyDetail,
    CompanyListResponse,
    CompanyTimeseriesResponse,
    CompanyWithSentiment,
    TimeseriesPoint,
)

router = APIRouter(prefix="/companies", tags=["companies"])

TIMEFRAME_HOURS = {
    "1h": 1,
    "6h": 6,
    "24h": 24,
    "7d": 168,
    "30d": 720,
}


@router.get("", response_model=CompanyListResponse)
async def list_companies(db: AsyncSession = Depends(get_db)):
    """List all tracked companies with current sentiment (optimized)."""
    # Latest hourly aggregate per company (single subquery)
    latest_sq = (
        select(
            SentimentAggregate.company_id,
            func.max(SentimentAggregate.period_start).label("max_start"),
        )
        .where(
            SentimentAggregate.company_id.isnot(None),
            SentimentAggregate.period_type == "hourly",
        )
        .group_by(SentimentAggregate.company_id)
        .subquery()
    )

    result = await db.execute(
        select(Company, SentimentAggregate)
        .outerjoin(latest_sq, Company.id == latest_sq.c.company_id)
        .outerjoin(
            SentimentAggregate,
            (SentimentAggregate.company_id == Company.id)
            & (SentimentAggregate.period_start == latest_sq.c.max_start)
            & (SentimentAggregate.period_type == "hourly"),
        )
        .order_by(Company.symbol)
    )
    company_rows = result.all()

    # Batch-load all industry mappings
    ind_result = await db.execute(
        select(company_industries.c.company_id, Industry.slug).join(
            Industry, Industry.id == company_industries.c.industry_id
        )
    )
    ind_map: dict[str, list[str]] = {}
    for cid, slug in ind_result.all():
        ind_map.setdefault(str(cid), []).append(slug)

    # Batch-load latest price per company
    latest_price_sq = (
        select(PriceData.company_id, func.max(PriceData.date).label("max_date"))
        .group_by(PriceData.company_id)
        .subquery()
    )
    price_result = await db.execute(
        select(PriceData)
        .join(
            latest_price_sq,
            (PriceData.company_id == latest_price_sq.c.company_id)
            & (PriceData.date == latest_price_sq.c.max_date),
        )
    )
    price_map: dict[str, PriceData] = {
        str(p.company_id): p for p in price_result.scalars().all()
    }

    items = []
    for comp, agg in company_rows:
        price = price_map.get(str(comp.id))
        items.append(
            CompanyWithSentiment(
                id=comp.id,
                symbol=comp.symbol,
                name=comp.name,
                avg_score=agg.avg_score if agg else None,
                volume=agg.volume if agg else 0,
                momentum=agg.momentum if agg else None,
                acceleration=agg.acceleration if agg else None,
                confidence=agg.confidence if agg else None,
                industries=ind_map.get(str(comp.id), []),
                price=price.close if price else None,
                price_change=round(price.daily_return * 100, 2) if price and price.daily_return else None,
                price_date=str(price.date) if price else None,
            )
        )

    return CompanyListResponse(companies=items)


@router.get("/{symbol}", response_model=CompanyDetail)
async def get_company(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get detailed company profile with sentiment breakdown."""
    result = await db.execute(
        select(Company).where(func.upper(Company.symbol) == symbol.upper())
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    # Get latest aggregate
    agg_result = await db.execute(
        select(SentimentAggregate)
        .where(
            SentimentAggregate.company_id == comp.id,
            SentimentAggregate.period_type == "hourly",
        )
        .order_by(SentimentAggregate.period_start.desc())
        .limit(1)
    )
    agg = agg_result.scalar_one_or_none()

    # Get per-source averages
    source_stats = {}
    for source in ("reddit", "news", "stocktwits"):
        src_result = await db.execute(
            select(
                func.avg(SentimentScore.ensemble_score).label("avg"),
                func.count(SentimentScore.id).label("vol"),
            ).where(
                SentimentScore.company_id == comp.id,
                SentimentScore.source == source,
            )
        )
        row = src_result.one()
        source_stats[source] = {
            "avg": float(row.avg) if row.avg else None,
            "vol": int(row.vol) if row.vol else 0,
        }

    # Get industries
    ind_result = await db.execute(
        select(Industry.slug)
        .join(company_industries, Industry.id == company_industries.c.industry_id)
        .where(company_industries.c.company_id == comp.id)
    )
    industry_slugs = [row[0] for row in ind_result.all()]

    # Get latest price
    price_result = await db.execute(
        select(PriceData)
        .where(PriceData.company_id == comp.id)
        .order_by(PriceData.date.desc())
        .limit(1)
    )
    price = price_result.scalar_one_or_none()

    return CompanyDetail(
        id=comp.id,
        symbol=comp.symbol,
        name=comp.name,
        avg_score=agg.avg_score if agg else None,
        volume=agg.volume if agg else 0,
        momentum=agg.momentum if agg else None,
        acceleration=agg.acceleration if agg else None,
        confidence=agg.confidence if agg else None,
        industries=industry_slugs,
        price=price.close if price else None,
        price_change=round(price.daily_return * 100, 2) if price and price.daily_return else None,
        price_date=str(price.date) if price else None,
        reddit_avg=source_stats["reddit"]["avg"],
        reddit_volume=source_stats["reddit"]["vol"],
        news_avg=source_stats["news"]["avg"],
        news_volume=source_stats["news"]["vol"],
        stocktwits_avg=source_stats["stocktwits"]["avg"],
        stocktwits_volume=source_stats["stocktwits"]["vol"],
    )


@router.get("/{symbol}/timeseries", response_model=CompanyTimeseriesResponse)
async def get_company_timeseries(
    symbol: str,
    timeframe: str = Query("24h", pattern="^(1h|6h|24h|7d|30d)$"),
    source: str = Query("all", pattern="^(all|reddit|news|stocktwits)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get historical sentiment timeseries for a company."""
    result = await db.execute(
        select(Company).where(func.upper(Company.symbol) == symbol.upper())
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    hours = TIMEFRAME_HOURS.get(timeframe, 24)
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(SentimentScore)
        .where(
            SentimentScore.company_id == comp.id,
            SentimentScore.scored_at >= since,
        )
        .order_by(SentimentScore.scored_at.asc())
    )

    if source != "all":
        query = query.where(SentimentScore.source == source)

    scores_result = await db.execute(query)
    scores = scores_result.scalars().all()

    data = [
        TimeseriesPoint(
            timestamp=s.scored_at,
            score=s.ensemble_score,
            volume=1,
            source=s.source,
        )
        for s in scores
    ]

    return CompanyTimeseriesResponse(
        company=CompanyBase(id=comp.id, symbol=comp.symbol, name=comp.name),
        data=data,
        timeframe=timeframe,
    )


@router.get("/{symbol}/sources")
async def get_company_sources(
    symbol: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get the actual source articles/posts that contribute to this company's sentiment."""
    result = await db.execute(
        select(Company).where(func.upper(Company.symbol) == symbol.upper())
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    # Count total
    count_result = await db.execute(
        select(func.count(SentimentScore.id)).where(SentimentScore.company_id == comp.id)
    )
    total = count_result.scalar() or 0

    # Get scored items with their raw content
    offset = (page - 1) * page_size
    items_result = await db.execute(
        select(SentimentScore, RawContent)
        .join(RawContent, SentimentScore.raw_content_id == RawContent.id)
        .where(SentimentScore.company_id == comp.id)
        .order_by(SentimentScore.scored_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    items = []
    for score, content in items_result.all():
        items.append({
            "id": str(score.id),
            "source": score.source,
            "title": content.title,
            "body": content.body[:300] + ("..." if len(content.body) > 300 else ""),
            "url": content.url,
            "author": content.author,
            "subreddit": content.subreddit,
            "published_at": content.published_at.isoformat() if content.published_at else None,
            "ensemble_score": score.ensemble_score,
            "ensemble_label": score.ensemble_label,
            "ensemble_confidence": score.ensemble_confidence,
            "finbert_label": score.finbert_label,
            "finbert_positive": score.finbert_positive,
            "finbert_negative": score.finbert_negative,
            "llm_score": score.llm_score,
            "llm_reasoning": score.llm_reasoning,
            "scored_at": score.scored_at.isoformat() if score.scored_at else None,
        })

    return {"symbol": comp.symbol, "total": total, "page": page, "items": items}


@router.get("/{symbol}/prices")
async def get_company_prices(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get historical price data for a company."""
    result = await db.execute(
        select(Company).where(func.upper(Company.symbol) == symbol.upper())
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")

    prices_result = await db.execute(
        select(PriceData)
        .where(PriceData.company_id == comp.id)
        .order_by(PriceData.date.desc())
        .limit(days)
    )
    prices = prices_result.scalars().all()

    return {
        "symbol": comp.symbol,
        "prices": [
            {
                "date": str(p.date),
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
                "daily_return": p.daily_return,
            }
            for p in reversed(prices)
        ],
    }

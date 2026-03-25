"""Compute hourly and daily sentiment aggregates per company and industry."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.models.company import Company
from app.models.company_industry import company_industries
from app.models.industry import Industry
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)


async def _compute_company_aggregate(
    session: AsyncSession,
    company_id,
    period_type: str,
    period_start: datetime,
    period_end: datetime,
) -> dict | None:
    """Compute aggregate stats for a company over a time window."""
    base = and_(
        SentimentScore.company_id == company_id,
        SentimentScore.scored_at >= period_start,
        SentimentScore.scored_at < period_end,
    )

    result = await session.execute(
        select(
            func.avg(SentimentScore.ensemble_score).label("avg_score"),
            func.count(SentimentScore.id).label("volume"),
            func.stddev(SentimentScore.ensemble_score).label("stddev"),
        ).where(base)
    )
    row = result.one()
    if not row.volume or row.volume == 0:
        return None

    # Per-source breakdown
    source_stats = {}
    for source in ("reddit", "news", "stocktwits"):
        src_result = await session.execute(
            select(
                func.avg(SentimentScore.ensemble_score).label("avg"),
                func.count(SentimentScore.id).label("vol"),
            ).where(and_(base, SentimentScore.source == source))
        )
        src_row = src_result.one()
        source_stats[source] = {
            "avg": float(src_row.avg) if src_row.avg else None,
            "vol": int(src_row.vol) if src_row.vol else 0,
        }

    return {
        "avg_score": float(row.avg_score),
        "volume": int(row.volume),
        "score_stddev": float(row.stddev) if row.stddev else None,
        "reddit_avg": source_stats["reddit"]["avg"],
        "reddit_volume": source_stats["reddit"]["vol"],
        "news_avg": source_stats["news"]["avg"],
        "news_volume": source_stats["news"]["vol"],
        "stocktwits_avg": source_stats["stocktwits"]["avg"],
        "stocktwits_volume": source_stats["stocktwits"]["vol"],
    }


async def compute_aggregates(period_type: str = "hourly") -> int:
    """
    Compute aggregates for the most recent period.
    period_type: 'hourly' or 'daily'
    Returns the number of aggregates created/updated.
    """
    now = datetime.now(timezone.utc)

    if period_type == "hourly":
        # Compute current hour (not previous) so data appears immediately
        period_start = now.replace(minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(hours=1)
    else:  # daily
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)

    count = 0
    async with get_session_factory()() as session:
        # Company aggregates
        companies = (await session.execute(select(Company))).scalars().all()
        for company in companies:
            stats = await _compute_company_aggregate(
                session, company.id, period_type, period_start, period_end
            )
            if stats is None:
                continue

            # Upsert aggregate
            existing = await session.execute(
                select(SentimentAggregate).where(
                    SentimentAggregate.company_id == company.id,
                    SentimentAggregate.industry_id == None,  # noqa: E711
                    SentimentAggregate.period_type == period_type,
                    SentimentAggregate.period_start == period_start,
                )
            )
            agg = existing.scalar_one_or_none()
            if agg:
                for k, v in stats.items():
                    setattr(agg, k, v)
            else:
                agg = SentimentAggregate(
                    company_id=company.id,
                    industry_id=None,
                    period_type=period_type,
                    period_start=period_start,
                    **stats,
                )
                session.add(agg)
            count += 1

        # Industry aggregates (average of company aggregates)
        industries = (await session.execute(select(Industry))).scalars().all()
        for industry in industries:
            # Get company IDs in this industry
            comp_ids_result = await session.execute(
                select(company_industries.c.company_id).where(
                    company_industries.c.industry_id == industry.id
                )
            )
            comp_ids = [r[0] for r in comp_ids_result.all()]
            if not comp_ids:
                continue

            ind_result = await session.execute(
                select(
                    func.avg(SentimentScore.ensemble_score).label("avg_score"),
                    func.count(SentimentScore.id).label("volume"),
                ).where(
                    SentimentScore.company_id.in_(comp_ids),
                    SentimentScore.scored_at >= period_start,
                    SentimentScore.scored_at < period_end,
                )
            )
            ind_row = ind_result.one()
            if not ind_row.volume or ind_row.volume == 0:
                continue

            existing = await session.execute(
                select(SentimentAggregate).where(
                    SentimentAggregate.company_id == None,  # noqa: E711
                    SentimentAggregate.industry_id == industry.id,
                    SentimentAggregate.period_type == period_type,
                    SentimentAggregate.period_start == period_start,
                )
            )
            agg = existing.scalar_one_or_none()
            if agg:
                agg.avg_score = float(ind_row.avg_score)
                agg.volume = int(ind_row.volume)
            else:
                agg = SentimentAggregate(
                    company_id=None,
                    industry_id=industry.id,
                    period_type=period_type,
                    period_start=period_start,
                    avg_score=float(ind_row.avg_score),
                    volume=int(ind_row.volume),
                )
                session.add(agg)
            count += 1

        await session.commit()

    logger.info(f"Computed {count} {period_type} aggregates")
    return count

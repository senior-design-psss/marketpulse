"""Sentiment momentum — velocity and acceleration of sentiment change."""

import logging
from datetime import timedelta

from sqlalchemy import select

from app.core.database import get_session_factory
from app.models.company import Company
from app.models.sentiment_aggregate import SentimentAggregate

logger = logging.getLogger(__name__)

LOOKBACK_HOURS = 6


async def compute_momentum() -> int:
    """
    Compute momentum (velocity) and acceleration for each company's latest hourly aggregate.

    momentum = (score[now] - score[now - 6h]) / 6
    acceleration = (momentum[now] - momentum[now - 6h]) / 6

    Returns count of aggregates updated.
    """
    count = 0

    async with get_session_factory()() as session:
        companies = (await session.execute(select(Company))).scalars().all()

        for company in companies:
            # Get the two most recent hourly aggregates separated by LOOKBACK_HOURS
            result = await session.execute(
                select(SentimentAggregate)
                .where(
                    SentimentAggregate.company_id == company.id,
                    SentimentAggregate.period_type == "hourly",
                )
                .order_by(SentimentAggregate.period_start.desc())
                .limit(12)  # ~12 hours of hourly data
            )
            aggregates = result.scalars().all()
            if len(aggregates) < 2:
                continue

            current = aggregates[0]

            # Find aggregate ~6 hours ago
            target_time = current.period_start - timedelta(hours=LOOKBACK_HOURS)
            prev = None
            for agg in aggregates[1:]:
                if agg.period_start <= target_time:
                    prev = agg
                    break

            if prev is None:
                prev = aggregates[-1]  # Use oldest available

            hours_diff = max(
                (current.period_start - prev.period_start).total_seconds() / 3600, 1
            )

            # Momentum (velocity)
            momentum = (current.avg_score - prev.avg_score) / hours_diff

            # Acceleration (change in momentum)
            acceleration = None
            if prev.momentum is not None:
                acceleration = (momentum - prev.momentum) / hours_diff

            current.momentum = momentum
            current.acceleration = acceleration
            count += 1

        await session.commit()

    logger.info(f"Computed momentum for {count} company aggregates")
    return count

"""Composite confidence scoring based on volume, source diversity, and model agreement."""

import logging

from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.models.company import Company
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)

# Weights for confidence components
VOLUME_WEIGHT = 0.40
DIVERSITY_WEIGHT = 0.30
AGREEMENT_WEIGHT = 0.30

# Volume cap — 20+ items = full volume confidence
VOLUME_CAP = 20


async def compute_confidence() -> int:
    """
    Compute composite confidence for the latest hourly aggregate of each company.

    confidence = 0.4 * volume_factor + 0.3 * source_diversity + 0.3 * model_agreement
    """
    count = 0

    async with get_session_factory()() as session:
        companies = (await session.execute(select(Company))).scalars().all()

        for company in companies:
            # Get latest hourly aggregate
            result = await session.execute(
                select(SentimentAggregate)
                .where(
                    SentimentAggregate.company_id == company.id,
                    SentimentAggregate.period_type == "hourly",
                )
                .order_by(SentimentAggregate.period_start.desc())
                .limit(1)
            )
            agg = result.scalar_one_or_none()
            if agg is None or agg.volume == 0:
                continue

            # Volume factor: min(volume / VOLUME_CAP, 1.0)
            volume_factor = min(agg.volume / VOLUME_CAP, 1.0)

            # Source diversity: count how many sources have data
            sources_with_data = sum([
                1 for v in [agg.reddit_volume, agg.news_volume, agg.stocktwits_volume]
                if v and v > 0
            ])
            diversity_factor = sources_with_data / 3.0

            # Model agreement: average ensemble_confidence of recent scores
            scores_result = await session.execute(
                select(func.avg(SentimentScore.ensemble_confidence)).where(
                    SentimentScore.company_id == company.id,
                    SentimentScore.scored_at >= agg.period_start,
                )
            )
            avg_agreement = scores_result.scalar() or 0.5
            agreement_factor = float(avg_agreement)

            # Composite
            confidence = (
                VOLUME_WEIGHT * volume_factor
                + DIVERSITY_WEIGHT * diversity_factor
                + AGREEMENT_WEIGHT * agreement_factor
            )
            agg.confidence = round(confidence, 4)
            count += 1

        await session.commit()

    logger.info(f"Computed confidence for {count} company aggregates")
    return count

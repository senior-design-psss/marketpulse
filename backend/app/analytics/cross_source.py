"""Cross-source correlation — detect divergence between Reddit, News, and StockTwits."""

import logging
from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import get_session_factory
from app.models.company import Company
from app.models.sentiment_aggregate import SentimentAggregate

logger = logging.getLogger(__name__)

DIVERGENCE_THRESHOLD = 0.4  # If any two sources differ by > 0.4, flag it


@dataclass
class DivergenceSignal:
    company_id: str
    symbol: str
    source_a: str
    source_b: str
    score_a: float
    score_b: float
    divergence: float


async def detect_cross_source_divergences() -> list[DivergenceSignal]:
    """
    For each company, compare per-source sentiment averages.
    Flag pairs that differ by more than DIVERGENCE_THRESHOLD.
    """
    signals: list[DivergenceSignal] = []

    async with get_session_factory()() as session:
        companies = (await session.execute(select(Company))).scalars().all()

        for company in companies:
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
            if agg is None:
                continue

            sources = {
                "reddit": agg.reddit_avg,
                "news": agg.news_avg,
                "stocktwits": agg.stocktwits_avg,
            }

            # Check all pairs
            names = [k for k, v in sources.items() if v is not None]
            for i, a in enumerate(names):
                for b in names[i + 1 :]:
                    diff = abs(sources[a] - sources[b])
                    if diff >= DIVERGENCE_THRESHOLD:
                        signals.append(
                            DivergenceSignal(
                                company_id=str(company.id),
                                symbol=company.symbol,
                                source_a=a,
                                source_b=b,
                                score_a=sources[a],
                                score_b=sources[b],
                                divergence=round(diff, 4),
                            )
                        )

    logger.info(f"Found {len(signals)} cross-source divergences")
    return signals

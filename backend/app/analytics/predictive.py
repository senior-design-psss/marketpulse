"""Predictive signals — correlate sentiment shifts with price movements."""

import logging
from datetime import timedelta

from sqlalchemy import select

from app.core.database import get_session_factory
from app.models.company import Company
from app.models.predictive_signal import PredictiveSignal
from app.models.price_data import PriceData
from app.models.sentiment_aggregate import SentimentAggregate

logger = logging.getLogger(__name__)

MIN_DATA_POINTS = 14  # Need at least 14 days of data


async def compute_predictive_signals() -> int:
    """
    For each company, compute correlation between daily sentiment and next-day returns.
    Creates PredictiveSignal records for statistically meaningful correlations.

    Returns number of signals created.
    """
    count = 0

    async with get_session_factory()() as session:
        companies = (await session.execute(select(Company))).scalars().all()

        for company in companies:
            # Get daily aggregates
            agg_result = await session.execute(
                select(SentimentAggregate)
                .where(
                    SentimentAggregate.company_id == company.id,
                    SentimentAggregate.period_type == "daily",
                )
                .order_by(SentimentAggregate.period_start.asc())
            )
            aggregates = agg_result.scalars().all()

            # Get price data
            price_result = await session.execute(
                select(PriceData)
                .where(PriceData.company_id == company.id)
                .order_by(PriceData.date.asc())
            )
            prices = price_result.scalars().all()

            if len(aggregates) < MIN_DATA_POINTS or len(prices) < MIN_DATA_POINTS:
                continue

            # Build date-keyed lookups
            sentiment_by_date = {
                agg.period_start.date(): agg.avg_score for agg in aggregates
            }
            return_by_date = {
                p.date: p.daily_return for p in prices if p.daily_return is not None
            }

            # Compute correlation: sentiment[t] vs return[t+1]
            for lag_days in [1, 2, 3]:
                pairs = []
                all_dates = sorted(sentiment_by_date.keys())
                for d in all_dates:
                    next_day = d + timedelta(days=lag_days)
                    if d in sentiment_by_date and next_day in return_by_date:
                        pairs.append((sentiment_by_date[d], return_by_date[next_day]))

                if len(pairs) < MIN_DATA_POINTS:
                    continue

                # Pearson correlation
                corr = _pearson(pairs)
                if corr is None or abs(corr) < 0.2:
                    continue  # Not significant enough

                direction = "bullish" if corr > 0 else "bearish"
                strength = min(abs(corr), 1.0)

                signal = PredictiveSignal(
                    company_id=company.id,
                    signal_type="sentiment_leads_price",
                    direction=direction,
                    strength=round(strength, 4),
                    sentiment_window_days=len(pairs),
                    correlation=round(corr, 4),
                    lag_hours=lag_days * 24,
                    description=(
                        f"{company.symbol} sentiment shows {abs(corr):.2f} correlation "
                        f"with {lag_days}-day forward returns. "
                        f"{'Positive' if corr > 0 else 'Negative'} sentiment tends to "
                        f"{'precede gains' if corr > 0 else 'precede losses'}."
                    ),
                )
                session.add(signal)
                count += 1

        await session.commit()

    logger.info(f"Generated {count} predictive signals")
    return count


def _pearson(pairs: list[tuple[float, float]]) -> float | None:
    """Compute Pearson correlation coefficient."""
    n = len(pairs)
    if n < 3:
        return None

    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in pairs) / n
    std_x = (sum((xi - mean_x) ** 2 for xi in x) / n) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5

    if std_x == 0 or std_y == 0:
        return None

    return cov / (std_x * std_y)

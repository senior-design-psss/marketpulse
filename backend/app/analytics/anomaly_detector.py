"""Anomaly detection using rolling Z-score on sentiment aggregates."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.models.anomaly_alert import AnomalyAlert
from app.models.company import Company
from app.models.sentiment_aggregate import SentimentAggregate

logger = logging.getLogger(__name__)

# Z-score thresholds for severity levels
SEVERITY_MAP = [
    (4.0, "critical"),
    (3.5, "high"),
    (3.0, "medium"),
    (2.5, "low"),
]

ROLLING_WINDOW_DAYS = 7


async def detect_anomalies() -> int:
    """
    Detect anomalies by comparing the latest hourly aggregate against
    a 7-day rolling window for each company.

    Returns number of new alerts created.
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=ROLLING_WINDOW_DAYS)
    alerts_created = 0

    async with get_session_factory()() as session:
        companies = (await session.execute(select(Company))).scalars().all()

        for company in companies:
            # Get latest hourly aggregate
            latest_result = await session.execute(
                select(SentimentAggregate)
                .where(
                    SentimentAggregate.company_id == company.id,
                    SentimentAggregate.period_type == "hourly",
                )
                .order_by(SentimentAggregate.period_start.desc())
                .limit(1)
            )
            latest = latest_result.scalar_one_or_none()
            if latest is None:
                continue

            # Get rolling window stats
            stats_result = await session.execute(
                select(
                    func.avg(SentimentAggregate.avg_score).label("mean"),
                    func.stddev(SentimentAggregate.avg_score).label("stddev"),
                    func.count(SentimentAggregate.id).label("count"),
                ).where(
                    SentimentAggregate.company_id == company.id,
                    SentimentAggregate.period_type == "hourly",
                    SentimentAggregate.period_start >= window_start,
                )
            )
            stats = stats_result.one()
            if not stats.count or stats.count < 5 or not stats.stddev or stats.stddev == 0:
                continue

            mean = float(stats.mean)
            stddev = float(stats.stddev)
            z_score = (latest.avg_score - mean) / stddev

            # Check if anomalous
            severity = None
            for threshold, sev in SEVERITY_MAP:
                if abs(z_score) >= threshold:
                    severity = sev
                    break

            if severity is None:
                continue

            # Check if we already have an active alert for this company
            existing = await session.execute(
                select(AnomalyAlert).where(
                    AnomalyAlert.company_id == company.id,
                    AnomalyAlert.is_active == True,  # noqa: E712
                    AnomalyAlert.alert_type == "sentiment_spike",
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue  # Already alerted

            direction = "positive" if z_score > 0 else "negative"
            alert = AnomalyAlert(
                company_id=company.id,
                alert_type="sentiment_spike",
                severity=severity,
                title=f"{company.symbol}: Unusual {direction} sentiment",
                description=(
                    f"{company.symbol} sentiment score ({latest.avg_score:+.3f}) is "
                    f"{abs(z_score):.1f} standard deviations from its 7-day mean ({mean:+.3f}). "
                    f"This {direction} deviation may indicate a significant market event."
                ),
                metric_value=latest.avg_score,
                baseline_value=mean,
                z_score=round(z_score, 3),
                is_active=True,
            )
            session.add(alert)
            alerts_created += 1

        # Auto-resolve old alerts (> 24h)
        cutoff = now - timedelta(hours=24)
        old_alerts = await session.execute(
            select(AnomalyAlert).where(
                AnomalyAlert.is_active == True,  # noqa: E712
                AnomalyAlert.triggered_at < cutoff,
            )
        )
        for alert in old_alerts.scalars().all():
            alert.is_active = False
            alert.resolved_at = now

        await session.commit()

    logger.info(f"Anomaly detection: {alerts_created} new alerts")
    return alerts_created

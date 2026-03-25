"""Analytics API endpoints — momentum, anomalies, cross-source, predictive."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.cross_source import detect_cross_source_divergences
from app.dependencies import get_db
from app.models.anomaly_alert import AnomalyAlert
from app.models.company import Company
from app.models.predictive_signal import PredictiveSignal
from app.models.sentiment_aggregate import SentimentAggregate
from app.schemas.analytics import (
    AnomalyAlertItem,
    AnomalyResponse,
    CrossSourceItem,
    CrossSourceResponse,
    MomentumItem,
    MomentumResponse,
    PredictiveResponse,
    PredictiveSignalItem,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/momentum", response_model=MomentumResponse)
async def get_momentum(db: AsyncSession = Depends(get_db)):
    """Get top companies by sentiment momentum (velocity of change)."""
    result = await db.execute(
        select(SentimentAggregate, Company)
        .join(Company, SentimentAggregate.company_id == Company.id)
        .where(
            SentimentAggregate.period_type == "hourly",
            SentimentAggregate.momentum != None,  # noqa: E711
        )
        .order_by(SentimentAggregate.period_start.desc())
    )
    rows = result.all()

    # Deduplicate — keep only latest per company
    seen = set()
    items = []
    for agg, comp in rows:
        if comp.symbol in seen:
            continue
        seen.add(comp.symbol)
        items.append(
            MomentumItem(
                symbol=comp.symbol,
                name=comp.name,
                avg_score=agg.avg_score,
                momentum=agg.momentum,
                acceleration=agg.acceleration,
                volume=agg.volume,
            )
        )

    # Sort by absolute momentum
    items.sort(key=lambda x: abs(x.momentum), reverse=True)
    return MomentumResponse(movers=items[:20])


@router.get("/anomalies", response_model=AnomalyResponse)
async def get_anomalies(db: AsyncSession = Depends(get_db)):
    """Get active anomaly alerts."""
    result = await db.execute(
        select(AnomalyAlert, Company)
        .outerjoin(Company, AnomalyAlert.company_id == Company.id)
        .where(AnomalyAlert.is_active == True)  # noqa: E712
        .order_by(AnomalyAlert.triggered_at.desc())
    )
    rows = result.all()

    alerts = [
        AnomalyAlertItem(
            id=str(alert.id),
            company_symbol=comp.symbol if comp else None,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            metric_value=alert.metric_value,
            baseline_value=alert.baseline_value,
            z_score=alert.z_score,
            triggered_at=alert.triggered_at,
        )
        for alert, comp in rows
    ]

    return AnomalyResponse(alerts=alerts)


@router.get("/cross-source", response_model=CrossSourceResponse)
async def get_cross_source():
    """Get cross-source divergence signals."""
    divergences = await detect_cross_source_divergences()
    return CrossSourceResponse(
        signals=[
            CrossSourceItem(
                symbol=d.symbol,
                source_a=d.source_a,
                source_b=d.source_b,
                score_a=d.score_a,
                score_b=d.score_b,
                divergence=d.divergence,
            )
            for d in divergences
        ]
    )


@router.get("/predictive", response_model=PredictiveResponse)
async def get_predictive_signals(db: AsyncSession = Depends(get_db)):
    """Get predictive sentiment-price signals."""
    result = await db.execute(
        select(PredictiveSignal, Company)
        .join(Company, PredictiveSignal.company_id == Company.id)
        .order_by(PredictiveSignal.generated_at.desc())
        .limit(50)
    )
    rows = result.all()

    signals = [
        PredictiveSignalItem(
            id=str(sig.id),
            symbol=comp.symbol,
            signal_type=sig.signal_type,
            direction=sig.direction,
            strength=sig.strength,
            correlation=sig.correlation,
            lag_hours=sig.lag_hours,
            description=sig.description,
            generated_at=sig.generated_at,
        )
        for sig, comp in rows
    ]

    return PredictiveResponse(signals=signals)

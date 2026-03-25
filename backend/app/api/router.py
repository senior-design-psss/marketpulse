from fastapi import APIRouter

from app.api.analyst import router as analyst_router
from app.api.analytics import router as analytics_router
from app.api.companies import router as companies_router
from app.api.graph import router as graph_router
from app.api.industries import router as industries_router
from app.api.sentiment import router as sentiment_router
from app.config import settings

router = APIRouter(prefix="/api/v1")

# Core data routers
router.include_router(industries_router)
router.include_router(companies_router)
router.include_router(sentiment_router)
router.include_router(analytics_router)
router.include_router(analyst_router)
router.include_router(graph_router)


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "marketpulse-backend"}


# Debug endpoints (only in development)
if settings.environment == "development":
    from app.analyst.briefing_generator import generate_daily_briefing
    from app.analytics.aggregator import compute_aggregates
    from app.analytics.anomaly_detector import detect_anomalies
    from app.analytics.confidence import compute_confidence
    from app.analytics.momentum import compute_momentum
    from app.analytics.predictive import compute_predictive_signals
    from app.ingestion.service import run_all_collectors, run_collector
    from app.market.price_fetcher import fetch_prices
    from app.processing.pipeline import process_batch

    @router.post("/debug/ingest/{source}")
    async def debug_ingest_source(source: str):
        """Manually trigger ingestion for a single source."""
        count = await run_collector(source)
        return {"source": source, "new_items": count}

    @router.post("/debug/ingest")
    async def debug_ingest_all():
        """Manually trigger ingestion for all sources."""
        results = await run_all_collectors()
        return {"results": results}

    @router.post("/debug/process")
    async def debug_process(batch_size: int = 50):
        """Manually trigger the sentiment processing pipeline."""
        count = await process_batch(batch_size=batch_size)
        return {"processed": count}

    @router.post("/debug/analytics")
    async def debug_analytics():
        """Run the full analytics pipeline: aggregate -> momentum -> confidence -> anomalies."""
        h = await compute_aggregates("hourly")
        d = await compute_aggregates("daily")
        m = await compute_momentum()
        c = await compute_confidence()
        a = await detect_anomalies()
        return {
            "hourly_aggregates": h,
            "daily_aggregates": d,
            "momentum_updated": m,
            "confidence_updated": c,
            "anomalies_created": a,
        }

    @router.post("/debug/prices")
    async def debug_fetch_prices():
        """Fetch latest stock prices from yfinance."""
        count = await fetch_prices(days=30)
        return {"price_records": count}

    @router.post("/debug/briefing")
    async def debug_generate_briefing():
        """Generate an AI market briefing."""
        bid = await generate_daily_briefing()
        return {"briefing_id": bid}

    @router.post("/debug/predictive")
    async def debug_predictive():
        """Compute predictive sentiment-price signals."""
        count = await compute_predictive_signals()
        return {"signals_created": count}

    @router.get("/debug/status")
    async def debug_status():
        """Get system status: table counts."""
        from sqlalchemy import func, select

        from app.core.database import get_session_factory
        from app.models.ai_briefing import AIBriefing
        from app.models.anomaly_alert import AnomalyAlert
        from app.models.entity_mention import EntityMention
        from app.models.raw_content import RawContent
        from app.models.sentiment_aggregate import SentimentAggregate
        from app.models.sentiment_score import SentimentScore

        async with get_session_factory()() as session:
            counts = {}
            for name, model in [
                ("raw_content", RawContent),
                ("processed", RawContent),
                ("sentiment_scores", SentimentScore),
                ("entity_mentions", EntityMention),
                ("aggregates", SentimentAggregate),
                ("anomaly_alerts", AnomalyAlert),
                ("ai_briefings", AIBriefing),
            ]:
                if name == "processed":
                    r = await session.execute(
                        select(func.count(RawContent.id)).where(RawContent.is_processed == True)  # noqa: E712
                    )
                else:
                    r = await session.execute(select(func.count(model.id)))
                counts[name] = r.scalar() or 0
            counts["unprocessed"] = counts["raw_content"] - counts["processed"]
        return counts

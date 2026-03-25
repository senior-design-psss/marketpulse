"""APScheduler configuration for periodic ingestion jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.analyst.briefing_generator import generate_daily_briefing
from app.analytics.aggregator import compute_aggregates
from app.analytics.anomaly_detector import detect_anomalies
from app.analytics.confidence import compute_confidence
from app.analytics.momentum import compute_momentum
from app.analytics.predictive import compute_predictive_signals
from app.graph.entity_graph import compute_entity_graph
from app.ingestion.service import run_collector
from app.market.price_fetcher import fetch_prices
from app.processing.pipeline import process_batch

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_analytics():
    """Run the full analytics pipeline: aggregate → momentum → confidence → anomalies."""
    await compute_aggregates("hourly")
    await compute_momentum()
    await compute_confidence()
    await detect_anomalies()


def setup_scheduler():
    """Configure and start all scheduled jobs."""

    # === Ingestion ===
    scheduler.add_job(
        run_collector, trigger=IntervalTrigger(minutes=15),
        args=["reddit"], id="ingest_reddit", name="Reddit Ingestion",
        replace_existing=True, max_instances=1,
    )
    scheduler.add_job(
        run_collector, trigger=IntervalTrigger(minutes=10),
        args=["news"], id="ingest_news", name="News RSS Ingestion",
        replace_existing=True, max_instances=1,
    )
    scheduler.add_job(
        run_collector, trigger=IntervalTrigger(minutes=10),
        args=["stocktwits"], id="ingest_stocktwits", name="StockTwits Ingestion",
        replace_existing=True, max_instances=1,
    )

    # === Processing ===
    scheduler.add_job(
        process_batch, trigger=IntervalTrigger(minutes=5),
        kwargs={"batch_size": 50}, id="process_pipeline",
        name="Sentiment Processing", replace_existing=True, max_instances=1,
    )

    # === Analytics (every 15 min, after enough data accumulates) ===
    scheduler.add_job(
        run_analytics, trigger=IntervalTrigger(minutes=15),
        id="analytics_pipeline", name="Analytics Pipeline",
        replace_existing=True, max_instances=1,
    )

    # === Daily aggregates (every 6 hours) ===
    scheduler.add_job(
        compute_aggregates, trigger=IntervalTrigger(hours=6),
        args=["daily"], id="daily_aggregates", name="Daily Aggregates",
        replace_existing=True, max_instances=1,
    )

    # === Price data (every 12 hours) ===
    scheduler.add_job(
        fetch_prices, trigger=IntervalTrigger(hours=12),
        kwargs={"days": 30}, id="price_fetcher", name="Price Data Fetch",
        replace_existing=True, max_instances=1,
    )

    # === AI Briefing (every 6 hours) ===
    scheduler.add_job(
        generate_daily_briefing, trigger=IntervalTrigger(hours=6),
        id="ai_briefing", name="AI Market Briefing",
        replace_existing=True, max_instances=1,
    )

    # === Entity Graph (daily) ===
    scheduler.add_job(
        compute_entity_graph, trigger=IntervalTrigger(hours=24),
        id="entity_graph", name="Entity Graph Computation",
        replace_existing=True, max_instances=1,
    )

    # === Predictive Signals (weekly / every 24h) ===
    scheduler.add_job(
        compute_predictive_signals, trigger=IntervalTrigger(hours=24),
        id="predictive_signals", name="Predictive Signal Computation",
        replace_existing=True, max_instances=1,
    )

    scheduler.start()
    logger.info("Scheduler started: 11 jobs (3 ingestion, 1 processing, 7 analytics)")


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Ingestion scheduler stopped")

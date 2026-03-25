"""Generate per-company AI summaries using Claude Haiku."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.analyst.prompts import COMPANY_SUMMARY_PROMPT
from app.core.database import get_session_factory
from app.models.ai_briefing import AIBriefing
from app.models.company import Company
from app.models.raw_content import RawContent
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)


def _get_client():
    try:
        import anthropic

        from app.config import settings

        if not settings.anthropic_api_key:
            return None
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except ImportError:
        return None


async def generate_company_summary(symbol: str) -> str | None:
    """Generate an AI summary for a specific company. Returns briefing ID."""
    async with get_session_factory()() as session:
        comp = (await session.execute(
            select(Company).where(func.upper(Company.symbol) == symbol.upper())
        )).scalar_one_or_none()
        if not comp:
            return None

        since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Get latest aggregate
        agg = (await session.execute(
            select(SentimentAggregate)
            .where(SentimentAggregate.company_id == comp.id, SentimentAggregate.period_type == "hourly")
            .order_by(SentimentAggregate.period_start.desc()).limit(1)
        )).scalar_one_or_none()

        # Get sample headlines
        headlines_result = await session.execute(
            select(RawContent.title, SentimentScore.ensemble_score)
            .join(SentimentScore, SentimentScore.raw_content_id == RawContent.id)
            .where(SentimentScore.company_id == comp.id, SentimentScore.scored_at >= since)
            .order_by(SentimentScore.scored_at.desc())
            .limit(10)
        )
        headlines = headlines_result.all()
        headline_text = "\n".join(
            [f"- [{h.ensemble_score:+.2f}] {h.title}" for h in headlines if h.title]
        ) or "- No recent headlines"

        # Format source averages
        def fmt(val):
            return f"{val:+.3f}" if val is not None else "N/A"

        prompt_data = {
            "symbol": comp.symbol,
            "company_name": comp.name,
            "avg_score": agg.avg_score if agg else 0.0,
            "label": "bullish" if (agg and agg.avg_score and agg.avg_score > 0.1) else (
                "bearish" if (agg and agg.avg_score and agg.avg_score < -0.1) else "neutral"
            ),
            "confidence": agg.confidence if agg and agg.confidence else 0.0,
            "volume": agg.volume if agg else 0,
            "momentum": fmt(agg.momentum) if agg else "N/A",
            "reddit_avg": fmt(agg.reddit_avg) if agg else "N/A",
            "reddit_vol": agg.reddit_volume if agg else 0,
            "news_avg": fmt(agg.news_avg) if agg else "N/A",
            "news_vol": agg.news_volume if agg else 0,
            "stocktwits_avg": fmt(agg.stocktwits_avg) if agg else "N/A",
            "stocktwits_vol": agg.stocktwits_volume if agg else 0,
            "sample_headlines": headline_text,
        }

        client = _get_client()
        if client:
            try:
                message = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=500,
                    messages=[{"role": "user", "content": COMPANY_SUMMARY_PROMPT.format(**prompt_data)}],
                )
                content = message.content[0].text
            except Exception as e:
                logger.error(f"Company summary LLM failed for {symbol}: {e}")
                content = f"**{comp.name} ({comp.symbol})** — Sentiment score: {prompt_data['avg_score']:+.3f} ({prompt_data['label']}). {prompt_data['volume']} mentions in last 24h."
        else:
            content = f"**{comp.name} ({comp.symbol})** — Sentiment score: {prompt_data['avg_score']:+.3f} ({prompt_data['label']}). {prompt_data['volume']} mentions across {prompt_data['reddit_vol']} Reddit, {prompt_data['news_vol']} News, {prompt_data['stocktwits_vol']} StockTwits posts."

        briefing = AIBriefing(
            briefing_type="company_deep_dive",
            company_id=comp.id,
            title=f"{comp.symbol} Summary — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            content=content,
            data_window_start=since,
            data_window_end=datetime.now(timezone.utc),
            items_analyzed=agg.volume if agg else 0,
        )
        session.add(briefing)
        await session.commit()

        return str(briefing.id)

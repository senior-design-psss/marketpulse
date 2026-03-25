"""Generate AI market briefings using Claude Haiku."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyst.prompts import DAILY_BRIEFING_PROMPT
from app.core.database import get_session_factory
from app.models.ai_briefing import AIBriefing
from app.models.anomaly_alert import AnomalyAlert
from app.models.company import Company
from app.models.industry import Industry
from app.models.sentiment_aggregate import SentimentAggregate
from app.models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)


def _get_anthropic_client():
    try:
        import anthropic

        from app.config import settings

        if not settings.anthropic_api_key:
            return None
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except ImportError:
        return None


async def _gather_briefing_data(session: AsyncSession) -> dict:
    """Gather all data needed for a market briefing."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=24)

    # Overall score
    overall = await session.execute(
        select(func.avg(SentimentScore.ensemble_score)).where(
            SentimentScore.scored_at >= window_start
        )
    )
    overall_score = float(overall.scalar() or 0)
    overall_label = "bullish" if overall_score > 0.1 else ("bearish" if overall_score < -0.1 else "neutral")

    items_count = await session.execute(
        select(func.count(SentimentScore.id)).where(SentimentScore.scored_at >= window_start)
    )
    items_analyzed = items_count.scalar() or 0

    # Industry breakdown
    industries = (await session.execute(select(Industry).order_by(Industry.name))).scalars().all()
    industry_lines = []
    for ind in industries:
        agg = await session.execute(
            select(SentimentAggregate)
            .where(SentimentAggregate.industry_id == ind.id, SentimentAggregate.period_type == "daily")
            .order_by(SentimentAggregate.period_start.desc()).limit(1)
        )
        a = agg.scalar_one_or_none()
        if a:
            industry_lines.append(f"- {ind.name}: {a.avg_score:+.3f} ({a.volume} items)")
        else:
            industry_lines.append(f"- {ind.name}: No data")

    # Top bullish/bearish companies
    company_scores = await session.execute(
        select(Company.symbol, Company.name, func.avg(SentimentScore.ensemble_score).label("avg"))
        .join(SentimentScore, SentimentScore.company_id == Company.id)
        .where(SentimentScore.scored_at >= window_start)
        .group_by(Company.id)
        .order_by(func.avg(SentimentScore.ensemble_score).desc())
    )
    all_scores = company_scores.all()
    bullish = [f"- {r.symbol} ({r.name}): {float(r.avg):+.3f}" for r in all_scores[:5]]
    bearish = [f"- {r.symbol} ({r.name}): {float(r.avg):+.3f}" for r in all_scores[-5:]]

    # Active anomalies
    anomalies_result = await session.execute(
        select(AnomalyAlert).where(AnomalyAlert.is_active == True).order_by(AnomalyAlert.triggered_at.desc())  # noqa
    )
    anomalies = anomalies_result.scalars().all()
    anomaly_lines = [f"- [{a.severity.upper()}] {a.title}" for a in anomalies] or ["- None"]

    return {
        "window_start": window_start.strftime("%Y-%m-%d %H:%M UTC"),
        "window_end": now.strftime("%Y-%m-%d %H:%M UTC"),
        "items_analyzed": items_analyzed,
        "overall_score": overall_score,
        "overall_label": overall_label,
        "industry_breakdown": "\n".join(industry_lines),
        "top_bullish": "\n".join(bullish) or "- No data",
        "top_bearish": "\n".join(bearish) or "- No data",
        "anomalies": "\n".join(anomaly_lines),
    }


async def generate_daily_briefing() -> str | None:
    """Generate and store a daily market briefing. Returns the briefing ID or None."""
    client = _get_anthropic_client()

    async with get_session_factory()() as session:
        data = await _gather_briefing_data(session)

        prompt = DAILY_BRIEFING_PROMPT.format(**data)

        if client:
            try:
                message = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = message.content[0].text
            except Exception as e:
                logger.error(f"LLM briefing generation failed: {e}")
                content = _generate_fallback_briefing(data)
        else:
            logger.info("No Anthropic client, using fallback briefing")
            content = _generate_fallback_briefing(data)

        briefing = AIBriefing(
            briefing_type="daily_market",
            title=f"Market Briefing — {data['window_end'][:10]}",
            content=content,
            key_insights={"overall_score": data["overall_score"], "items": data["items_analyzed"]},
            data_window_start=datetime.now(timezone.utc) - timedelta(hours=24),
            data_window_end=datetime.now(timezone.utc),
            items_analyzed=data["items_analyzed"],
        )
        session.add(briefing)
        await session.commit()

        logger.info(f"Generated daily briefing: {briefing.title}")
        return str(briefing.id)


def _generate_fallback_briefing(data: dict) -> str:
    """Generate a rule-based briefing when LLM is unavailable."""
    score = data["overall_score"]
    label = data["overall_label"]
    items = data["items_analyzed"]

    return f"""## Market Overview

The overall market sentiment is **{label}** with a composite score of **{score:+.3f}** based on {items} analyzed items in the last 24 hours.

## Sector Highlights

{data["industry_breakdown"]}

## Companies to Watch

**Most Bullish:**
{data["top_bullish"]}

**Most Bearish:**
{data["top_bearish"]}

## Risk Factors

{data["anomalies"]}

## Outlook

Sentiment data continues to be collected and analyzed. Monitor momentum indicators for emerging trends.

---
*Generated by MarketPulse AI Analytics Engine*"""

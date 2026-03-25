"""AI-enriched risk alert descriptions."""

import logging

from sqlalchemy import select

from app.analyst.prompts import RISK_ALERT_PROMPT
from app.core.database import get_session_factory
from app.models.anomaly_alert import AnomalyAlert
from app.models.company import Company
from app.models.raw_content import RawContent
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


async def enrich_alert(alert_id: str) -> bool:
    """Enrich an anomaly alert with AI-generated context. Returns True on success."""
    async with get_session_factory()() as session:
        alert = (await session.execute(
            select(AnomalyAlert).where(AnomalyAlert.id == alert_id)
        )).scalar_one_or_none()
        if not alert or not alert.company_id:
            return False

        company = (await session.execute(
            select(Company).where(Company.id == alert.company_id)
        )).scalar_one_or_none()
        if not company:
            return False

        # Get recent sentiment items
        recent = await session.execute(
            select(RawContent.title, SentimentScore.ensemble_score)
            .join(SentimentScore, SentimentScore.raw_content_id == RawContent.id)
            .where(SentimentScore.company_id == company.id)
            .order_by(SentimentScore.scored_at.desc())
            .limit(5)
        )
        items = recent.all()
        items_text = "\n".join(
            [f"- [{i.ensemble_score:+.2f}] {i.title}" for i in items if i.title]
        ) or "- No recent items"

        client = _get_client()
        if not client:
            return False

        try:
            prompt_data = {
                "symbol": company.symbol,
                "company_name": company.name,
                "title": alert.title,
                "severity": alert.severity,
                "metric_value": alert.metric_value or 0.0,
                "baseline_value": alert.baseline_value or 0.0,
                "z_score": alert.z_score or 0.0,
                "recent_items": items_text,
            }
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": RISK_ALERT_PROMPT.format(**prompt_data)}],
            )
            alert.description = message.content[0].text
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Risk alert enrichment failed: {e}")
            return False

"""Entity relationship graph — co-occurrence and sentiment correlation between companies."""

import logging
from datetime import datetime, timedelta, timezone
from itertools import combinations

from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.models.entity_mention import EntityMention
from app.models.entity_relation import EntityRelation
from app.models.sentiment_score import SentimentScore

logger = logging.getLogger(__name__)

MIN_CO_OCCURRENCES = 2


async def compute_entity_graph(period_type: str = "daily") -> int:
    """
    Compute co-occurrence counts and sentiment correlation between company pairs.
    A co-occurrence = two companies mentioned in the same raw_content item.

    Returns number of relations upserted.
    """
    now = datetime.now(timezone.utc)

    if period_type == "daily":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    else:
        period_start = now - timedelta(weeks=1)

    count = 0

    async with get_session_factory()() as session:
        # Find all raw_content_ids that have 2+ entity mentions
        multi_mention = await session.execute(
            select(EntityMention.raw_content_id)
            .group_by(EntityMention.raw_content_id)
            .having(func.count(EntityMention.company_id.distinct()) >= 2)
        )
        content_ids = [r[0] for r in multi_mention.all()]

        if not content_ids:
            logger.info("No co-mentions found for entity graph")
            return 0

        # For each content with multiple mentions, get the company pairs
        pair_counts: dict[tuple, int] = {}
        for content_id in content_ids:
            mentions = await session.execute(
                select(EntityMention.company_id).where(
                    EntityMention.raw_content_id == content_id
                )
            )
            company_ids = sorted([str(r[0]) for r in mentions.all()])

            for a, b in combinations(company_ids, 2):
                key = (min(a, b), max(a, b))
                pair_counts[key] = pair_counts.get(key, 0) + 1

        # Compute sentiment correlation for significant pairs

        for (a_id, b_id), co_count in pair_counts.items():
            if co_count < MIN_CO_OCCURRENCES:
                continue

            # Get sentiment scores for both companies
            a_scores = await session.execute(
                select(SentimentScore.ensemble_score).where(
                    SentimentScore.company_id == a_id,
                    SentimentScore.scored_at >= period_start,
                )
            )
            b_scores = await session.execute(
                select(SentimentScore.ensemble_score).where(
                    SentimentScore.company_id == b_id,
                    SentimentScore.scored_at >= period_start,
                )
            )

            a_vals = [r[0] for r in a_scores.all()]
            b_vals = [r[0] for r in b_scores.all()]

            correlation = None
            if len(a_vals) >= 3 and len(b_vals) >= 3:
                # Simple correlation using overlapping means
                min_len = min(len(a_vals), len(b_vals))
                pairs = list(zip(a_vals[:min_len], b_vals[:min_len]))
                correlation = _pearson(pairs)

            # Upsert entity relation
            # Ensure canonical ordering (a < b)
            id_a, id_b = (a_id, b_id) if a_id < b_id else (b_id, a_id)

            existing = await session.execute(
                select(EntityRelation).where(
                    EntityRelation.company_a_id == id_a,
                    EntityRelation.company_b_id == id_b,
                    EntityRelation.period_type == period_type,
                    EntityRelation.period_start == period_start,
                )
            )
            rel = existing.scalar_one_or_none()

            if rel:
                rel.co_occurrence_count = co_count
                rel.sentiment_correlation = correlation
            else:
                rel = EntityRelation(
                    company_a_id=id_a,
                    company_b_id=id_b,
                    co_occurrence_count=co_count,
                    sentiment_correlation=correlation,
                    period_type=period_type,
                    period_start=period_start,
                )
                session.add(rel)
            count += 1

        await session.commit()

    logger.info(f"Computed {count} entity relations ({period_type})")
    return count


def _pearson(pairs: list[tuple[float, float]]) -> float | None:
    n = len(pairs)
    if n < 3:
        return None
    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((xi - mx) * (yi - my) for xi, yi in pairs) / n
    sx = (sum((xi - mx) ** 2 for xi in x) / n) ** 0.5
    sy = (sum((yi - my) ** 2 for yi in y) / n) ** 0.5
    if sx == 0 or sy == 0:
        return None
    return round(cov / (sx * sy), 4)

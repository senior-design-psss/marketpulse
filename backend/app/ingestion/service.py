"""Ingestion service — orchestrates collection, dedup, and storage."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.ingestion.base import BaseCollector, RawContentItem
from app.ingestion.news_collector import NewsCollector
from app.ingestion.reddit_collector import RedditCollector
from app.ingestion.stocktwits_collector import StockTwitsCollector
from app.models.raw_content import RawContent
from app.processing.deduplicator import deduplicate_by_source_id, filter_duplicates
from app.processing.text_cleaner import clean_text

logger = logging.getLogger(__name__)

# Collector instances (reused across runs)
_collectors: dict[str, BaseCollector] = {}


def get_collectors() -> dict[str, BaseCollector]:
    global _collectors
    if not _collectors:
        _collectors = {
            "reddit": RedditCollector(),
            "news": NewsCollector(),
            "stocktwits": StockTwitsCollector(),
        }
    return _collectors


async def _store_items(session: AsyncSession, items: list[RawContentItem]) -> int:
    """Deduplicate and store raw content items. Returns count of new items inserted."""
    if not items:
        return 0

    # Dedup by content hash
    hashes = [item.content_hash for item in items]
    existing_hashes = await filter_duplicates(session, hashes)

    # Dedup by source_id within each source
    source_groups: dict[str, list[str]] = {}
    for item in items:
        if item.source_id:
            source_groups.setdefault(item.source, []).append(item.source_id)

    existing_source_ids: set[str] = set()
    for source, source_ids in source_groups.items():
        existing_source_ids |= await deduplicate_by_source_id(session, source, source_ids)

    # Filter out duplicates
    new_items = [
        item
        for item in items
        if item.content_hash not in existing_hashes
        and (item.source_id is None or item.source_id not in existing_source_ids)
    ]

    if not new_items:
        return 0

    # Insert new items
    for item in new_items:
        record = RawContent(
            source=item.source,
            source_id=item.source_id,
            title=item.title,
            body=clean_text(item.body),
            url=item.url,
            author=item.author,
            subreddit=item.subreddit,
            published_at=item.published_at,
            content_hash=item.content_hash,
            is_processed=False,
        )
        session.add(record)

    await session.flush()
    return len(new_items)


async def run_collector(source_name: str) -> int:
    """Run a single collector and store results. Returns count of new items."""
    collectors = get_collectors()
    collector = collectors.get(source_name)
    if not collector:
        logger.error(f"Unknown collector: {source_name}")
        return 0

    items = await collector.run()

    async with get_session_factory()() as session:
        try:
            count = await _store_items(session, items)
            await session.commit()
            logger.info(f"[{source_name}] Stored {count} new items (fetched {len(items)})")
            return count
        except Exception as e:
            await session.rollback()
            logger.error(f"[{source_name}] Storage failed: {e}")
            return 0


async def run_all_collectors() -> dict[str, int]:
    """Run all collectors and return counts per source."""
    results = {}
    for name in get_collectors():
        results[name] = await run_collector(name)
    return results

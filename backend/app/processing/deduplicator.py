"""Content deduplication using SHA-256 hashing."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_content import RawContent

logger = logging.getLogger(__name__)


async def filter_duplicates(
    session: AsyncSession,
    content_hashes: list[str],
) -> set[str]:
    """Return the set of content_hashes that already exist in the database."""
    if not content_hashes:
        return set()

    result = await session.execute(
        select(RawContent.content_hash).where(
            RawContent.content_hash.in_(content_hashes)
        )
    )
    return {row[0] for row in result.all()}


async def deduplicate_by_source_id(
    session: AsyncSession,
    source: str,
    source_ids: list[str],
) -> set[str]:
    """Return the set of source_ids that already exist for the given source."""
    if not source_ids:
        return set()

    result = await session.execute(
        select(RawContent.source_id).where(
            RawContent.source == source,
            RawContent.source_id.in_(source_ids),
        )
    )
    return {row[0] for row in result.all()}

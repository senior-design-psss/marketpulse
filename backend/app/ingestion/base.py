"""Abstract base class for all data collectors."""

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RawContentItem(BaseModel):
    """Schema for a collected content item before DB insertion."""

    source: str  # reddit, news, stocktwits
    source_id: str | None = None
    title: str | None = None
    body: str
    url: str | None = None
    author: str | None = None
    subreddit: str | None = None
    published_at: datetime

    @property
    def content_hash(self) -> str:
        normalized = self.body.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class BaseCollector(ABC):
    """Abstract base for all ingestion collectors."""

    source_name: str = ""

    @abstractmethod
    async def collect(self) -> list[RawContentItem]:
        """Fetch new content items from the source. Returns a list of raw items."""
        ...

    async def run(self) -> list[RawContentItem]:
        """Execute collection with error handling."""
        try:
            items = await self.collect()
            logger.info(f"[{self.source_name}] Collected {len(items)} items")
            return items
        except Exception as e:
            logger.error(f"[{self.source_name}] Collection failed: {e}")
            return []

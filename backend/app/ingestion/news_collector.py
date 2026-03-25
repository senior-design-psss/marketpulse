"""News RSS feed collector using feedparser."""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.ingestion.base import BaseCollector, RawContentItem

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    # CNBC
    ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147", "CNBC Finance"),
    ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910", "CNBC Tech"),
    ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839135", "CNBC Economy"),
    # MarketWatch
    ("https://feeds.marketwatch.com/marketwatch/topstories/", "MarketWatch"),
    ("https://feeds.marketwatch.com/marketwatch/marketpulse/", "MarketWatch Pulse"),
    # Seeking Alpha
    ("https://seekingalpha.com/market_currents.xml", "Seeking Alpha Currents"),
    # Google News - Business
    ("https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB", "Google News Business"),
    # Nasdaq
    ("https://www.nasdaq.com/feed/rssoutbound?category=Markets", "Nasdaq Markets"),
    # Bloomberg
    ("https://feeds.bloomberg.com/markets/news.rss", "Bloomberg Markets"),
    ("https://feeds.bloomberg.com/technology/news.rss", "Bloomberg Tech"),
    # Wall Street Journal
    ("https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "WSJ Markets"),
    ("https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml", "WSJ Business"),
    # Barron's
    ("https://feeds.barrons.com/barrons/articles", "Barrons"),
    # Investor's Business Daily
    ("https://www.investors.com/feed/", "IBD"),
    # Financial Times (free summaries)
    ("https://www.ft.com/rss/home", "Financial Times"),
]


def _parse_pub_date(entry: dict) -> datetime:
    """Try to extract a published date from an RSS entry."""
    for field in ("published", "updated", "created"):
        val = entry.get(field)
        if val:
            try:
                return parsedate_to_datetime(val).astimezone(timezone.utc)
            except Exception:
                pass

    # Fallback: use struct_time fields
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                from calendar import timegm
                return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc)
            except Exception:
                pass

    return datetime.now(timezone.utc)


class NewsCollector(BaseCollector):
    source_name = "news"

    async def collect(self) -> list[RawContentItem]:
        items: list[RawContentItem] = []

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for feed_url, feed_name in RSS_FEEDS:
                try:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)

                    for entry in feed.entries[:15]:
                        title = entry.get("title", "").strip()
                        summary = entry.get("summary", "").strip()
                        body = f"{title}\n\n{summary}" if summary else title

                        if len(body.strip()) < 30:
                            continue

                        items.append(
                            RawContentItem(
                                source="news",
                                source_id=entry.get("id") or entry.get("link"),
                                title=title,
                                body=body,
                                url=entry.get("link"),
                                author=entry.get("author"),
                                published_at=_parse_pub_date(entry),
                            )
                        )
                except Exception as e:
                    logger.error(f"[news] Error fetching {feed_name} ({feed_url}): {e}")
                    continue

        return items

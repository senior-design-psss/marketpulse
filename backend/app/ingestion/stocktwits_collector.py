"""StockTwits collector — free, no API key, pre-labeled bullish/bearish sentiment."""

import asyncio
import json
import logging
import re
import subprocess
from datetime import datetime, timezone

from app.ingestion.base import BaseCollector, RawContentItem

logger = logging.getLogger(__name__)

SYMBOLS = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META",
    "JPM", "GS", "BAC", "XOM", "JNJ", "WMT", "BA", "NFLX",
    "BTC.X", "ETH.X", "COIN", "DIS", "PFE",
]

API_BASE = "https://api.stocktwits.com/api/2"

# Regex to count cashtags
CASHTAG_RE = re.compile(r"\$[A-Za-z]{1,6}(?:\.X)?")

# Minimum ratio of non-cashtag text to total text
MIN_CONTENT_RATIO = 0.3


def _is_quality_message(body: str) -> bool:
    """Filter out low-quality StockTwits messages."""
    # Strip sentiment tags for analysis
    clean = re.sub(r"^\[(BULLISH|BEARISH)\]\s*", "", body)

    # Too short after stripping tags
    if len(clean.strip()) < 20:
        return False

    # Count cashtags vs actual content
    cashtags = CASHTAG_RE.findall(clean)
    text_without_tags = CASHTAG_RE.sub("", clean).strip()

    # If it's mostly cashtags and no real text, skip
    if len(text_without_tags) < 15:
        return False

    # If more than 5 cashtags and very little text, it's spam
    if len(cashtags) > 5 and len(text_without_tags) < 30:
        return False

    return True


def _fetch_symbol(symbol: str) -> dict | None:
    """Fetch StockTwits data using curl (bypasses Cloudflare TLS fingerprinting)."""
    try:
        url = f"{API_BASE}/streams/symbol/{symbol}.json"
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0 or not result.stdout:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


class StockTwitsCollector(BaseCollector):
    source_name = "stocktwits"

    async def collect(self) -> list[RawContentItem]:
        items: list[RawContentItem] = []
        seen_ids: set[str] = set()  # Deduplicate across symbols
        loop = asyncio.get_event_loop()

        for symbol in SYMBOLS:
            try:
                data = await loop.run_in_executor(None, _fetch_symbol, symbol)
                if data is None or "errors" in data:
                    continue

                messages = data.get("messages", [])

                for msg in messages:
                    msg_id = str(msg.get("id", ""))

                    # Skip if we already saw this message from another symbol's feed
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)

                    body = msg.get("body", "").strip()

                    # Quality filter
                    if not _is_quality_message(body):
                        continue

                    # Extract user sentiment label
                    user_sentiment = ""
                    entities = msg.get("entities") or {}
                    sentiment_data = entities.get("sentiment") or {}
                    if sentiment_data:
                        user_sentiment = sentiment_data.get("basic", "") or ""

                    if user_sentiment:
                        body = f"[{user_sentiment.upper()}] {body}"

                    created_at = msg.get("created_at", "")
                    try:
                        pub_date = datetime.strptime(
                            created_at, "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        pub_date = datetime.now(timezone.utc)

                    clean_symbol = symbol.replace(".X", "")

                    items.append(
                        RawContentItem(
                            source="stocktwits",
                            source_id=msg_id,
                            title=f"${clean_symbol}: {body[:80]}",
                            body=body,
                            url=f"https://stocktwits.com/message/{msg_id}",
                            author=msg.get("user", {}).get("username"),
                            published_at=pub_date,
                        )
                    )

            except Exception as e:
                logger.error(f"[stocktwits] Error fetching {symbol}: {e}")
                continue

        return items

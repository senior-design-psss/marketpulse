"""Reddit data collector using public JSON endpoints (no API key required)."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.ingestion.base import BaseCollector, RawContentItem

logger = logging.getLogger(__name__)

SUBREDDITS = [
    "wallstreetbets",
    "stocks",
    "investing",
    "stockmarket",
    "cryptocurrency",
    "options",
]

POSTS_PER_SUB = 15
USER_AGENT = "MarketPulseAI/1.0 (student research project)"


class RedditCollector(BaseCollector):
    source_name = "reddit"

    async def collect(self) -> list[RawContentItem]:
        items: list[RawContentItem] = []

        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            for sub_name in SUBREDDITS:
                try:
                    # Public JSON endpoint — no auth needed
                    url = f"https://www.reddit.com/r/{sub_name}/hot.json?limit={POSTS_PER_SUB}"
                    resp = await client.get(url)

                    if resp.status_code == 429:
                        logger.warning(f"[reddit] Rate limited on r/{sub_name}, waiting 10s")
                        await asyncio.sleep(10)
                        resp = await client.get(url)

                    resp.raise_for_status()
                    data = resp.json()

                    posts = data.get("data", {}).get("children", [])
                    for post_wrapper in posts:
                        post = post_wrapper.get("data", {})

                        # Skip pinned/stickied
                        if post.get("stickied"):
                            continue

                        title = post.get("title", "").strip()
                        selftext = post.get("selftext", "").strip()
                        body = f"{title}\n\n{selftext}" if selftext else title

                        if len(body.strip()) < 20:
                            continue

                        created_utc = post.get("created_utc", 0)

                        items.append(
                            RawContentItem(
                                source="reddit",
                                source_id=post.get("id"),
                                title=title,
                                body=body,
                                url=f"https://reddit.com{post.get('permalink', '')}",
                                author=post.get("author"),
                                subreddit=sub_name,
                                published_at=datetime.fromtimestamp(
                                    created_utc, tz=timezone.utc
                                ),
                            )
                        )

                except Exception as e:
                    logger.error(f"[reddit] Error fetching r/{sub_name}: {e}")
                    continue

                # Rate limit: ~2 seconds between subreddits to stay under 10 QPM
                await asyncio.sleep(2)

        return items

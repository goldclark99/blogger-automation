from __future__ import annotations

from datetime import datetime, timezone

import feedparser

from .models import ResearchPacket


TREND_RSS = "https://trends.google.com/trending/rss?geo={geo}"


def fetch_google_trends(geo: str, limit: int = 20) -> list[dict]:
    feed = feedparser.parse(TREND_RSS.format(geo=geo))
    items: list[dict] = []
    for entry in feed.entries[:limit]:
        items.append(
            {
                "title": entry.get("title", ""),
                "published": entry.get("published", ""),
                "traffic": entry.get("ht_approx_traffic", ""),
            }
        )
    return items


def build_packet(blog_key: str, existing_posts: list[dict]) -> ResearchPacket:
    geo = "US" if blog_key == "english" else "TH"
    compact_posts = [
        {
            "id": post.get("id"),
            "status": post.get("status"),
            "title": post.get("title"),
            "labels": post.get("labels", []),
            "published": post.get("published"),
            "url": post.get("url"),
        }
        for post in existing_posts
    ]
    return ResearchPacket(
        blog_key=blog_key,
        trend_items=fetch_google_trends(geo),
        existing_posts=compact_posts,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


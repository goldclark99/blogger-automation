from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse

from openai import OpenAI

from .models import Article, ResearchPacket


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_SOURCE_HOSTS = {
    "facebook.com",
    "instagram.com",
    "moneytoday.co.kr",
    "reddit.com",
    "tiktok.com",
    "x.com",
    "youtube.com",
}


def _json_from_text(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _article_schema() -> str:
    return json.dumps(Article.model_json_schema(), ensure_ascii=False)


def generate_article(*, cfg: dict, blog_cfg: dict, packet: ResearchPacket) -> Article:
    master = (ROOT / "prompts" / "master.md").read_text(encoding="utf-8")
    prompt = f"""
{master}

PUBLICATION CONFIGURATION:
{json.dumps(blog_cfg, ensure_ascii=False, indent=2)}

CURRENT SEARCH-DEMAND AND DUPLICATION PACKET:
{packet.model_dump_json(indent=2)}

TODAY'S OUTPUT SCHEMA:
{_article_schema()}

Use web search to verify the topic against current primary sources. Select one topic that passes every gate.
The HTML must begin with the subtitle and 30-second summary; do not include an H1 because Blogger supplies the title.
"""
    response = OpenAI().responses.create(
        model=cfg["text_model"],
        reasoning={"effort": "medium"},
        tools=[{"type": "web_search"}],
        input=prompt,
    )
    article = Article.model_validate(_json_from_text(response.output_text))
    validate_article(
        article,
        blog_cfg,
        packet,
        duplicate_threshold=float(cfg["duplicate_title_threshold"]),
        minimum_sources=int(cfg["minimum_official_sources"]),
    )
    return article


def validate_article(
    article: Article,
    blog_cfg: dict,
    packet: ResearchPacket,
    *,
    duplicate_threshold: float,
    minimum_sources: int,
) -> None:
    if article.category not in blog_cfg["categories"]:
        raise ValueError(f"Invalid category: {article.category}")
    if article.category not in article.labels:
        raise ValueError("Primary category must also be a Blogger label")

    old_titles = [post.get("title", "") for post in packet.existing_posts]
    for old_title in old_titles:
        similarity = SequenceMatcher(None, article.title.casefold(), old_title.casefold()).ratio()
        if similarity >= duplicate_threshold:
            raise ValueError(f"Duplicate-risk title ({similarity:.2f}): {old_title}")

    if len(article.official_sources) < minimum_sources:
        raise ValueError(f"At least {minimum_sources} official sources are required")

    domain_hints = tuple(hint.casefold() for hint in blog_cfg["official_domain_hints"])
    for source in article.official_sources:
        host = (urlparse(str(source.url)).hostname or "").lower().removeprefix("www.")
        if host in BLOCKED_SOURCE_HOSTS or any(host.endswith("." + blocked) for blocked in BLOCKED_SOURCE_HOSTS):
            raise ValueError(f"Non-primary source is not allowed: {host}")
        if source.source_type not in {"government", "regulator", "public_institution", "official_company"}:
            raise ValueError(f"Unsupported source type: {source.source_type}")
        if source.source_type != "official_company" and not any(host.endswith(hint) for hint in domain_hints):
            raise ValueError(f"Official-domain allowlist check failed: {host}")

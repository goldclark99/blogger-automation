from __future__ import annotations

import argparse
import html
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .blogger_client import BloggerClient
from .config import ROOT, env, is_true, load_config
from .images import generate_thumbnail, public_image_url
from .research import build_packet
from .writer import generate_article


def next_publish_time(now: datetime, hour: int) -> datetime:
    candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def image_html(url: str, alt: str) -> str:
    return (
        '<div class="separator" style="clear: both; text-align: center;">'
        f'<img alt="{html.escape(alt, quote=True)}" border="0" '
        'style="width:100%;height:auto;" '
        f'src="{html.escape(url, quote=True)}" />'
        "</div>"
    )


def run_evening(cfg: dict) -> list[dict]:
    timezone = ZoneInfo(cfg["timezone"])
    now = datetime.now(timezone)
    publish_at = next_publish_time(now, cfg["publish_hour"])
    dry_run = is_true("DRY_RUN", True) or not is_true("AUTOMATION_ENABLED", False)
    repository = env("GITHUB_REPOSITORY", required=not dry_run)
    branch = env("GITHUB_REF_NAME", required=False, default="main")
    results: list[dict] = []

    for blog_key, blog_cfg in cfg["blogs"].items():
        client = BloggerClient(blog_cfg["blog_id"], blog_cfg["refresh_token_env"])
        existing = client.list_posts(["live", "draft", "scheduled"], cfg["recent_post_limit"])
        packet = build_packet(blog_key, existing)
        article = generate_article(cfg=cfg, blog_cfg=blog_cfg, packet=packet)

        stamp = publish_at.strftime("%Y-%m-%d-%H%M")
        relative = f"assets/thumbnails/{stamp}-{blog_key}.png"
        image_path = generate_thumbnail(
            article=article,
            blog_key=blog_key,
            model=cfg["image_model"],
            size=cfg["image_size"],
            quality=cfg["image_quality"],
            output_dir=ROOT / "assets" / "thumbnails",
        )
        final_image = ROOT / relative
        if image_path != final_image:
            image_path.replace(final_image)

        image_url = public_image_url(repository=repository or "DRY-RUN/REPOSITORY", branch=branch, relative_path=relative)
        source_links = "".join(
            f'<li><a href="{source.url}" rel="nofollow noopener" target="_blank">{html.escape(source.title)}</a></li>'
            for source in article.official_sources
        )
        disclaimer = blog_cfg.get("disclaimer", "ข้อมูลนี้มีวัตถุประสงค์เพื่อให้ข้อมูลทั่วไป โปรดตรวจสอบเงื่อนไขล่าสุดกับหน่วยงานที่รับผิดชอบ")
        body = (
            image_html(image_url, article.title)
            + article.content_html
            + f"<p><strong>Last updated / อัปเดตล่าสุด:</strong> {now.date().isoformat()}</p>"
            + f"<p>{html.escape(disclaimer)}</p>"
            + f"<h2>Official sources / แหล่งข้อมูลทางการ</h2><ul>{source_links}</ul>"
        )

        result = {
            "blog": blog_key,
            "title": article.title,
            "publish_at": publish_at.isoformat(),
            "labels": article.labels,
            "search_description": article.search_description,
            "thumbnail": relative,
            "official_sources": [str(source.url) for source in article.official_sources],
            "dry_run": dry_run,
        }
        if not dry_run:
            published = client.create_scheduled_post(
                title=article.title,
                content=body,
                labels=article.labels,
                publish_at=publish_at.isoformat(),
            )
            result["post_id"] = published.get("id")
            result["status"] = published.get("status")
        results.append(result)

    return results


def run_morning(cfg: dict) -> list[dict]:
    output: list[dict] = []
    for blog_key, blog_cfg in cfg["blogs"].items():
        client = BloggerClient(blog_cfg["blog_id"], blog_cfg["refresh_token_env"])
        posts = client.list_posts(["live", "draft", "scheduled"], cfg["recent_post_limit"])
        packet = build_packet(blog_key, posts)
        output.append(packet.model_dump())
    return output


def run_weekly(cfg: dict) -> list[dict]:
    report = []
    for blog_key, blog_cfg in cfg["blogs"].items():
        client = BloggerClient(blog_cfg["blog_id"], blog_cfg["refresh_token_env"])
        posts = client.list_posts(["live", "scheduled"], 30)
        report.append(
            {
                "blog": blog_key,
                "recent_posts_checked": len(posts),
                "scheduled_count": sum(post.get("status") == "scheduled" for post in posts),
                "note": "Search Console and AdSense metrics require optional reporting OAuth scopes.",
            }
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["morning", "evening", "weekly"], required=True)
    args = parser.parse_args()
    cfg = load_config()
    runners = {"morning": run_morning, "evening": run_evening, "weekly": run_weekly}
    result = runners[args.mode](cfg)
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    output = reports / f"{args.mode}-latest.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


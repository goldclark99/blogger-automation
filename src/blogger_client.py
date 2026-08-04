from __future__ import annotations

from collections.abc import Iterable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .config import env


BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"


class BloggerClient:
    def __init__(self, blog_id: str, refresh_token_env: str):
        credentials = Credentials(
            token=None,
            refresh_token=env(refresh_token_env),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=env("GOOGLE_OAUTH_CLIENT_SECRET"),
            scopes=[BLOGGER_SCOPE],
        )
        self.blog_id = blog_id
        self.service = build("blogger", "v3", credentials=credentials, cache_discovery=False)

    def list_posts(self, statuses: Iterable[str], limit: int = 60) -> list[dict]:
        posts: list[dict] = []
        for status in statuses:
            page_token = None
            while len(posts) < limit:
                result = (
                    self.service.posts()
                    .list(
                        blogId=self.blog_id,
                        status=status,
                        view="ADMIN",
                        fetchBodies=True,
                        fetchImages=True,
                        maxResults=min(50, limit - len(posts)),
                        pageToken=page_token,
                    )
                    .execute()
                )
                for item in result.get("items", []):
                    posts.append(
                        {
                            "id": item.get("id"),
                            "status": item.get("status", status),
                            "title": item.get("title", ""),
                            "content": item.get("content", ""),
                            "labels": item.get("labels", []),
                            "published": item.get("published"),
                            "updated": item.get("updated"),
                            "url": item.get("url"),
                        }
                    )
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
        return posts[:limit]

    def create_scheduled_post(self, *, title: str, content: str, labels: list[str], publish_at: str) -> dict:
        draft = (
            self.service.posts()
            .insert(
                blogId=self.blog_id,
                isDraft=True,
                body={"kind": "blogger#post", "title": title, "content": content, "labels": labels},
            )
            .execute()
        )
        return (
            self.service.posts()
            .publish(blogId=self.blog_id, postId=draft["id"], publishDate=publish_at)
            .execute()
        )


from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Source(BaseModel):
    title: str
    url: HttpUrl
    source_type: str = Field(description="government, regulator, public_institution, or official_company")


class Article(BaseModel):
    title: str = Field(min_length=20, max_length=140)
    subtitle: str = Field(min_length=20, max_length=220)
    primary_keyword: str = Field(min_length=2, max_length=100)
    secondary_keywords: list[str] = Field(min_length=2, max_length=4)
    category: str
    labels: list[str] = Field(min_length=5, max_length=8)
    search_description: str = Field(min_length=40, max_length=155)
    thumbnail_text: str = Field(min_length=4, max_length=60)
    content_html: str = Field(min_length=1200)
    official_sources: list[Source] = Field(min_length=1)

    @field_validator("labels")
    @classmethod
    def labels_are_unique(cls, value: list[str]) -> list[str]:
        if len({item.casefold() for item in value}) != len(value):
            raise ValueError("labels must be unique")
        return value


class ResearchPacket(BaseModel):
    blog_key: str
    trend_items: list[dict]
    existing_posts: list[dict]
    generated_at: str


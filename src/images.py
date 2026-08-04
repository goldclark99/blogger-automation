from __future__ import annotations

import base64
from pathlib import Path

import requests
from openai import OpenAI


def generate_thumbnail(*, article, blog_key: str, model: str, size: str, quality: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = f"""
Create a clean 16:9 editorial news-card thumbnail for a Blogger article.
Language: {'English' if blog_key == 'english' else 'Thai'}.
Exact visible text, maximum two lines: {article.thumbnail_text}
Topic: {article.title}
Use high contrast, restrained editorial colors, large mobile-readable type and one relevant visual metaphor.
Do not use official logos, seals, watermarks, shock arrows, piles of cash or extra text.
Preserve exact spelling and numbers.
"""
    result = OpenAI().images.generate(model=model, prompt=prompt, size=size, quality=quality)
    item = result.data[0]
    target = output_dir / f"{blog_key}.png"
    if getattr(item, "b64_json", None):
        target.write_bytes(base64.b64decode(item.b64_json))
    elif getattr(item, "url", None):
        response = requests.get(item.url, timeout=60)
        response.raise_for_status()
        target.write_bytes(response.content)
    else:
        raise RuntimeError("Image API returned neither b64_json nor URL")
    return target


def public_image_url(*, repository: str, branch: str, relative_path: str) -> str:
    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is required for public thumbnail URLs")
    clean_path = relative_path.replace("\\", "/")
    return f"https://raw.githubusercontent.com/{repository}/{branch}/{clean_path}"


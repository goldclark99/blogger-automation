from datetime import datetime
from zoneinfo import ZoneInfo

from src.images import public_image_url
from src.main import next_publish_time


def test_next_publish_time_same_day_before_slot():
    now = datetime(2026, 8, 5, 18, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert next_publish_time(now, 20).isoformat() == "2026-08-05T20:00:00+09:00"


def test_next_publish_time_next_day_after_slot():
    now = datetime(2026, 8, 5, 21, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    assert next_publish_time(now, 20).isoformat() == "2026-08-06T20:00:00+09:00"


def test_public_image_url_uses_raw_github():
    assert public_image_url(
        repository="owner/repo", branch="main", relative_path="assets\\thumbnails\\x.png"
    ) == "https://raw.githubusercontent.com/owner/repo/main/assets/thumbnails/x.png"


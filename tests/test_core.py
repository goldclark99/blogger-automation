from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

from src.images import crop_to_16_9, public_image_url
from src.writer import clean_generated_html
from src.main import (
    is_publish_day,
    next_available_publish_time,
    next_publish_time,
    scheduled_run_is_disabled,
)
from src.blogger_client import normalize_status_for_api


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


def test_disabled_schedule_skips_work(monkeypatch):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("AUTOMATION_ENABLED", "false")
    assert scheduled_run_is_disabled() is True


def test_manual_dry_run_still_allowed(monkeypatch):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("AUTOMATION_ENABLED", "false")
    assert scheduled_run_is_disabled() is False


def test_blogger_statuses_are_normalized_for_api():
    assert normalize_status_for_api("live") == "LIVE"
    assert normalize_status_for_api("draft") == "DRAFT"
    assert normalize_status_for_api("scheduled") == "SCHEDULED"


def test_generated_web_citation_markers_are_removed():
    value = '<p>Fact. ([agency.gov](https://agency.gov/page?utm_source=openai))</p>'
    assert clean_generated_html(value) == "<p>Fact.</p>"


def test_thumbnail_is_cropped_to_16_9(tmp_path):
    image_path = tmp_path / "thumbnail.png"
    Image.new("RGB", (1536, 1024), "navy").save(image_path)
    crop_to_16_9(image_path)
    with Image.open(image_path) as result:
        assert result.size == (1536, 864)


def test_90_day_publication_cadence():
    assert is_publish_day(datetime(2026, 8, 30).date()) is True
    assert is_publish_day(datetime(2026, 9, 5).date()) is False
    assert is_publish_day(datetime(2026, 9, 7).date()) is True
    assert is_publish_day(datetime(2026, 10, 7).date()) is False
    assert is_publish_day(datetime(2026, 10, 8).date()) is True


def test_occupied_slot_moves_to_next_valid_slot():
    now = datetime(2026, 9, 4, 18, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    posts = [{"status": "scheduled", "published": "2026-09-04T20:00:00+09:00"}]
    result = next_available_publish_time(now, 20, posts)
    assert result.isoformat() == "2026-09-07T20:00:00+09:00"

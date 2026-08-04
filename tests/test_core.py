from datetime import datetime
from zoneinfo import ZoneInfo

from src.images import public_image_url
from src.main import next_publish_time, scheduled_run_is_disabled
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

"""Tests for PMVHaven site implementation."""

import json

from resources.lib.sites import pmvhaven


def test_format_duration_uses_duration_seconds_fallback():
    """Fallback formatter converts seconds when the API omits duration."""
    assert pmvhaven._format_duration({"durationSeconds": 38}) == "0:38"
    assert pmvhaven._format_duration({"durationSeconds": 2182}) == "36:22"
    assert pmvhaven._format_duration({"durationSeconds": 3723}) == "1:02:03"


def test_list_handles_missing_duration(monkeypatch):
    """List() should not fail when PMVHaven omits the duration field."""
    payload = {
        "videos": [
            {
                "title": "Fallback Duration Video",
                "thumbnailUrl": "https://video.pmvhaven.com/thumb.webp",
                "videoUrl": "https://video.pmvhaven.com/video.mp4",
                "durationSeconds": 38,
                "height": 1080,
                "tags": ["TagA", "TagB"],
                "starsTags": ["ModelA"],
            }
        ],
        "pagination": {"hasNext": False},
    }

    downloads = []

    monkeypatch.setattr(pmvhaven.utils, "getHtml", lambda url, referer=None: json.dumps(payload))
    monkeypatch.setattr(pmvhaven.utils, "eod", lambda: None)
    monkeypatch.setattr(
        pmvhaven.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", **kw: downloads.append(
            {
                "name": name,
                "url": url,
                "icon": icon,
                "duration": kw.get("duration"),
                "quality": kw.get("quality"),
            }
        ),
    )

    pmvhaven.List("https://pmvhaven.com/api/videos?page=1")

    assert len(downloads) == 1
    assert downloads[0]["name"] == "Fallback Duration Video"
    assert downloads[0]["url"] == "https://video.pmvhaven.com/video.mp4"
    assert downloads[0]["icon"] == "https://video.pmvhaven.com/thumb.webp"
    assert downloads[0]["duration"] == "0:38"
    assert downloads[0]["quality"] == "1080p"


def test_list_skips_entries_without_title_or_stream(monkeypatch):
    """List() should skip incomplete entries instead of raising exceptions."""
    payload = {
        "videos": [
            {"title": "Missing Stream", "thumbnailUrl": "thumb", "durationSeconds": 10},
            {"videoUrl": "https://video.pmvhaven.com/video.mp4", "thumbnailUrl": "thumb"},
        ],
        "pagination": {"hasNext": False},
    }

    downloads = []

    monkeypatch.setattr(pmvhaven.utils, "getHtml", lambda url, referer=None: json.dumps(payload))
    monkeypatch.setattr(pmvhaven.utils, "eod", lambda: None)
    monkeypatch.setattr(
        pmvhaven.site,
        "add_download_link",
        lambda *args, **kwargs: downloads.append((args, kwargs)),
    )

    pmvhaven.List("https://pmvhaven.com/api/videos?page=1")

    assert downloads == []


def test_list_handles_invalid_json_payload(monkeypatch):
    """Search/list responses that are not JSON should not raise."""
    downloads = []

    monkeypatch.setattr(pmvhaven.utils, "getHtml", lambda url, referer=None: "<html>blocked</html>")
    monkeypatch.setattr(pmvhaven.utils, "eod", lambda: None)
    monkeypatch.setattr(
        pmvhaven.site,
        "add_download_link",
        lambda *args, **kwargs: downloads.append((args, kwargs)),
    )

    pmvhaven.List("https://pmvhaven.com/api/videos/search?limit=32&page=1&q=test")

    assert downloads == []

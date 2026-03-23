"""Tests for txxx.com site implementation (API-based)."""

import json
from resources.lib.sites import txxx


def test_list_parses_json(monkeypatch):
    """Test that List correctly parses API JSON data."""
    mock_data = {
        "videos": [
            {
                "title": "Video 1",
                "duration": "10:00",
                "scr": "https://img.jpg",
                "video_id": "123",
                "props": {"hd": "1"},
            }
        ],
        "total_count": "120",
    }

    downloads = []
    dirs = []

    monkeypatch.setattr(txxx.utils, "getHtml", lambda *a, **k: json.dumps(mock_data))
    monkeypatch.setattr(
        txxx.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(txxx.site, "add_dir", lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(txxx.utils, "eod", lambda: None)

    txxx.List("https://txxx.com/latest-updates", page=1)

    assert len(downloads) == 1
    assert downloads[0] == "Video 1"

    assert len(dirs) == 1
    assert "Next Page" in dirs[0]


def test_categories_parses_json(monkeypatch):
    """Test that Categories correctly parses API JSON data."""
    mock_cat_data = {
        "categories": [{"title": "Category 1", "dir": "cat1", "total_videos": "100"}]
    }

    dirs = []

    monkeypatch.setattr(
        txxx.utils, "getHtml", lambda *a, **k: json.dumps(mock_cat_data)
    )
    monkeypatch.setattr(txxx.site, "add_dir", lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(txxx.utils, "eod", lambda: None)

    txxx.Categories("https://txxx.com/categories")

    assert len(dirs) == 1
    assert "Category 1" in dirs[0]
    assert "(100 videos)" in dirs[0]


def test_list_handles_invalid_json_payload(monkeypatch):
    downloads = []

    monkeypatch.setattr(txxx.utils, "getHtml", lambda *a, **k: "<html>blocked</html>")
    monkeypatch.setattr(
        txxx.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(txxx.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(txxx.utils, "eod", lambda: None)

    txxx.List("https://txxx.com/latest-updates", page=1)

    assert downloads == []


def test_categories_handles_missing_category_list(monkeypatch):
    dirs = []

    monkeypatch.setattr(txxx.utils, "getHtml", lambda *a, **k: "{}")
    monkeypatch.setattr(txxx.site, "add_dir", lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(txxx.utils, "eod", lambda: None)

    txxx.Categories("https://txxx.com/categories")

    assert dirs == []

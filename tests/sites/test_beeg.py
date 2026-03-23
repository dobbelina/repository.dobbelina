"""Tests for beeg.com site implementation (API-based)."""

import json
import base64
from unittest.mock import MagicMock

from resources.lib.sites import beeg



def test_list_parses_json(monkeypatch):
    """Test that List correctly parses API JSON data."""
    mock_data = [
        {
            "fc_facts": [{"fc_thumbs": [1, 2, 3], "fc_start": 0, "fc_end": 600}],
            "tags": [{"is_owner": True, "tg_name": "Tag1", "tg_slug": "slug1", "id": "7629"}],
            "file": {

                "id": "123",
                "data": [
                    {"cd_column": "sf_name", "cd_value": "Video 1"},
                    {"cd_column": "sf_story", "cd_value": "Story 1"},
                ],
                "fl_duration": 600,
                "fl_height": 1080,
            },
        }
    ]

    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return json.dumps(mock_data)

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "icon": iconimage,
                "duration": kwargs.get("duration"),
                "quality": kwargs.get("quality"),
            }
        )

    monkeypatch.setattr(beeg.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(beeg.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(beeg.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(beeg.utils, "eod", lambda: None)

    beeg.List("https://store.externulls.com/facts/tag?id=27173&limit=48&offset=0")

    assert len(downloads) == 1
    assert "Tag1 - Video 1" in downloads[0]["name"]
    assert downloads[0]["duration"] == "10:00"
    assert downloads[0]["quality"] == "1080p"
    assert "https://thumbs.externulls.com/videos/123/" in downloads[0]["icon"]

    # Verify video data is encoded in URL
    assert "id=123" in downloads[0]["url"]
    assert "tag_id=7629" in downloads[0]["url"]


def test_playvid_fresh_fetch(monkeypatch):
    """Test that Playvid fetches fresh video data."""
    mock_video_data = {
        "file": {
            "id": "123",
            "hls_resources": {
                "fl_cdn_1080": "path/to/video.mp4"
            }
        }
    }
    
    play_calls = []
    
    class MockVP:
        def __init__(self, name, download=None):
            self.name = name
            self.progress = MagicMock()
        def play_from_direct_link(self, url):
            play_calls.append(url)

    monkeypatch.setattr(beeg.utils, "getHtml", lambda *a, **k: json.dumps(mock_video_data))
    monkeypatch.setattr(beeg.utils, "VideoPlayer", MockVP)
    monkeypatch.setattr(beeg.utils, "prefquality", lambda *a, **k: "path/to/video.mp4")

    beeg.Playvid("id=123&tag_id=7629", "Test Video")    
    assert len(play_calls) == 1
    assert "path/to/video.mp4" in play_calls[0]
    assert "Referer=" in play_calls[0]


def test_category_parses_json(monkeypatch):
    """Test that Category correctly parses category API data."""
    # Upstream change: Category(url) now fetches json and iterates it directly
    mock_cat_data = [
        {
            "tg_name": "Category 1",
            "tg_slug": "cat1",
            "thumbs": [{"id": "t1", "crops": [{"id": "c1"}]}],
        }
    ]

    dirs = []

    def fake_get_html(url, *args, **kwargs):
        return json.dumps(mock_cat_data)

    def fake_add_dir(name, url, mode, iconimage, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(beeg.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(beeg.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(beeg.utils, "eod", lambda: None)

    beeg.Category("https://store.externulls.com/tag/recommends?type=other&slug=index")

    assert len(dirs) == 1
    assert dirs[0]["name"] == "Category 1"
    assert "slug=cat1" in dirs[0]["url"]


def test_list_handles_invalid_json_payload(monkeypatch):
    downloads = []

    monkeypatch.setattr(beeg.utils, "getHtml", lambda *a, **k: "<html>blocked</html>")
    monkeypatch.setattr(
        beeg.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(beeg.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(beeg.utils, "eod", lambda: None)

    beeg.List("https://store.externulls.com/facts/tag?id=27173&limit=48&offset=0")

    assert downloads == []


def test_category_handles_invalid_json_payload(monkeypatch):
    dirs = []

    monkeypatch.setattr(beeg.utils, "getHtml", lambda *a, **k: "<html>blocked</html>")
    monkeypatch.setattr(beeg.site, "add_dir", lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(beeg.utils, "eod", lambda: None)

    beeg.Category("https://store.externulls.com/tag/recommends?type=other&slug=index")

    assert dirs == []

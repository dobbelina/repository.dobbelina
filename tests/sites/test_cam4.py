"""Tests for cam4.com site implementation (API-based)."""

import json
from resources.lib.sites import cam4


def test_list_parses_json(monkeypatch):
    """Test that List correctly parses API JSON data."""
    mock_data = {
        "users": [
            {
                "username": "Model1",
                "age": 22,
                "hdStream": True,
                "snapshotImageLink": "https://img.jpg",
                "viewers": 100,
                "countryCode": "ES",
                "languages": ["es", "en"],
                "resolution": "1080p",
                "sexPreference": "Guys",
                "statusMessage": "Status 1",
                "showTags": ["Tag1", "Tag2"],
            }
        ]
    }

    downloads = []

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append({"name": name, "url": url, "quality": kwargs.get("quality")})

    monkeypatch.setattr(cam4.utils, "_getHtml", lambda *a, **k: json.dumps(mock_data))
    monkeypatch.setattr(cam4.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(cam4.utils, "eod", lambda: None)
    monkeypatch.setattr(cam4.utils.addon, "getSetting", lambda x: "false")
    monkeypatch.setattr(cam4.utils, "get_country", lambda x: "Spain")
    monkeypatch.setattr(
        cam4.utils, "get_language", lambda x: "Spanish" if x == "es" else "English"
    )

    cam4.List("gender=female", page=1)

    assert len(downloads) == 1
    assert "Model1" in downloads[0]["name"]
    assert "[22]" in downloads[0]["name"]
    assert downloads[0]["quality"] == "HD"
    assert "[Spain]" in downloads[0]["name"]


def test_playvid_parses_json(monkeypatch):
    """Test that Playvid correctly parses stream info JSON."""
    mock_play_data = {"cdnURL": "https://stream.cam4.com/playlist.m3u8"}

    play_calls = []

    class FakeVideoPlayer:
        def __init__(self, name):
            pass

        def play_from_direct_link(self, url):
            play_calls.append(url)

    monkeypatch.setattr(
        cam4.utils, "_getHtml", lambda *a, **k: json.dumps(mock_play_data)
    )
    monkeypatch.setattr(cam4.utils, "VideoPlayer", FakeVideoPlayer)

    cam4.Playvid("Model1", "Model1")

    assert len(play_calls) == 1
    assert "playlist.m3u8" in play_calls[0]


def test_list_handles_invalid_json_payload(monkeypatch):
    downloads = []

    monkeypatch.setattr(cam4.utils, "_getHtml", lambda *a, **k: "<html>blocked</html>")
    monkeypatch.setattr(
        cam4.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(cam4.utils, "eod", lambda: None)
    monkeypatch.setattr(cam4.utils.addon, "getSetting", lambda x: "false")
    monkeypatch.setattr(cam4.utils, "get_country", lambda x: "Spain")
    monkeypatch.setattr(cam4.utils, "get_language", lambda x: x)

    cam4.List("gender=female", page=1)

    assert downloads == []

"""Tests for amateur.tv site implementation (API-based)."""

import json
from resources.lib.sites import amateurtv


def test_list_parses_json(monkeypatch):
    """Test that List correctly parses API JSON data."""
    mock_data = {
        "cams": {
            "nodes": [
                {
                    "online": True,
                    "user": {"username": "Model1", "age": [25]},
                    "hd": True,
                    "imageURL": "https://en.amateur.tv/img.jpg?v=1",
                    "viewers": {"totalNumber": 100},
                    "country": "ES",
                    "quality": "1080p",
                    "topic": {"text": "Topic 1"},
                    "isInPrivateExclusive": False,
                }
            ],
            "totalCount": 300,
        }
    }

    downloads = []
    dirs = []

    def fake_get_html(url, *args, **kwargs):
        return json.dumps(mock_data)

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append({"name": name, "username": url, "icon": iconimage})

    def fake_add_dir(name, url, mode, iconimage, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(amateurtv.utils, "_getHtml", fake_get_html)
    monkeypatch.setattr(amateurtv.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(amateurtv.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(amateurtv.utils, "eod", lambda: None)
    monkeypatch.setattr(amateurtv.utils.addon, "getSetting", lambda x: "false")

    amateurtv.List("w", page=1)

    assert len(downloads) == 1
    assert "Model1" in downloads[0]["name"]
    assert "[25]" in downloads[0]["name"]
    assert "[ES]" in downloads[0]["name"]
    assert downloads[0]["username"] == "Model1"
    assert "www.amateur.tv" in downloads[0]["icon"]

    # Check pagination
    assert len(dirs) == 1
    assert "Next Page..." in dirs[0]["name"]


def test_playvid_parses_json(monkeypatch):
    """Test that Playvid correctly parses video source JSON."""
    mock_play_data = {
        "videoTechnologies": {"fmp4-hls": "https://stream.amateur.tv/playlist.m3u8"}
    }

    play_calls = []

    class FakeVideoPlayer:
        def __init__(self, name):
            self.progress = type(
                "obj", (object,), {"update": lambda *a: None, "close": lambda *a: None}
            )

        def play_from_direct_link(self, url):
            play_calls.append(url)

    monkeypatch.setattr(
        amateurtv.utils, "_getHtml", lambda *a, **k: json.dumps(mock_play_data)
    )
    monkeypatch.setattr(amateurtv.utils, "VideoPlayer", FakeVideoPlayer)

    amateurtv.Playvid("Model1", "Model1")

    assert len(play_calls) == 1
    assert "playlist.m3u8" in play_calls[0]


def test_list_handles_invalid_json_payload(monkeypatch):
    downloads = []

    monkeypatch.setattr(amateurtv.utils, "_getHtml", lambda *a, **k: "<html>down</html>")
    monkeypatch.setattr(
        amateurtv.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(amateurtv.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(amateurtv.utils, "eod", lambda: None)
    monkeypatch.setattr(amateurtv.utils.addon, "getSetting", lambda x: "false")

    amateurtv.List("w", page=1)

    assert downloads == []

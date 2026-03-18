"""Tests for LemonCams pagination and playback routing."""

import pytest
from resources.lib.sites import lemoncams
from unittest.mock import MagicMock


def test_list_uses_real_pagination_and_adds_next_page(monkeypatch):
    added_links = []
    added_dirs = []

    def fake_api_get(params):
        assert params["function"] == "cams"
        assert params["provider"] == "stripchat"
        assert params["page"] == "1"
        return {
            "cams": [
                {
                    "username": "model1",
                    "provider": "stripchat",
                    "title": "test title",
                    "numberOfUsers": 12,
                    "imageUrl": "https://img.example/model1.jpg",
                    "embedUrl": "https://stream.example/model1.m3u8"
                }
            ],
            "maxPage": 3,
        }

    monkeypatch.setattr(lemoncams, "_api_get", fake_api_get)
    monkeypatch.setattr(
        lemoncams.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc, **kwargs: added_links.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        ),
    )
    monkeypatch.setattr(
        lemoncams.site,
        "add_dir",
        lambda name, url, mode, iconimage="", page=None, **kwargs: added_dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "page": page,
            }
        ),
    )
    monkeypatch.setattr(lemoncams.utils, "eod", lambda: None)

    lemoncams.List("stripchat", page=1)

    assert len(added_links) == 1
    assert "model1" in added_links[0]["name"]
    # URL should contain the piped stream URL now
    assert "https://www.lemoncams.com/stripchat/model1|https://stream.example/model1.m3u8" == added_links[0]["url"]
    
    assert added_dirs == [
        {
            "name": "Next Page (2/3)",
            "url": "stripchat",
            "mode": "List",
            "page": 2,
        }
    ]


def test_playvid_uses_direct_stream(monkeypatch):
    play_calls = []
    
    class MockVP:
        def __init__(self, name):
            self.name = name
            self.IA_check = None
        def play_from_direct_link(self, url):
            play_calls.append({"name": self.name, "url": url})

    monkeypatch.setattr(lemoncams.utils, "VideoPlayer", MockVP)
    
    # Test with piped URL
    url = "https://www.lemoncams.com/stripchat/model1|https://stream.example/model1.m3u8"
    lemoncams.Playvid(url, "Model 1")
    
    assert len(play_calls) == 1
    assert play_calls[0]["name"] == "Model 1"
    assert "https://stream.example/model1.m3u8" in play_calls[0]["url"]
    assert "User-Agent=" in play_calls[0]["url"]
    assert "Referer=" in play_calls[0]["url"]


def test_playvid_searches_if_no_cached_stream(monkeypatch):
    play_calls = []
    
    def fake_fetch_payload(provider, page):
        return {
            "cams": [
                {
                    "username": "model1",
                    "provider": "stripchat",
                    "embedUrl": "https://newstream.example/model1.m3u8"
                }
            ]
        }

    class MockVP:
        def __init__(self, name):
            self.name = name
        def play_from_direct_link(self, url):
            play_calls.append({"url": url})

    monkeypatch.setattr(lemoncams, "_fetch_provider_payload", fake_fetch_payload)
    monkeypatch.setattr(lemoncams.utils, "VideoPlayer", MockVP)
    
    # Test with URL without piped stream
    url = "https://www.lemoncams.com/stripchat/model1"
    lemoncams.Playvid(url, "Model 1")
    
    assert len(play_calls) == 1
    assert "https://newstream.example/model1.m3u8" in play_calls[0]["url"]

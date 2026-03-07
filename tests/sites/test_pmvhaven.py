"""Tests for pmvhaven site implementation."""

import json
from unittest.mock import MagicMock

from resources.lib.sites import pmvhaven


def _sample_payload(has_next=True):
    return {
        "videos": [
            {
                "title": "Clip One",
                "thumbnailUrl": "https://pmvhaven.com/thumb1.jpg",
                "videoUrl": "https://pmvhaven.com/video1.mp4",
                "duration": "01:23",
                "height": 1080,
                "hasExtremeContent": True,
                "tags": ["tag1", "tag2"],
                "starsTags": ["model1"],
            },
            {
                "title": "Clip Two",
                "thumbnailUrl": "https://pmvhaven.com/thumb2.jpg",
                "hlsMasterPlaylistUrl": "https://pmvhaven.com/video2.m3u8",
                "duration": "02:34",
                "height": 720,
                "tags": [],
                "starsTags": [],
            },
        ],
        "pagination": {"hasNext": has_next, "page": 1},
    }


def test_main_menu(monkeypatch):
    dirs = []
    monkeypatch.setattr(
        pmvhaven.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append((name, url, mode)),
    )
    monkeypatch.setattr(pmvhaven, "List", lambda *a, **k: None)
    monkeypatch.setattr(pmvhaven.utils, "eod", lambda: None)

    pmvhaven.Main()

    assert dirs == [
        (
            "[COLOR hotpink]Search[/COLOR]",
            "https://pmvhaven.com/api/videos/search?limit=32&page=1&q=",
            "Search",
        )
    ]


def test_list_parses_json_and_adds_next_page(monkeypatch):
    payload = _sample_payload(has_next=True)
    downloads = []
    dirs = []

    monkeypatch.setattr(pmvhaven.utils, "getHtml", lambda *a, **k: json.dumps(payload))
    monkeypatch.setattr(
        pmvhaven.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc, **kwargs: downloads.append(
            {"name": name, "url": url, "mode": mode, "quality": kwargs.get("quality")}
        ),
    )
    monkeypatch.setattr(
        pmvhaven.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append((name, url, mode, kwargs.get("contextm"))),
    )
    monkeypatch.setattr(pmvhaven.utils, "eod", lambda: None)

    pmvhaven.List("https://pmvhaven.com/api/videos?limit=32&page=1")

    assert downloads[0]["name"].endswith("[COLOR red] EXTREME[/COLOR]")
    assert downloads[0]["url"] == "https://pmvhaven.com/video1.mp4"
    assert downloads[0]["quality"] == "1080p"
    assert downloads[1]["url"] == "https://pmvhaven.com/video2.m3u8"
    assert dirs[0][0] == "Next Page (2)"
    assert "pmvhaven.GotoPage" in dirs[0][3][0][1]


def test_list_handles_missing_pagination(monkeypatch):
    payload = {"videos": []}
    dirs = []

    monkeypatch.setattr(pmvhaven.utils, "getHtml", lambda *a, **k: json.dumps(payload))
    monkeypatch.setattr(
        pmvhaven.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append((name, url, mode)),
    )
    monkeypatch.setattr(pmvhaven.utils, "eod", lambda: None)

    pmvhaven.List("https://pmvhaven.com/api/videos?limit=32&page=1")

    assert dirs == []


def test_playvid_plays_direct_link(monkeypatch):
    played = []

    class MockPlayer:
        def __init__(self, *a, **k):
            self.progress = MagicMock()

        def play_from_direct_link(self, url):
            played.append(url)

    monkeypatch.setattr(pmvhaven.utils, "VideoPlayer", MockPlayer)

    pmvhaven.Playvid("https://pmvhaven.com/video1.mp4", "Name")

    assert played == ["https://pmvhaven.com/video1.mp4"]


def test_search(monkeypatch):
    search_dir = []
    list_calls = []
    monkeypatch.setattr(pmvhaven.site, "search_dir", lambda *a, **k: search_dir.append((a, k)))
    monkeypatch.setattr(pmvhaven, "List", lambda url: list_calls.append(url))

    pmvhaven.Search("https://pmvhaven.com/api/videos/search?limit=32&page=1&q=")
    pmvhaven.Search(
        "https://pmvhaven.com/api/videos/search?limit=32&page=1&q=",
        keyword="abc def",
    )

    assert search_dir
    assert list_calls == ["https://pmvhaven.com/api/videos/search?limit=32&page=1&q=abc+def"]


def test_goto_page_updates_container(monkeypatch):
    monkeypatch.setattr(pmvhaven.xbmcgui, "Dialog", lambda: type("D", (), {"numeric": lambda *a: "7"})())
    executed = []
    monkeypatch.setattr(pmvhaven.xbmc, "executebuiltin", lambda cmd: executed.append(cmd))

    pmvhaven.GotoPage("https://pmvhaven.com/api/videos?limit=32&page=2")

    assert executed
    assert "pmvhaven.List" in executed[0]
    assert "page%3D7" in executed[0]


def test_lookupinfo_builds_selector_options(monkeypatch):
    selected = []
    executed = []

    monkeypatch.setattr(
        pmvhaven.utils,
        "selector",
        lambda title, lookup_list, show_on_one=False: selected.append(lookup_list) or next(iter(lookup_list.values())),
    )
    monkeypatch.setattr(pmvhaven.xbmc, "executebuiltin", lambda cmd: executed.append(cmd))

    pmvhaven.Lookupinfo("tag1,tag2|model1")

    assert selected
    assert "Tag - tag1" in selected[0]
    assert "Model - model1" in selected[0]
    assert executed

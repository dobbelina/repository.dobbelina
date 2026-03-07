"""Tests for porno1.hu site implementation."""

from pathlib import Path
from resources.lib.sites import porno1hu

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "porno1hu"


def load_fixture(name):
    """Load a fixture file from the porno1hu fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_videos(monkeypatch):
    """Test that List correctly parses video items."""
    html = load_fixture("listing.html")
    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return html

    monkeypatch.setattr(porno1hu.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(
        porno1hu.site,
        "add_download_link",
        lambda n, u, m, i, p, **k: downloads.append({"name": n, "url": u, "icon": i}),
    )
    monkeypatch.setattr(porno1hu.utils, "eod", lambda: None)

    porno1hu.List("https://porno1.hu/friss-porno/")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Video A"
    assert "video/alpha" in downloads[0]["url"]
    assert "alpha.jpg" in downloads[0]["icon"]


def test_list_pagination(monkeypatch):
    """Test that List handles pagination."""
    html = load_fixture("listing.html")
    dirs = []

    monkeypatch.setattr(porno1hu.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        porno1hu.site, "add_dir", lambda n, u, m, i, **k: dirs.append({"name": n, "url": u})
    )
    monkeypatch.setattr(porno1hu.utils, "eod", lambda: None)

    porno1hu.List("https://porno1.hu/friss-porno/")

    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "mode=async" in dirs[0]["url"]


def test_playvid_decodes_kvs(monkeypatch):
    video_page = load_fixture("video_page.html")
    embed_page = load_fixture("embed_page.html")
    player_calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None):
            self.name = name
            self.download = download
            self.progress = type(
                "p",
                (),
                {
                    "update": lambda *args, **kwargs: None,
                    "close": lambda *args, **kwargs: None,
                },
            )()

        def play_from_direct_link(self, url):
            player_calls.append(url)

        def play_from_html(self, html):
            player_calls.append("html_fallback")

        def play_from_kt_player(self, html, url=None):
            player_calls.append(("kt", html, url))

    def fake_get_html(url, ref=None, hdr=None):
        if "embed" in url:
            return embed_page
        return video_page

    monkeypatch.setattr(porno1hu.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(porno1hu.utils, "VideoPlayer", FakeVideoPlayer)

    porno1hu.Playvid("https://porno1.hu/video/test", "Test Video")

    assert player_calls
    assert player_calls[0][0] == "kt"
    assert player_calls[0][1] == embed_page
    assert player_calls[0][2] == "https://porno1.hu/video/test"

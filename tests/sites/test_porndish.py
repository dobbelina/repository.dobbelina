"""Functional tests for porndish site implementation."""

from pathlib import Path
from resources.lib.sites import porndish

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "porndish"


def load_fixture(name):
    """Load a fixture file from the porndish fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_site_initialization():
    """Test that the site is properly initialized"""
    assert porndish.site.name == "porndish"
    assert "Porndish" in porndish.site.title


def test_list_parses_video_items(monkeypatch):
    """Test that List correctly parses video items with BeautifulSoup."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    monkeypatch.setattr(porndish.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(porndish.site, "add_download_link", lambda n, u, m, i, p: downloads.append({"name": n, "url": u, "icon": i}))
    monkeypatch.setattr(porndish.site, "add_dir", lambda n, u, m, i: dirs.append({"name": n, "url": u}))
    monkeypatch.setattr(porndish.utils, "eod", lambda: None)

    porndish.List("https://www.porndish.com/page/1/")

    # Should have 2 videos from the fixture
    assert len(downloads) == 2
    assert downloads[0]["name"] == "Video One Title"
    assert downloads[0]["url"] == "https://www.porndish.com/video-one/"
    assert downloads[0]["icon"] == "https://www.porndish.com/thumb1.jpg"

    assert downloads[1]["name"] == "Video Two Title"
    assert downloads[1]["url"] == "https://www.porndish.com/video-two/"
    assert downloads[1]["icon"] == "https://www.porndish.com/thumb2.jpg"

    # Should have pagination
    assert len(dirs) == 1
    assert dirs[0]["name"] == "Next Page"
    assert "/page/2/" in dirs[0]["url"]


def test_playvid_implementation(monkeypatch):
    """Test that Playvid routes through site-link playback."""
    captured = {}

    class _VP:
        def play_from_site_link(self, source_url, page_url):
            captured["source_url"] = source_url
            captured["page_url"] = page_url

    monkeypatch.setattr(porndish.utils, "VideoPlayer", lambda *_a, **_k: _VP())
    porndish.Playvid("https://www.porndish.com/video-one/", "Video One")

    assert captured == {
        "source_url": "https://www.porndish.com/video-one/",
        "page_url": "https://www.porndish.com/video-one/",
    }


def test_main_exposes_latest_directory(monkeypatch):
    dirs = []

    monkeypatch.setattr(porndish, "List", lambda url: None)
    monkeypatch.setattr(
        porndish.site, "add_dir", lambda name, url, mode, iconimage=None, **kwargs: dirs.append({"name": name, "url": url, "mode": mode})
    )
    monkeypatch.setattr(porndish.utils, "eod", lambda: None)

    porndish.Main()

    assert dirs == [
        {
            "name": "[COLOR hotpink]Latest[/COLOR]",
            "url": "https://www.porndish.com/page/1/",
            "mode": "List",
        }
    ]

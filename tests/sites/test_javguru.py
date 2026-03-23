"""Tests for jav.guru site implementation."""

from pathlib import Path

from resources.lib.sites import javguru


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "javguru"


def load_fixture(name):
    """Load a fixture file from the javguru fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List correctly parses video items with BeautifulSoup."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(javguru.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(javguru.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(javguru.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(javguru.utils, "eod", lambda: None)

    javguru.List("https://jav.guru/")

    # Should have 3 videos
    assert len(downloads) == 3

    # Check first video
    assert downloads[0]["name"] == "JAV GURU Video Title 1"
    assert downloads[0]["url"] == "/jav-video-1234/"
    assert downloads[0]["icon"] == "https://cdn.javsts.com/thumb1.jpg"

    # Check second video (data-src)
    assert downloads[1]["name"] == "JAV GURU Video Title 2"
    assert downloads[1]["url"] == "/jav-video-5678/"
    assert downloads[1]["icon"] == "https://cdn.javsts.com/thumb2.jpg"

    # Check third video
    assert downloads[2]["name"] == "JAV GURU Video Title 3"
    assert downloads[2]["url"] == "/jav-video-9012/"


def test_list_pagination(monkeypatch):
    """Test that List correctly adds pagination."""
    html = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(javguru.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(javguru.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(javguru.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(javguru.utils, "eod", lambda: None)

    javguru.List("https://jav.guru/")

    # Should have next page
    next_pages = [d for d in dirs if "Next Page" in d["name"]]
    assert len(next_pages) == 1
    # Should be page 3 (next after current page 2)
    assert "/page/3/" in next_pages[0]["url"]
    assert "(3/25)" in next_pages[0]["name"]


def test_search_without_keyword(monkeypatch):
    """Test that Search without keyword shows search dialog."""
    search_called = []

    def fake_search_dir(url, mode):
        search_called.append((url, mode))

    monkeypatch.setattr(javguru.site, "search_dir", fake_search_dir)

    javguru.Search("https://jav.guru/?s=")

    assert len(search_called) == 1
    assert search_called[0][1] == "Search"


def test_search_with_keyword(monkeypatch):
    """Test that Search with keyword calls List with encoded search."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(javguru, "List", fake_list)

    javguru.Search("https://jav.guru/?s=", keyword="test query")

    assert len(list_calls) == 1
    assert "test+query" in list_calls[0]


def test_play_uses_iframe_fallback_when_json_sources_are_missing(monkeypatch):
    captured = {}

    class _DummyVP:
        def __init__(self, name, download=False, **kwargs):
            self.progress = type(
                "P",
                (),
                {
                    "update": lambda *a, **k: None,
                    "close": lambda *a, **k: None,
                },
            )()

        def play_from_link_to_resolve(self, source):
            captured["resolved"] = source

        def play_from_html(self, html, url=None):
            captured["html"] = html
            captured["url"] = url

        def play_from_direct_link(self, url):
            captured["direct"] = url

    monkeypatch.setattr(javguru.utils, "VideoPlayer", _DummyVP)
    monkeypatch.setattr(
        javguru.utils,
        "getHtml",
        lambda url, referer=None, headers=None: '<html><iframe src="/player/abc123"></iframe></html>',
    )

    javguru.Play("https://jav.guru/jav-video-1234/", "Example")

    assert captured["resolved"] == "https://jav.guru/player/abc123"


def test_play_falls_back_to_page_html_with_context(monkeypatch):
    captured = {}

    class _DummyVP:
        def __init__(self, name, download=False, **kwargs):
            self.progress = type(
                "P",
                (),
                {
                    "update": lambda *a, **k: None,
                    "close": lambda *a, **k: None,
                },
            )()

        def play_from_html(self, html, url=None):
            captured["html"] = html
            captured["url"] = url

        def play_from_link_to_resolve(self, source):
            captured["resolved"] = source

        def play_from_direct_link(self, url):
            captured["direct"] = url

    monkeypatch.setattr(javguru.utils, "VideoPlayer", _DummyVP)
    monkeypatch.setattr(javguru.utils, "getHtml", lambda url, referer=None, headers=None: "<html>No sources</html>")

    javguru.Play("https://jav.guru/jav-video-5678/", "Example")

    assert captured["html"] == "<html>No sources</html>"
    assert captured["url"] == "https://jav.guru/jav-video-5678/"

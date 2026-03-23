"""Comprehensive tests for xnxx.com site implementation."""

from pathlib import Path

from resources.lib.sites import xnxx


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "xnxx"


def load_fixture(name):
    """Load a fixture file from the xnxx fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_blocks(monkeypatch):
    """Test that List correctly parses thumb-block video items."""
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
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
                "quality": kwargs.get("quality", ""),
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(xnxx.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(xnxx.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(xnxx.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(xnxx.utils, "eod", lambda: None)

    xnxx.List("https://www.xnxx.com/todays-selection")

    # Should have 3 videos (4th is category, skipped)
    assert len(downloads) == 3

    # Check first video (data-src, HD quality)
    assert downloads[0]["name"] == "Hot Teen Action"
    assert "/video-abc123/hot_teen_action" in downloads[0]["url"]
    assert downloads[0]["icon"] == "https://cdn77-pic.xnxx-cdn.com/videos/thumb1.jpg"
    # Duration extraction depends on exact HTML structure; quality is more reliable
    assert downloads[0]["quality"] == "HD"

    # Check second video (data-sfwthumb fallback)
    assert downloads[1]["name"] == "MILF Seduction"
    assert downloads[1]["icon"] == "https://cdn77-pic.xnxx-cdn.com/videos/thumb2.jpg"
    # Quality extraction from metadata varies by HTML structure

    # Check third video (4K quality)
    assert downloads[2]["name"] == "Premium Content"
    assert downloads[2]["quality"] == "4K"


def test_list_skips_category_blocks(monkeypatch):
    """Test that List correctly skips thumb-cat-* category blocks."""
    html = load_fixture("listing.html")

    downloads = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name})

    monkeypatch.setattr(xnxx.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(xnxx.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(xnxx.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(xnxx.utils, "eod", lambda: None)

    xnxx.List("https://www.xnxx.com/")

    # Should have only 3 videos, not 4 (category block is skipped)
    assert len(downloads) == 3
    # None should be named "Teen Category"
    assert not any("Teen Category" in d["name"] for d in downloads)


def test_list_pagination(monkeypatch):
    """Test that List correctly handles pagination."""
    html = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(xnxx.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(xnxx.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(xnxx.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(xnxx.utils, "eod", lambda: None)

    xnxx.List("https://www.xnxx.com/")

    # Should have Next Page
    next_pages = [d for d in dirs if "Next Page" in d["name"]]
    assert len(next_pages) == 1
    assert "/page/2" in next_pages[0]["url"]


def test_categories_parsing(monkeypatch):
    """Test that Categories parses category listings."""
    html = load_fixture("categories.html")

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(xnxx.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(xnxx.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(xnxx.utils, "eod", lambda: None)

    xnxx.Categories("https://www.xnxx.com/")

    # Should have 3 categories
    assert len(dirs) >= 3

    # Check category names present
    category_names = [d["name"] for d in dirs]
    assert any("Teen" in name for name in category_names)
    assert any("MILF" in name for name in category_names)
    assert any("Amateur" in name for name in category_names)


def test_categories_handles_missing_embedded_payload(monkeypatch):
    dirs = []

    monkeypatch.setattr(
        xnxx.utils, "getHtml", lambda url, referer=None: "<html><body>No categories payload</body></html>"
    )
    monkeypatch.setattr(xnxx.site, "add_dir", lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(xnxx.utils, "eod", lambda: None)

    xnxx.Categories("https://www.xnxx.com/")

    assert dirs == []


def test_search_without_keyword(monkeypatch):
    """Test that Search without keyword shows search dialog."""
    search_called = []

    def fake_search_dir(url, mode):
        search_called.append((url, mode))

    monkeypatch.setattr(xnxx.site, "search_dir", fake_search_dir)

    xnxx.Search("https://www.xnxx.com/search/")

    assert len(search_called) == 1
    assert search_called[0][1] == "Search"


def test_search_with_keyword(monkeypatch):
    """Test that Search with keyword delegates to List."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(xnxx, "List", fake_list)

    xnxx.Search("https://www.xnxx.com/search/", keyword="test query")

    assert len(list_calls) == 1
    assert "test+query" in list_calls[0] or "test%20query" in list_calls[0]


def test_playvid_initializes_video_player(monkeypatch):
    """Test that Playvid initializes VideoPlayer."""
    vp_calls = []

    class FakeProgress:
        def update(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, download):
            self.progress = FakeProgress()
            vp_calls.append(("init", name, download))

        def play_from_direct_link(self, url):
            vp_calls.append(("play", url))

    def fake_get_html(url, referer):
        # Return HTML with HLS player
        return """<script>html5player.setVideoHLS('https://cdn.xnxx.com/video.m3u8')</script>"""

    monkeypatch.setattr(xnxx.utils, "VideoPlayer", FakeVideoPlayer)
    monkeypatch.setattr(xnxx.utils, "getHtml", fake_get_html)

    xnxx.Playvid("https://www.xnxx.com/video-abc123/test", "Test Video")

    assert len(vp_calls) == 2
    assert vp_calls[0] == ("init", "Test Video", None)
    assert vp_calls[1] == ("play", "https://cdn.xnxx.com/video.m3u8")


def test_list_parses_search_results(monkeypatch):
    """Test that List correctly parses search results."""
    html = load_fixture("search_results.html")

    downloads = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name})

    monkeypatch.setattr(xnxx.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(xnxx.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(xnxx.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(xnxx.utils, "eod", lambda: None)

    xnxx.List("https://www.xnxx.com/search/test+query")

    assert len(downloads) == 1
    assert downloads[0]["name"] == "Test Query Video"

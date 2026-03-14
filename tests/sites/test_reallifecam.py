"""Comprehensive tests for reallifecam.to site implementation."""

from pathlib import Path
from unittest.mock import MagicMock

from resources.lib.sites import reallifecam


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "reallifecam"


def load_fixture(name):
    """Load a fixture file from the reallifecam fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List correctly parses video items with BeautifulSoup."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": kwargs.get("duration"),
                "quality": kwargs.get("quality"),
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

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(reallifecam.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos?o=mr")

    # Should have 4 unique videos (5th one has no title and becomes 'Video')
    assert len(downloads) == 5

    # Check first video - using data-src and title-truncate
    assert downloads[0]["name"] == "Leora and Paul Bedroom Fun"
    assert "/videos/leora-paul-bedroom-fun-123/" in downloads[0]["url"]
    assert downloads[0]["icon"] == "https://reallifecam.to/images/thumbs/thumb1.jpg"
    assert downloads[0]["duration"] == "18:45"
    assert downloads[0]["quality"] == "HD"

    # Check second video - using data-original and title class
    assert downloads[1]["name"] == "Nora and Kira Shower Scene"
    assert "/videos/nora-kira-shower-456/" in downloads[1]["url"]
    assert downloads[1]["icon"] == "https://reallifecam.to/images/thumbs/thumb2.jpg"
    assert downloads[1]["duration"] == "25:30"

    # Check third video - using direct src and h3 title
    assert downloads[2]["name"] == "Masha Party Night"
    assert "/videos/masha-party-night-789/" in downloads[2]["url"]
    assert downloads[2]["icon"] == "https://reallifecam.to/images/thumbs/thumb3.jpg"
    assert downloads[2]["duration"] == "12:15"
    assert downloads[2]["quality"] == "HD"

    # Check fourth video - simpvids style with content-title
    assert downloads[3]["name"] == "Maya and Diego Pool Time"
    assert "https://simpvids.com/videos/maya-diego-pool-321/" in downloads[3]["url"]
    assert downloads[3]["icon"] == "https://simpvids.com/images/thumbs/thumb4.jpg"
    assert downloads[3]["duration"] == "33:22"
    assert downloads[3]["quality"] == "HD"

    # Check fifth video - minimal info, defaults to 'Video'
    assert downloads[4]["name"] == "Video"
    assert "/videos/late-night-fun-999/" in downloads[4]["url"]
    assert downloads[4]["icon"] == "https://reallifecam.to/images/thumbs/thumb5.jpg"
    assert downloads[4]["duration"] == "08:30"

    # Should have pagination
    assert len(dirs) == 1
    assert "Next Page (3)" in dirs[0]["name"]
    assert "/videos?o=mr&page=3" in dirs[0]["url"]


def test_list_handles_protocol_relative_urls(monkeypatch):
    """Test that List correctly handles protocol-relative URLs."""
    html = """
    <div class="col-sm-6">
        <a href="/videos/test-123/">
            <img src="//reallifecam.to/images/thumbs/test.jpg">
        </a>
    </div>
    """

    downloads = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"icon": iconimage})

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(reallifecam.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos")

    assert len(downloads) == 1
    assert downloads[0]["icon"] == "https://reallifecam.to/images/thumbs/test.jpg"


def test_list_handles_relative_image_urls(monkeypatch):
    """Test that List correctly converts relative image URLs to absolute."""
    html = """
    <div class="item">
        <a href="/videos/test-456/">
            <img src="/images/thumbs/test2.jpg">
        </a>
    </div>
    """

    downloads = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"icon": iconimage})

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(reallifecam.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos")

    assert len(downloads) == 1
    assert downloads[0]["icon"] == "https://reallifecam.to/images/thumbs/test2.jpg"


def test_list_deduplicates_videos(monkeypatch):
    """Test that List correctly deduplicates videos with same URL."""
    html = """
    <div class="col-sm-6">
        <a href="/videos/duplicate-123/">
            <img src="https://reallifecam.to/images/thumbs/dup1.jpg">
        </a>
    </div>
    <div class="col-sm-6">
        <a href="/videos/duplicate-123/">
            <img src="https://reallifecam.to/images/thumbs/dup2.jpg">
        </a>
    </div>
    """

    downloads = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"url": url})

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(reallifecam.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos")

    # Should only have one video despite duplicate
    assert len(downloads) == 1


def test_list_with_pagination(monkeypatch):
    """Test that List adds pagination correctly."""
    html = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(reallifecam.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos?o=mr")

    # Should have next page link
    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "page=3" in dirs[0]["url"]


def test_list_without_pagination(monkeypatch):
    """Test that List handles absence of pagination gracefully."""
    html = """
    <div class="col-sm-6">
        <a href="/videos/test-123/">
            <img src="https://reallifecam.to/images/thumbs/test.jpg">
        </a>
    </div>
    """

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name})

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(reallifecam.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos")

    # Should have no pagination
    assert len(dirs) == 0


def test_list_parses_new_video_format(monkeypatch):
    """Test that List correctly parses the new /video/ URL format."""
    html = (FIXTURE_DIR / "listing_new.html").read_text(encoding="utf-8")

    downloads = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
            }
        )

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(reallifecam.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.List("https://reallifecam.to/videos?o=mr")

    assert len(downloads) == 2
    assert "/video/21206/" in downloads[0]["url"] or "/video/21206" in downloads[0]["url"]
    assert "Massage Viper" in downloads[0]["name"]
    assert "/video/21205/" in downloads[1]["url"] or "/video/21205" in downloads[1]["url"]
    assert "Savaira" in downloads[1]["name"]


def test_categories_parses_items(monkeypatch):
    """Test that Categories correctly parses category items."""
    html = load_fixture("categories.html")

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
            }
        )

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.Categories("https://reallifecam.to/categories")

    # Should have 5 categories
    assert len(dirs) == 5

    # Check first category
    assert "Bedroom" in dirs[0]["name"]
    assert "342" in dirs[0]["name"]
    assert "/categories/bedroom" in dirs[0]["url"]
    assert dirs[0]["icon"] == "https://reallifecam.to/images/cats/bedroom.jpg"

    # Check second category
    assert "Bathroom" in dirs[1]["name"]
    assert "158" in dirs[1]["name"]
    assert "/categories/bathroom" in dirs[1]["url"]

    # Check third category
    assert "Kitchen" in dirs[2]["name"]
    assert "95" in dirs[2]["name"]

    # Check fourth category - protocol-relative URL
    assert "Living Room" in dirs[3]["name"]
    assert "267" in dirs[3]["name"]
    assert dirs[3]["icon"] == "https://reallifecam.to/images/cats/living.jpg"

    # Check fifth category
    assert "Pool" in dirs[4]["name"]
    assert "52" in dirs[4]["name"]


def test_categories_deduplicates_items(monkeypatch):
    """Test that Categories correctly deduplicates category items."""
    html = """
    <div class="col-sm">
        <a href="/categories/bedroom">
            <img src="https://reallifecam.to/images/cats/bedroom.jpg">
            <div class="title">Bedroom</div>
        </a>
    </div>
    <div class="col-sm">
        <a href="/categories/bedroom">
            <img src="https://reallifecam.to/images/cats/bedroom2.jpg">
            <div class="title">Bedroom</div>
        </a>
    </div>
    """

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(reallifecam.utils, "eod", lambda: None)

    reallifecam.Categories("https://reallifecam.to/categories")

    # Should only have one category despite duplicate
    assert len(dirs) == 1
    assert "Bedroom" in dirs[0]["name"]


def test_search_without_keyword_shows_dialog(monkeypatch):
    """Test that Search without keyword shows search input dialog."""
    search_called = []

    def fake_search_dir(url, mode):
        search_called.append((url, mode))

    monkeypatch.setattr(reallifecam.site, "search_dir", fake_search_dir)

    reallifecam.Search("https://reallifecam.to/search/videos?search_query=")

    assert len(search_called) == 1
    assert search_called[0][1] == "Search"


def test_search_with_keyword_calls_list(monkeypatch):
    """Test that Search with keyword delegates to List."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(reallifecam, "List", fake_list)

    reallifecam.Search(
        "https://reallifecam.to/search/videos?search_query=", keyword="test query"
    )

    assert len(list_calls) == 1
    assert "test%20query" in list_calls[0]


def test_playvid_handles_list_embed_response(monkeypatch):
    """Playvid should treat list-like embed responses as direct source candidates."""
    played_links = []

    class MockPlayer:
        def __init__(self, *args, **kwargs):
            self.progress = MagicMock()
            self.resolveurl = MagicMock()
            self.resolveurl.HostedMediaFile.return_value = False

        def play_from_link_list(self, links):
            played_links.append(links)

        def play_from_link_to_resolve(self, source):
            raise AssertionError("unexpected resolve path")

        def play_from_direct_link(self, link):
            raise AssertionError("unexpected direct link path")

        def play_from_html(self, html, url=None):
            raise AssertionError("unexpected HTML fallback")

    video_page = """
    <div class="video-embedded">
        <iframe src="https://embed.example/video"></iframe>
    </div>
    """
    embed_links = [
        "https://cdn.example/stream.m3u8",
        "https://cdn.example/fallback.mp4",
    ]

    def fake_get_html(url, referer=None):
        if url == "https://example.com/video/1":
            return video_page
        if url == "https://embed.example/video":
            return embed_links
        raise AssertionError("unexpected url {}".format(url))

    monkeypatch.setattr(reallifecam.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(reallifecam.utils, "VideoPlayer", MockPlayer)

    reallifecam.Playvid("https://example.com/video/1", "Name")

    assert played_links == [embed_links]

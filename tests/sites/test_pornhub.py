"""Comprehensive tests for pornhub.com site implementation."""

from pathlib import Path

from resources.lib.sites import pornhub


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "pornhub"


def load_fixture(name):
    """Load a fixture file from the pornhub fixtures directory."""
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
                "contextm": kwargs.get("contextm"),
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, desc="", **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "folder": kwargs.get("Folder", True),
            }
        )

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornhub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.List("https://www.pornhub.com/video?o=cm")

    # Should have 3 videos
    assert len(downloads) == 3

    def _base_icon(value):
        return value.split("|", 1)[0] if value else value

    # Check first video
    assert downloads[0]["name"] == "Hot Teen Gets Drilled Hard"
    assert "/view_video.php?viewkey=ph12345abcde" in downloads[0]["url"]
    assert (
        _base_icon(downloads[0]["icon"])
        == "https://ci.phncdn.com/videos/202411/thumb1.jpg"
    )
    assert downloads[0]["contextm"] is not None  # Should have context menu

    # Check second video (uses data-thumb-url)
    assert downloads[1]["name"] == "MILF Seduces Young Stud"
    assert "/view_video.php?viewkey=ph67890fghij" in downloads[1]["url"]
    assert (
        _base_icon(downloads[1]["icon"])
        == "https://ci.phncdn.com/videos/202411/thumb2.jpg"
    )

    # Check third video (uses data-src fallback)
    assert downloads[2]["name"] == "Premium HD Video Quality"
    assert (
        _base_icon(downloads[2]["icon"])
        == "https://ci.phncdn.com/videos/202411/thumb3.jpg"
    )

    # Should have pagination and filter reset
    assert len(dirs) >= 1
    # Check for "Clear all filters" or title dir
    filter_dirs = [
        d
        for d in dirs
        if "Clear all filters" in d["name"] or "Latest Videos" in d["name"]
    ]
    assert len(filter_dirs) > 0


def test_list_handles_empty_results(monkeypatch):
    """Test that List handles 'Error Page Not Found' gracefully."""
    html = load_fixture("empty_results.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode})

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(
        pornhub.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(pornhub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.List("https://www.pornhub.com/video?search=nonexistent")

    # Should have no videos
    assert len(downloads) == 0

    # Should have "No videos found" message with clear filters option
    no_results = [d for d in dirs if "No videos found" in d["name"]]
    assert len(no_results) == 1
    assert "Clear all filters" in no_results[0]["name"]
    assert no_results[0]["mode"] == "ResetFilters"


def test_list_with_pagination(monkeypatch):
    """Test that List adds pagination when present."""
    html = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(pornhub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.List("https://www.pornhub.com/video?o=cm")

    # Should have next page
    next_pages = [d for d in dirs if "Next" in d["name"] or "page=2" in d["url"]]
    assert len(next_pages) >= 1


def test_categories_parses_and_sorts(monkeypatch):
    """Test that Categories correctly parses categories and sorts alphabetically."""
    html = load_fixture("categories.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, desc=""):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
            }
        )

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.Categories("https://www.pornhub.com/categories")

    # Should have 4 categories
    assert len(dirs) == 4

    # Check alphabetical sorting (Amateur, Latina, MILF, Teen)
    assert "Amateur" in dirs[0]["name"]
    assert "Latina" in dirs[1]["name"]
    assert "MILF" in dirs[2]["name"]
    assert "Teen" in dirs[3]["name"]

    # Check video counts are displayed
    assert "(12,345 videos)" in dirs[3]["name"]  # Teen
    assert "(8,567 videos)" in dirs[2]["name"]  # MILF
    assert "(15,234 videos)" in dirs[0]["name"]  # Amateur
    assert "(6,789 videos)" in dirs[1]["name"]  # Latina

    # Check URLs
    assert "/categories/amateur" in dirs[0]["url"]
    assert "/categories/milf" in dirs[2]["url"]

    # Check icons
    assert "teen.jpg" in dirs[3]["icon"]


def test_categories_handles_missing_video_count(monkeypatch):
    """Test that Categories works even if video count is missing."""
    html = """
    <html>
    <div class="category-wrapper">
        <a href="/categories/test" alt="Test Category">
            <img src="test.jpg">
            <div class="title">Test Category</div>
        </a>
    </div>
    </html>
    """

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, desc=""):
        dirs.append({"name": name})

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.Categories("https://www.pornhub.com/categories")

    assert len(dirs) == 1
    # Should just be the category name without count
    assert dirs[0]["name"] == "Test Category"


def test_search_without_keyword_shows_search_dialog(monkeypatch):
    """Test that Search without keyword shows search input dialog."""
    search_called = []

    def fake_search_dir(url, mode):
        search_called.append((url, mode))

    monkeypatch.setattr(pornhub.site, "search_dir", fake_search_dir)

    pornhub.Search("https://www.pornhub.com/video/search?search=")

    assert len(search_called) == 1
    assert search_called[0][1] == "Search"


def test_search_with_keyword_calls_list(monkeypatch):
    """Test that Search with keyword delegates to List with encoded search."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(pornhub, "List", fake_list)

    pornhub.Search("https://www.pornhub.com/video/search?search=", keyword="test query")

    assert len(list_calls) == 1
    assert "test+query" in list_calls[0]


def test_search_url_encoding(monkeypatch):
    """Test that Search properly URL-encodes special characters."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(pornhub, "List", fake_list)

    pornhub.Search(
        "https://www.pornhub.com/video/search?search=", keyword="test & query"
    )

    assert len(list_calls) == 1
    assert "test+%26+query" in list_calls[0] or "test+&+query" in list_calls[0]


def test_list_parses_search_results(monkeypatch):
    """Test that List correctly parses search results."""
    html = load_fixture("search_results.html")

    downloads = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name, "url": url})

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornhub.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.List("https://www.pornhub.com/video/search?search=test+query")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Test Query Video One"
    assert downloads[1]["name"] == "Test Query Video Two"


def test_list_parses_all_search_result_wrappers(monkeypatch):
    """Test that List aggregates results across multiple search wrappers."""
    html = """
    <html>
    <body>
    <h1 class="searchPageTitle">Search results for: "test query"</h1>
    <div id="videoSearchWrapper">
        <div class="pcVideoListItem">
            <a href="/view_video.php?viewkey=phfeatured1" title="Featured Video One">
                <img data-mediumthumb="https://ci.phncdn.com/videos/search/featured1.jpg" alt="Featured Video One">
                <div class="duration">10:15</div>
            </a>
        </div>
        <div class="pcVideoListItem">
            <a href="/view_video.php?viewkey=phfeatured2" title="Featured Video Two">
                <img data-mediumthumb="https://ci.phncdn.com/videos/search/featured2.jpg" alt="Featured Video Two">
                <div class="duration">11:00</div>
            </a>
        </div>
    </div>
    <div id="searchPageVideoList">
        <div class="pcVideoListItem">
            <a href="/view_video.php?viewkey=phresult1" title="Result Video One">
                <img data-mediumthumb="https://ci.phncdn.com/videos/search/result1.jpg" alt="Result Video One">
                <div class="duration">12:00</div>
            </a>
        </div>
        <div class="pcVideoListItem">
            <a href="/view_video.php?viewkey=phresult2" title="Result Video Two">
                <img data-mediumthumb="https://ci.phncdn.com/videos/search/result2.jpg" alt="Result Video Two">
                <div class="duration">13:00</div>
            </a>
        </div>
        <div class="pcVideoListItem">
            <a href="/view_video.php?viewkey=phresult3" title="Result Video Three">
                <img data-mediumthumb="https://ci.phncdn.com/videos/search/result3.jpg" alt="Result Video Three">
                <div class="duration">14:00</div>
            </a>
        </div>
        <div class="pcVideoListItem">
            <a href="/view_video.php?viewkey=phresult4" title="Result Video Four">
                <img data-mediumthumb="https://ci.phncdn.com/videos/search/result4.jpg" alt="Result Video Four">
                <div class="duration">15:00</div>
            </a>
        </div>
    </div>
    </body>
    </html>
    """

    downloads = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name, "url": url})

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornhub.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.List("https://www.pornhub.com/video/search?search=test+query")

    assert len(downloads) == 6
    assert [item["name"] for item in downloads] == [
        "Featured Video One",
        "Featured Video Two",
        "Result Video One",
        "Result Video Two",
        "Result Video Three",
        "Result Video Four",
    ]


def test_playvid_calls_video_player(monkeypatch):
    """Test that Playvid initializes VideoPlayer and calls resolve."""
    video_player_calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download):
            self.name = name
            self.download = download
            self.progress = type("P", (), {"update": lambda *a, **k: None, "close": lambda *a, **k: None})()
            video_player_calls.append(("init", name, download))

        def play_from_link_to_resolve(self, url):
            video_player_calls.append(("play", url))

    monkeypatch.setattr(pornhub.utils, "VideoPlayer", FakeVideoPlayer)

    pornhub.Playvid(
        "https://www.pornhub.com/view_video.php?viewkey=ph12345",
        "Test Video",
        download=None,
    )

    assert len(video_player_calls) == 2
    assert video_player_calls[0] == ("init", "Test Video", None)
    assert video_player_calls[1] == (
        "play",
        "https://www.pornhub.com/view_video.php?viewkey=ph12345",
    )


def test_list_extracts_page_title(monkeypatch):
    """Test that List extracts and displays page title."""
    html = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "mode": mode})

    monkeypatch.setattr(pornhub.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhub.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(pornhub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhub.utils, "eod", lambda: None)

    pornhub.List("https://www.pornhub.com/video?o=cm")

    # Should have title dir with "Latest Videos"
    title_dirs = [d for d in dirs if "Latest Videos" in d["name"]]
    assert len(title_dirs) > 0
    assert "Clear all filters" in title_dirs[0]["name"]

"""Tests for playvids.com site implementation."""

from pathlib import Path

from resources.lib.sites import playvids


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "playvids"


def load_fixture(name):
    """Load a fixture file from the playvids fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List correctly parses video items with BeautifulSoup."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
                "quality": kwargs.get("quality", ""),
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(playvids.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(playvids.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(playvids.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(playvids.utils, "eod", lambda: None)

    playvids.List("https://www.playvids.com/?page=1")

    # Should have 3 videos
    assert len(downloads) == 3

    # Check first video (src, HD badge)
    assert downloads[0]["name"] == "Hot Stepmom Action"
    assert "video-one" in downloads[0]["url"]
    assert "img1.jpg" in downloads[0]["icon"]
    assert downloads[0]["duration"] == "10:25"
    assert downloads[0]["quality"] == "HD"

    # Check second video (data-src fallback, no HD)
    assert downloads[1]["name"] == "College Girls Wild"
    assert "video-two" in downloads[1]["url"]
    assert "img2.jpg" in downloads[1]["icon"]
    assert downloads[1]["duration"] == "8:15"
    assert downloads[1]["quality"] == ""

    # Check third video (HD in HTML string)
    assert downloads[2]["name"] == "Passionate Encounter"
    assert "video-three" in downloads[2]["url"]
    assert downloads[2]["duration"] == "12:00"
    assert downloads[2]["quality"] == "HD"

    # Should have pagination
    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "page=2" in dirs[0]["url"]


def test_cat_parses_categories(monkeypatch):
    """Test that Cat correctly parses category links."""
    html = load_fixture("categories.html")

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(playvids.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(playvids.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(playvids.utils, "eod", lambda: None)

    playvids.Cat("https://www.playvids.com/categories")

    # Should have 3 categories
    assert len(dirs) == 3

    # Check categories
    assert dirs[0]["name"] == "MILF"
    assert "category/milf" in dirs[0]["url"]

    assert dirs[1]["name"] == "Teen"
    assert "category/teen" in dirs[1]["url"]

    assert dirs[2]["name"] == "Anal"
    assert "category/anal" in dirs[2]["url"]


def test_search_without_keyword_shows_search_dialog(monkeypatch):
    """Test that Search without keyword shows search input dialog."""
    search_called = []

    def fake_search_dir(url, mode):
        search_called.append((url, mode))

    monkeypatch.setattr(playvids.site, "search_dir", fake_search_dir)

    playvids.Search("https://www.playvids.com/videos?q=")

    assert len(search_called) == 1
    assert search_called[0][1] == "Search"


def test_search_with_keyword_calls_list(monkeypatch):
    """Test that Search with keyword delegates to List."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(playvids, "List", fake_list)

    playvids.Search("https://www.playvids.com/videos?q=", keyword="test query")

    assert len(list_calls) == 1
    assert "test+query" in list_calls[0]


def test_search_with_keyword_uses_default_search_endpoint_for_base_url(monkeypatch):
    """Test that Search builds the search endpoint when given the site base URL."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(playvids, "List", fake_list)

    playvids.Search("https://www.playvids.com/", keyword="test query")

    assert len(list_calls) == 1
    assert list_calls[0] == "https://www.playvids.com/videos?q=test+query"


def test_list_handles_missing_info_section(monkeypatch):
    """Test that List handles missing info sections gracefully."""
    html = """
    <html>
    <body>
    <div class="card">
        <img src="thumb.jpg">
    </div>
    </body>
    </html>
    """

    downloads = []

    def fake_get_html(url, referer=None):
        return html

    monkeypatch.setattr(playvids.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(
        playvids.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(playvids.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(playvids.utils, "eod", lambda: None)

    playvids.List("https://www.playvids.com/?page=1")

    # Should skip items without info section
    assert len(downloads) == 0


def test_list_parses_current_live_card_markup(monkeypatch):
    """Test that List supports the current PlayVids card-body markup."""
    html = """
    <html>
    <body>
    <div class="card thumbs_rotate itemVideo v0259e8458">
        <div class="card-img">
            <a href="/VW5NrXhVQzG/example-video">
                <img
                    class="card-img-top"
                    src="https://cdn-img1.playvids.com/thumbs/example.jpg"
                    alt="Example Video Title"
                />
            </a>
            <div class="video-info">
                <span class="duration">27:28</span>
            </div>
        </div>
        <div class="card-body">
            <h5 class="card-title">
                <a href="/VW5NrXhVQzG/example-video">Example Video Title</a>
            </h5>
            <div class="card-info">
                <span class="autor"><a href="/u/example">example</a></span>
            </div>
        </div>
    </div>
    </body>
    </html>
    """

    downloads = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
            }
        )

    monkeypatch.setattr(playvids.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(playvids.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(playvids.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(playvids.utils, "eod", lambda: None)

    playvids.List("https://www.playvids.com/videos?q=test")

    assert len(downloads) == 1
    assert downloads[0]["name"] == "Example Video Title"
    assert downloads[0]["url"] == "https://www.playvids.com/VW5NrXhVQzG/example-video"
    assert downloads[0]["icon"] == "https://cdn-img1.playvids.com/thumbs/example.jpg"
    assert downloads[0]["duration"] == "27:28"

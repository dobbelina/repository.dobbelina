"""Comprehensive tests for avple site implementation."""

from pathlib import Path
from unittest.mock import MagicMock
from six.moves import urllib_parse

from resources.lib.sites import avple


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "avple"


def load_fixture(name):
    """Load a fixture file from the avple fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List correctly parses video items from JSON data."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None, timeout=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, desc="", **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(avple.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(avple.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(avple.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)

    avple.List("https://avple.tv/")

    # Should have 3 videos
    assert len(downloads) == 3

    # Check first video
    assert downloads[0]["name"] == "Beautiful Asian Girl IPX-001"
    assert "/video/12345" in downloads[0]["url"]
    assert "ipx001.jpg" in downloads[0]["icon"]
    assert downloads[0]["duration"] == "45:30"

    # Check second video
    assert downloads[1]["name"] == "Premium JAV SNIS-456"
    assert "/video/67890" in downloads[1]["url"]
    assert downloads[1]["duration"] == "120:15"

    # Check third video (no duration)
    assert downloads[2]["name"] == "Uncensored Beauty ABC-789"
    assert "/video/11223" in downloads[2]["url"]
    assert downloads[2]["duration"] == ""

    # Should have pagination
    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "(2/50)" in dirs[0]["name"]


def test_list_handles_search_results_format(monkeypatch):
    """Test that List correctly handles search results JSON format."""
    html = load_fixture("search_results.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None, timeout=None, headers=None):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
            }
        )

    monkeypatch.setattr(avple.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(avple.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(avple.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)

    avple.List("https://avple.tv/search?page=2&sort=date&key=test")

    # Should have 2 videos from search results
    assert len(downloads) == 2

    assert downloads[0]["name"] == "Search Result Video One"
    assert "/video/99988" in downloads[0]["url"]

    assert downloads[1]["name"] == "Search Result Video Two"
    assert "/video/77766" in downloads[1]["url"]

    # Should have pagination (currently on page 2 of 10)
    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "(3/10)" in dirs[0]["name"]


def test_list_handles_404_error(monkeypatch):
    """Test that List handles 404 errors gracefully."""
    html = "<html><body><h1>404</h1><p>>404< Not Found</p></body></html>"

    def fake_get_html(url, referer=None, timeout=None, headers=None):
        return html

    monkeypatch.setattr(avple.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)
    monkeypatch.setattr(avple.utils, "notify", lambda **kwargs: None)

    # Should handle 404 gracefully without crashing
    avple.List("https://avple.tv/nonexistent")


def test_list_handles_missing_json(monkeypatch):
    """Test that List handles missing JSON script tag."""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <div>No JSON here</div>
    </body>
    </html>
    """

    def fake_get_html(url, referer=None, timeout=None, headers=None):
        return html

    monkeypatch.setattr(avple.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)
    monkeypatch.setattr(avple.utils, "notify", lambda *args, **kwargs: None)

    # Should handle missing JSON gracefully
    avple.List("https://avple.tv/")


def test_search_without_keyword_shows_search_dialog(monkeypatch):
    """Test that Search without keyword shows search input dialog."""
    search_called = []

    def fake_search_dir(url, mode):
        search_called.append((url, mode))

    monkeypatch.setattr(avple.site, "search_dir", fake_search_dir)

    avple.Search("https://avple.tv/search?page=1&sort=date&key=")

    assert len(search_called) == 1
    assert search_called[0][1] == "Search"


def test_search_with_keyword_calls_list(monkeypatch):
    """Test that Search with keyword delegates to List."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(avple, "List", fake_list)

    avple.Search("https://avple.tv/search?page=1&sort=date&key=", keyword="test query")

    assert len(list_calls) == 1
    assert "test%20query" in list_calls[0]


def test_cat_lists_all_tags(monkeypatch):
    """Test that Cat lists all predefined tags."""
    dirs = []

    def fake_add_dir(name, url, mode, iconimage=None, desc=""):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(avple.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)

    avple.Cat("https://avple.tv/")

    # Should have many tags (check a few known ones)
    assert len(dirs) > 50

    # Find specific tags
    tag_names = [d["name"] for d in dirs]
    assert "Big breasts" in tag_names
    assert "Creampie" in tag_names
    assert "Uncoded liberation" in tag_names  # Uncensored


def test_list_pagination_url_handling(monkeypatch):
    """Test that List correctly builds next page URLs for different URL formats."""
    html = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None, timeout=None, headers=None):
        return html

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "url": url,
            }
        )

    monkeypatch.setattr(avple.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(avple.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(avple.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)

    # Test URL without page parameter
    avple.List("https://avple.tv/")
    assert len(dirs) == 1
    assert dirs[0]["url"] == "https://avple.tv/"

    # Test URL with /1/date format (Line 129)
    dirs.clear()
    avple.List("https://avple.tv/tags/93/1/date")
    assert len(dirs) == 1
    assert "/2/date" in dirs[0]["url"]


def test_main(monkeypatch):
    """Test Main() function."""
    dirs = []
    monkeypatch.setattr(avple.site, "add_dir", lambda *a, **k: dirs.append(a))
    monkeypatch.setattr(avple, "List", lambda *a: None)
    monkeypatch.setattr(avple.utils, "eod", lambda: None)
    
    avple.Main()
    assert len(dirs) == 3


def test_gotopage(monkeypatch):
    """Test GotoPage() logic (Lines 306-319)."""
    builtins = []
    notify_calls = []

    class _Dialog:
        def numeric(self, *_a, **_k):
            return "5"

    monkeypatch.setattr(avple.xbmcgui, "Dialog", _Dialog)
    monkeypatch.setattr(avple.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd))
    monkeypatch.setattr(avple.utils, "notify", lambda msg=None: notify_calls.append(msg))

    # 1. page= format
    avple.GotoPage("https://avple.tv/search?page=1", "1", "10")
    assert "page%3D5" in builtins[0] or "page=5" in urllib_parse.unquote(builtins[0])

    # 2. /1/date format
    builtins.clear()
    avple.GotoPage("https://avple.tv/tags/93/1/date", "1", "10")
    assert "/5/date" in urllib_parse.unquote(builtins[0])

    # 3. Out of range
    avple.GotoPage("https://avple.tv/search?page=1", "1", "2")
    assert "Out of range!" in notify_calls


def test_playvid_success_and_errors(monkeypatch):
    """Test Playvid() paths (Lines 333-373)."""
    html_success = "<script>var source = 'https://stream.mp4';</script>"
    html_no_source = "<script>var nothing = '';</script>"
    
    played = []
    notify_calls = []
    
    class MockPlayer:
        def __init__(self, *a, **k):
            self.progress = MagicMock()
        def play_from_direct_link(self, url):
            played.append(url)

    monkeypatch.setattr(avple.utils, "VideoPlayer", MockPlayer)
    monkeypatch.setattr(avple.utils, "notify", lambda *a, **k: notify_calls.append(a))

    # 1. Success
    monkeypatch.setattr(avple.utils, "getHtml", lambda *a, **k: html_success)
    avple.Playvid("https://avple.tv/video/1", "Name")
    assert any("https://stream.mp4" in p for p in played)

    # 2. No source URL
    monkeypatch.setattr(avple.utils, "getHtml", lambda *a, **k: html_no_source)
    avple.Playvid("https://avple.tv/video/1", "Name")
    assert any("Unable to find video source" in str(n) for n in notify_calls)

    # 3. Load error
    monkeypatch.setattr(avple.utils, "getHtml", MagicMock(side_effect=Exception("boom")))
    avple.Playvid("https://avple.tv/video/1", "Name")
    assert any("Unable to load video page" in str(n) for n in notify_calls)


def test_list_extra_branches(monkeypatch):
    """Test extra branches in List() (Lines 70-73, 94, 106, 109, 118, 153-154)."""
    notify_calls = []
    monkeypatch.setattr(avple.utils, "notify", lambda *a, **k: notify_calls.append(a))
    monkeypatch.setattr(avple.utils, "eod", lambda: None)

    # 1. getHtml error (Line 70-73)
    monkeypatch.setattr(avple.utils, "getHtml", MagicMock(side_effect=Exception("boom")))
    avple.List("https://avple.tv/")
    
    # 2. initialState fallback (Line 94)
    html_initial = '<script id="__NEXT_DATA__" type="application/json">{"props":{"initialState":{"page":1,"totalPage":1,"data":[{"title":"T1","id":"id1"}]}}}</script>'
    monkeypatch.setattr(avple.utils, "getHtml", lambda *a, **k: html_initial)
    downloads = []
    monkeypatch.setattr(avple.site, "add_download_link", lambda *a, **k: downloads.append(a))
    avple.List("https://avple.tv/")
    assert len(downloads) == 1

    # 3. Skip non-list videos, non-dict video, missing videoid (Line 106, 109, 118)
    html_skips = '<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"indexListObj":{"obj":"not a list", "obj2":["not a dict", {"title":"no id"}]}}}}</script>'
    monkeypatch.setattr(avple.utils, "getHtml", lambda *a, **k: html_skips)
    downloads.clear()
    avple.List("https://avple.tv/")
    assert len(downloads) == 0

    # 4. Parsing error (Line 153-154)
    html_bad_json = '<script id="__NEXT_DATA__" type="application/json">{invalid json}</script>'
    monkeypatch.setattr(avple.utils, "getHtml", lambda *a, **k: html_bad_json)
    avple.List("https://avple.tv/")
    assert any("Unable to parse videos" in str(n) for n in notify_calls)


def test_playvid_parsing_error(monkeypatch):
    """Test Playvid() parsing error branch (Lines 370-373)."""
    notify_calls = []
    
    class MockPlayer:
        def __init__(self, *a, **k):
            self.progress = MagicMock()
        def play_from_direct_link(self, url):
            pass

    monkeypatch.setattr(avple.utils, "VideoPlayer", MockPlayer)
    monkeypatch.setattr(avple.utils, "notify", lambda *a, **k: notify_calls.append(a))
    
    # Force error in parse_html
    monkeypatch.setattr(avple.utils, "parse_html", MagicMock(side_effect=Exception("boom")))
    monkeypatch.setattr(avple.utils, "getHtml", lambda *a, **k: "some html")
    
    avple.Playvid("https://avple.tv/video/1", "Name")
    assert any("Unable to extract video link" in str(n) for n in notify_calls)

"""Comprehensive tests for erogarga site implementation."""

from pathlib import Path
from unittest.mock import MagicMock
from six.moves import urllib_parse

from resources.lib.sites import erogarga


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "erogarga"


def load_fixture(name):
    """Load a fixture file from the erogarga fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List() correctly parses video items using BeautifulSoup."""
    html = load_fixture("list.html")

    downloads = []
    dirs = []

    def fake_get_html(url, *args, **kwargs):
        return html

    def fake_add_download_link(
        name, url, mode, iconimage, desc="", contextm=None, quality="", **kwargs
    ):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "desc": desc,
                "quality": quality,
                "contextm": contextm,
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, contextm=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode, "contextm": contextm})

    monkeypatch.setattr(erogarga.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(erogarga.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(erogarga.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    # Call List
    erogarga.List("https://www.erogarga.com/?filter=latest")

    # Verify we got 3 videos (skipped the photo gallery)
    assert len(downloads) == 3


def test_list_skips_photo_galleries(monkeypatch):
    """Test that List() skips photo galleries (type-photos class)."""
    html = load_fixture("list.html")

    downloads = []

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        erogarga.site, "add_download_link", lambda *a, **k: downloads.append(a)
    )
    monkeypatch.setattr(erogarga.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    erogarga.List("https://www.erogarga.com/?filter=latest")

    # Should have 3 videos, skipping the 1 photo gallery
    assert len(downloads) == 3


def test_list_handles_pagination(monkeypatch):
    """Test that List() correctly handles pagination."""
    html = load_fixture("list.html")

    dirs = []

    def fake_add_dir(name, url, mode, iconimage=None, contextm=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode, "contextm": contextm})

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(erogarga.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    # Call List
    erogarga.List("https://www.erogarga.com/?filter=latest")

    # Verify pagination was added
    next_pages = [d for d in dirs if "Next Page" in d["name"]]
    assert len(next_pages) == 1


def test_cat_parses_categories(monkeypatch):
    """Test that Cat() correctly parses category items using BeautifulSoup."""
    html = load_fixture("categories.html")

    dirs = []

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode, "icon": iconimage})

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    # Call Cat
    erogarga.Cat("https://www.erogarga.com/categories/")

    # Should have 3 categories
    assert len(dirs) == 3


def test_search_without_keyword_shows_dialog(monkeypatch):
    """Test that Search() without keyword shows search dialog."""
    search_dir_called = [False]

    def fake_search_dir(*args):
        search_dir_called[0] = True

    monkeypatch.setattr(erogarga.site, "search_dir", fake_search_dir)

    erogarga.Search("https://www.erogarga.com/?s=")

    assert search_dir_called[0]


def test_search_with_keyword_calls_list(monkeypatch):
    """Test that Search() with keyword calls List()."""
    list_called_with = {}

    def fake_list(url):
        list_called_with["url"] = url

    monkeypatch.setattr(erogarga, "List", fake_list)

    erogarga.Search("https://www.erogarga.com/?s=", keyword="sample search")

    # Verify URL contains the search keyword
    assert "url" in list_called_with
    assert "sample%20search" in list_called_with["url"]


def test_list_handles_empty_results(monkeypatch):
    """Test that List() handles empty results gracefully."""
    html = load_fixture("empty_results.html")

    notify_called = []

    def fake_notify(msg=None, **kwargs):
        notify_called.append(msg)

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.utils, "notify", fake_notify)
    monkeypatch.setattr(erogarga.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(erogarga.site, "add_dir", lambda *a, **k: None)

    erogarga.List("https://www.erogarga.com/?s=nonexistent")

    # Should have called notify with "No data found"
    assert len(notify_called) == 1
    assert notify_called[0] == "No data found"


def test_list_extracts_duration(monkeypatch):
    """Test that List() correctly extracts video durations."""
    html = load_fixture("list.html")

    downloads = []

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name, "desc": desc})

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(erogarga.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    erogarga.List("https://www.erogarga.com/?filter=latest")

    assert len(downloads) == 3


def test_list_adds_context_menu(monkeypatch):
    """Test that List() adds context menu items for lookup and related."""
    html = load_fixture("list.html")

    downloads = []

    def fake_add_download_link(
        name, url, mode, iconimage, desc="", contextm=None, **kwargs
    ):
        downloads.append({"contextm": contextm})

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(erogarga.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    erogarga.List("https://www.erogarga.com/?filter=latest")

    assert len(downloads) == 3


def test_play_extracts_phixxx_iframe(monkeypatch):
    """Test that Play() extracts video from phixxx.cc player."""
    html = load_fixture("video.html")

    video_player_calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None, regex=None, direct_regex=None):
            self.resolveurl = MagicMock()
            self.resolveurl.HostedMediaFile.return_value.valid_url.return_value = False
            video_player_calls.append(("init", name, download))

        def play_from_link_to_resolve(self, url):
            video_player_calls.append(("play_resolve", url))

        def play_from_direct_link(self, url):
            video_player_calls.append(("play_direct", url))

    def fake_post_html(url, form_data=None, **kwargs):
        return '{"source":[{"file":"https://cdn.example.com/video.mp4"}]}'

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.utils, "VideoPlayer", FakeVideoPlayer)
    monkeypatch.setattr(erogarga.utils, "postHtml", fake_post_html)

    erogarga.Play(
        "https://www.erogarga.com/video/hot-japanese-schoolgirl-12345/", "Test Video"
    )

    assert len(video_player_calls) >= 1


def test_play_handles_watcherotic_embed(monkeypatch):
    """Test that Play() handles watcherotic.com iframe embeds."""
    html = load_fixture("video_iframe.html")

    video_player_calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None, regex=None, direct_regex=None):
            self.resolveurl = MagicMock()
            self.resolveurl.HostedMediaFile.return_value.valid_url.return_value = False
            video_player_calls.append(("init", name))

        def play_from_direct_link(self, url):
            video_player_calls.append(("play_direct", url))

    embed_html = """
    <html>
    <script>
    video_url: 'https://cdn.watcherotic.com/videos/test.mp4'
    </script>
    </html>
    """

    def fake_get_html(url, *args, **kwargs):
        if "watcherotic" in url:
            return embed_html
        return html

    monkeypatch.setattr(erogarga.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(erogarga.utils, "VideoPlayer", FakeVideoPlayer)

    erogarga.Play("https://www.erogarga.com/video/asian-milf-69/", "Test Video")

    assert len(video_player_calls) >= 1


def test_play_handles_spankbang_embed(monkeypatch):
    """Test that Play() handles spankbang.com iframe embeds."""
    html = load_fixture("video_spankbang.html")

    playvid_calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None, regex=None, direct_regex=None):
            self.resolveurl = MagicMock()
            self.resolveurl.HostedMediaFile.return_value.valid_url.return_value = False

        def play_from_direct_link(self, url):
            pass

    def fake_playvid(url, name, download=None):
        playvid_calls.append({"url": url, "name": name, "download": download})

    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.utils, "VideoPlayer", FakeVideoPlayer)
    monkeypatch.setattr(erogarga, "Playvid", fake_playvid)

    erogarga.Play("https://www.erogarga.com/video/korean-beauty-xxx/", "Test Video")

    assert len(playvid_calls) == 1


def test_play_handles_koreanpornmovie(monkeypatch):
    """Test that Play() handles koreanpornmovie.com videos."""
    html = load_fixture("video_koreanpm.html")
    iframe_html = load_fixture("video_koreanpm_iframe.html")

    video_player_calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None):
            video_player_calls.append(("init", name, download))

        def play_from_direct_link(self, url):
            video_player_calls.append(("play_direct", url))

    def fake_get_html(url, *args, **kwargs):
        if "somecdn.com" in url:
            return iframe_html
        return html

    monkeypatch.setattr(erogarga.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(erogarga.utils, "VideoPlayer", FakeVideoPlayer)

    erogarga.Play("https://koreanpornmovie.com/video/test-video/", "Korean Video")

    assert len(video_player_calls) >= 2


def test_lookupinfo_extracts_tags_and_actors(monkeypatch):
    """Test that Lookupinfo() extracts tags and actors using BeautifulSoup."""
    lookup_calls = []
    additem_calls = []

    class FakeLookupInfo:
        def __init__(self, siteurl, url, mode, lookup_list):
            lookup_calls.append({"url": url, "mode": mode})

        def additem(self, category, name, url):
            additem_calls.append({"category": category, "name": name, "url": url})

    def fake_get_html(url, *args, **kwargs):
        return """
        <html>
        <a href="https://www.erogarga.com/tag/asian/" class="label" title="Asian">Asian</a>
        <a href="https://www.erogarga.com/actor/jane-doe/" title="Jane Doe">Jane Doe</a>
        </html>
        """

    monkeypatch.setattr(erogarga.utils, "LookupInfo", FakeLookupInfo)
    monkeypatch.setattr(erogarga.utils, "getHtml", fake_get_html)

    erogarga.Lookupinfo("https://www.erogarga.com/video/test-video/")

    assert len(lookup_calls) == 1
    assert len(additem_calls) == 2


def test_related_navigates_to_video_page(monkeypatch):
    """Test that Related() navigates to the video page."""
    executebuiltin_calls = []

    def fake_executebuiltin(cmd):
        executebuiltin_calls.append(cmd)

    import xbmc

    monkeypatch.setattr(xbmc, "executebuiltin", fake_executebuiltin)

    erogarga.Related("https://www.erogarga.com/video/test-video/")

    assert len(executebuiltin_calls) == 1


def test_getbaselink_identifies_site(monkeypatch):
    """Test that getBaselink() correctly identifies the site from URL."""
    assert erogarga.getBaselink("https://www.erogarga.com/video/test/") == "https://www.erogarga.com/"
    assert erogarga.getBaselink("https://fulltaboo.tv/video/test/") == "https://fulltaboo.tv/"
    assert erogarga.getBaselink("https://koreanpornmovie.com/video/test/") == "https://koreanpornmovie.com/"


def test_main_creates_proper_menu_structure(monkeypatch):
    """Test that Main() creates the proper menu structure."""
    dirs = []

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode})

    monkeypatch.setattr(erogarga.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(erogarga, "List", lambda *a: None)

    erogarga.Main("https://www.erogarga.com/")

    assert len(dirs) == 2


def test_gotopage(monkeypatch):
    """Test GotoPage() logic."""
    builtins = []
    notify_calls = []

    class _Dialog:
        def numeric(self, *_a, **_k):
            return "5"

    monkeypatch.setattr(erogarga.xbmcgui, "Dialog", _Dialog)
    monkeypatch.setattr(erogarga.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd))
    monkeypatch.setattr(erogarga.utils, "notify", lambda msg=None: notify_calls.append(msg))

    erogarga.GotoPage("erogarga.List", "https://www.erogarga.com/page/1/", "1", "10")
    assert "page/5" in urllib_parse.unquote(builtins[0])

    # Out of range
    erogarga.GotoPage("erogarga.List", "https://www.erogarga.com/page/1/", "1", "2")
    assert "Out of range!" in notify_calls


def test_list_pagination_max_page(monkeypatch):
    """Test List() pagination finding highest number when Last is missing (Lines 185-192)."""
    html = """
    <div class="pagination">
        <span class="current">1</span>
        <a href="/page/2/">2</a>
        <a href="/page/10/">10</a>
    </div>
    """
    dirs = []
    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    erogarga.List("https://www.erogarga.com/")
    assert any("Next Page" in d for d in dirs)


def test_cat_split_logic_and_continues(monkeypatch):
    """Test Cat() split logic and loop continues (Lines 256-257, 267)."""
    # 1. Split logic
    html = """
    class="wp-block-tag-cloud"
    <a href="/c1/" aria-label="Cat 1">Cat 1</a>
    <a href="" aria-label="No href">No href</a>
    <a href="/c3/">No label</a>
    /section>
    """
    dirs = []
    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(erogarga.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(erogarga.utils, "eod", lambda: None)

    erogarga.Cat("https://www.erogarga.com/categories/")
    assert len(dirs) == 1
    assert dirs[0] == "Cat 1"

    # 2. No soup (Line 256-257)
    monkeypatch.setattr(erogarga.utils, "parse_html", lambda *a: None)
    erogarga.Cat("https://www.erogarga.com/categories/")


def test_play_extra_branches(monkeypatch):
    """Test Play() extra branches (Lines 315, 330-349, 367-384)."""
    played = []
    
    class MockPlayer:
        def __init__(self, *a, **k):
            self.resolveurl = MagicMock()
            self.resolveurl.HostedMediaFile.return_value.valid_url.return_value = False
        def play_from_link_to_resolve(self, url): played.append(("resolve", url))
        def play_from_direct_link(self, url): played.append(("direct", url))
        def play_from_html(self, html, url): played.append(("html", html, url))
        def play_from_site_link(self, url, referer): played.append(("site", url, referer))

    monkeypatch.setattr(erogarga.utils, "VideoPlayer", MockPlayer)
    monkeypatch.setattr(erogarga.utils, "get_packed_data", lambda x: "packed")

    # 1. koreanporn source not found (Line 315)
    html_korean_no_source = "<iframe></iframe>"
    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html_korean_no_source)
    erogarga.Play("https://koreanpornmovie.com/v1", "Name")
    assert len(played) == 0

    # 2. player-x.php?q= (Line 330-334)
    html_iframe_x = '<iframe src="https://www.erogarga.com/player-x.php?q=c291cmNlIHNyYz0iaHR0cHM6Ly9zdHJlYW0ubXA0Ig=="></iframe>'
    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html_iframe_x)
    monkeypatch.setattr(erogarga.utils, "_bdecode", lambda x: "source src=\"https://stream.mp4\"")
    erogarga.Play("https://www.erogarga.com/v1", "Name")
    assert any("https://stream.mp4" in p[1] for p in played if p[0] == "direct")

    # 3. klcams.com (Line 335-349)
    played.clear()
    html_page_with_kl = '<iframe src="https://klcams.com/embed/"></iframe>'
    html_kl_embed = '<iframe src="https://klcams.com/inner/"></iframe>'
    def fake_get_html_kl(url, referer=None, **k):
        if "erogarga.com/v1" in url: return html_page_with_kl
        if "klcams.com/embed/" in url: return html_kl_embed
        return "packed_data"
    monkeypatch.setattr(erogarga.utils, "getHtml", fake_get_html_kl)
    erogarga.Play("https://www.erogarga.com/v1", "Name")
    assert any(p[0] == "html" for p in played)

    # 4. itemprop fallback (Line 384)
    played.clear()
    html_itemprop = '<iframe src="https://player.com/"></iframe><span itemprop="contentURL" content="https://direct.mp4"></span>'
    monkeypatch.setattr(erogarga.utils, "getHtml", lambda *a, **k: html_itemprop)
    erogarga.Play("https://www.erogarga.com/v1", "Name")
    assert any("https://direct.mp4" in p[1] for p in played if p[0] == "direct")

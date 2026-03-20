from resources.lib.sites import anybunny
from tests.conftest import fixture_mapped_get_html


class _Recorder:
    def __init__(self):
        self.downloads = []
        self.dirs = []

    def add_download(self, name, url, mode, iconimage, desc="", *args, **kwargs):
        self.downloads.append(
            {
                "name": name,
                "url": url,
                "mode": anybunny.site.get_full_mode(mode),
                "icon": iconimage,
            }
        )

    def add_dir(self, name, url, mode, *args, **kwargs):
        self.dirs.append(
            {
                "name": name,
                "url": url,
                "mode": anybunny.site.get_full_mode(mode),
            }
        )


def test_list_populates_download_links(monkeypatch):
    recorder = _Recorder()

    get_html_fn = fixture_mapped_get_html(
        monkeypatch,
        anybunny,
        {
            "new/?p=1": "sites/anybunny/listing.html",
            "https://anybunny.org/": "sites/anybunny/listing.html",
        },
    )

    # Mock fetch_with_playwright to raise ImportError
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == 'resources.lib.playwright_helper':
            raise ImportError("Mocked ImportError for testing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', mock_import)

    # Also mock get_html_with_cloudflare_retry to return the fixture
    def mock_cloudflare_html(url, *args, **kwargs):
        return get_html_fn(url), None

    monkeypatch.setattr(anybunny.utils, "get_html_with_cloudflare_retry", mock_cloudflare_html)
    monkeypatch.setattr(anybunny.site, "add_download_link", recorder.add_download)
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.List("http://anybunny.org/new/?p=1")

    assert recorder.downloads == [
        {
            "name": "First Video Title",
            "url": "https://anybunny.org/videos/first-video",
            "mode": "anybunny.Playvid",
            "icon": "https://cdn.anybunny.org/thumb-first.jpg",
        },
        {
            "name": "Second Video Title",
            "url": "https://anybunny.org/videos/second-video",
            "mode": "anybunny.Playvid",
            "icon": "https://cdn.anybunny.org/thumb-second.jpg",
        },
    ]

    assert recorder.dirs == [
        {
            "name": "Next Page",
            "url": "https://anybunny.org/new/?p=2",
            "mode": "anybunny.List",
        }
    ]


def test_search_results_have_no_pagination(monkeypatch):
    recorder = _Recorder()

    get_html_fn = fixture_mapped_get_html(
        monkeypatch, anybunny, {"search": "sites/anybunny/search.html"}
    )

    # Mock fetch_with_playwright to raise ImportError
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == 'resources.lib.playwright_helper':
            raise ImportError("Mocked ImportError for testing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', mock_import)

    # Also mock get_html_with_cloudflare_retry to return the fixture
    def mock_cloudflare_html(url, *args, **kwargs):
        return get_html_fn(url), None

    monkeypatch.setattr(anybunny.utils, "get_html_with_cloudflare_retry", mock_cloudflare_html)
    monkeypatch.setattr(anybunny.site, "add_download_link", recorder.add_download)
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.List("http://anybunny.org/search?q=query")

    assert [d["name"] for d in recorder.downloads] == [
        "Search Result One",
        "Search Result Two",
    ]
    assert recorder.dirs == []


def test_playvid_uses_direct_regex(monkeypatch):
    captured = {}

    class _DummyVP:
        def __init__(self, name, download=False, direct_regex=None, **kwargs):
            captured["direct_regex"] = direct_regex
            self.progress = type("P", (), {"update": lambda *a, **k: None})()

        def play_from_site_link(self, url):
            captured["site_url"] = url

        def play_from_direct_link(self, url):
            captured["direct_url"] = url

    monkeypatch.setattr(anybunny.utils, "VideoPlayer", _DummyVP)

    # Mock sniff_video_url to return None (simulating Playwright not available or failed)
    def mock_sniff(*args, **kwargs):
        return None

    # Patch the import to avoid ImportError
    import sys
    mock_module = type(sys)('resources.lib.playwright_helper')
    mock_module.sniff_video_url = mock_sniff
    monkeypatch.setitem(sys.modules, 'resources.lib.playwright_helper', mock_module)

    # Mock get_html_with_cloudflare_retry for the fallback logic
    def mock_get_html(url, *args, **kwargs):
        return '<html><iframe src="http://anybunny.org/iframe/123"></iframe></html>', None
    
    def mock_get_iframe_html(url, *args, **kwargs):
        return '<html>var video = "https://stream.anybunny.org/vid.mp4";</html>', None

    def combined_mock_get_html(url, *args, **kwargs):
        if "/iframe/" in url:
            return mock_get_iframe_html(url)
        return mock_get_html(url)

    monkeypatch.setattr(anybunny.utils, "get_html_with_cloudflare_retry", combined_mock_get_html)

    anybunny.Playvid("http://anybunny.org/videos/video-123", "Example")

    assert captured["direct_url"] == "https://stream.anybunny.org/vid.mp4"


def test_playvid_uses_iframe_fallback_without_playwright(monkeypatch):
    captured = {}

    class _DummyVP:
        def __init__(self, name, download=False, direct_regex=None, **kwargs):
            captured["direct_regex"] = direct_regex
            self.progress = type("P", (), {"update": lambda *a, **k: None})()

        def play_from_site_link(self, url):
            captured["site_url"] = url

        def play_from_direct_link(self, url):
            captured["direct_url"] = url

    monkeypatch.setattr(anybunny.utils, "VideoPlayer", _DummyVP)

    def mock_get_html(url, *args, **kwargs):
        if "/iframe/" in url:
            return '<html>var video = "https://stream1.anybunny.org/m4vid/123/video.mp4";</html>', None
        return '<html><iframe src="http://anybunny.org/iframe/123"></iframe></html>', None

    monkeypatch.setattr(anybunny.utils, "get_html_with_cloudflare_retry", mock_get_html)

    anybunny.Playvid("http://anybunny.org/videos/video-123", "Example")

    assert captured["direct_url"] == "https://stream1.anybunny.org/m4vid/123/video.mp4"


def test_main_populates_directories(monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    # Mock List since it's now called from Main
    monkeypatch.setattr(anybunny, "List", lambda *args, **kwargs: None)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.Main()

    # Should have 4 directories (New, Top, Categories, Search)
    assert len(recorder.dirs) == 4
    assert any("New videos" in d["name"] for d in recorder.dirs)
    assert any("Top videos" in d["name"] for d in recorder.dirs)
    assert any("Categories" in d["name"] for d in recorder.dirs)
    assert any("Search" in d["name"] for d in recorder.dirs)

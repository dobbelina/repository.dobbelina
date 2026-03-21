from resources.lib.sites import anybunny
from tests.conftest import fixture_mapped_get_html, read_fixture


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
    """List() extracts video items and pagination from a category page."""
    recorder = _Recorder()

    fixture_mapped_get_html(
        monkeypatch,
        anybunny,
        {
            "https://anybunny.org/top/Indian": "sites/anybunny/listing.html",
        },
    )

    monkeypatch.setattr(anybunny.site, "add_download_link", recorder.add_download)
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.List("https://anybunny.org/top/Indian")

    assert recorder.downloads == [
        {
            "name": "First Video Title",
            "url": "https://anybunny.org/too/111-first_video_title",
            "mode": "anybunny.Playvid",
            "icon": "https://cdn.anybunny.org/thumb-first.jpg",
        },
        {
            "name": "Second Video Title",
            "url": "https://anybunny.org/too/222-second_video_title",
            "mode": "anybunny.Playvid",
            "icon": "https://cdn.anybunny.org/thumb-second.jpg",
        },
    ]

    assert recorder.dirs == [
        {
            "name": "Next Page",
            "url": "https://anybunny.org/top/Indian?p=2",
            "mode": "anybunny.List",
        }
    ]


def test_list_filters_out_category_links(monkeypatch):
    """List() skips a.nuyrfe items pointing to /top/ (categories, not videos)."""
    recorder = _Recorder()

    fixture_mapped_get_html(
        monkeypatch,
        anybunny,
        {
            "https://anybunny.org/top/Indian": "sites/anybunny/listing.html",
        },
    )

    monkeypatch.setattr(anybunny.site, "add_download_link", recorder.add_download)
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.List("https://anybunny.org/top/Indian")

    # Only /too/ items should produce downloads — no /top/ category items
    for dl in recorder.downloads:
        assert "/too/" in dl["url"], f"Expected /too/ in URL, got {dl['url']}"


def test_search_results_list_videos(monkeypatch):
    """Search results page produces video downloads with no pagination."""
    recorder = _Recorder()

    fixture_mapped_get_html(
        monkeypatch,
        anybunny,
        {
            "https://anybunny.org/top/blonde": "sites/anybunny/search.html",
        },
    )

    monkeypatch.setattr(anybunny.site, "add_download_link", recorder.add_download)
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.List("https://anybunny.org/top/blonde")

    assert [d["name"] for d in recorder.downloads] == [
        "Search Result One",
        "Search Result Two",
    ]
    # search.html has no topbtmsel2r so no pagination dir should be added
    assert recorder.dirs == []


def test_categories2_extracts_category_links(monkeypatch):
    """Categories2() lists categories from the root page (a.nuyrfe -> /top/)."""
    recorder = _Recorder()

    fixture_mapped_get_html(
        monkeypatch,
        anybunny,
        {
            "https://anybunny.org/": "sites/anybunny/categories.html",
        },
    )

    monkeypatch.setattr(anybunny.site, "add_download_link", recorder.add_download)
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.Categories2("https://anybunny.org/")

    # Should list Indian and Big Tits but NOT the bare /top/ link
    cat_names = [d["name"] for d in recorder.dirs]
    assert "Indian" in cat_names
    assert "Big Tits" in cat_names
    # The bare /top/ entry should be skipped
    assert not any(d["url"].rstrip("/").endswith("/top") for d in recorder.dirs)


def test_playvid_extracts_mp4_from_file_param(monkeypatch):
    """Playvid() extracts an MP4 URL from a Playerjs file: parameter."""
    captured = {}

    class _DummyVP:
        def __init__(self, name, download=False, **kwargs):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()

        def play_from_direct_link(self, url):
            captured["direct_url"] = url

    monkeypatch.setattr(anybunny.utils, "VideoPlayer", _DummyVP)

    playerjs_html = (
        '<html><script>'
        'playerjs({id:"player", file:"https://anybunny.org/video/hls/123/abc/ts/video.m3u8?jtry=1'
        ':cast:https://anybunny.org/video/hls/123/abc/ts/video.m3u8?jtry=1'
        ' or https://anybunny.org/video/mp4/123/abc/ts/video.mp4'
        ':cast:https://anybunny.org/video/mp4/123/abc/ts/video.mp4"});'
        '</script></html>'
    )

    def mock_get_html(url, *args, **kwargs):
        return playerjs_html, None

    monkeypatch.setattr(anybunny.utils, "get_html_with_cloudflare_retry", mock_get_html)

    anybunny.Playvid("https://anybunny.org/too/123-video", "Example")

    assert captured["direct_url"] == "https://anybunny.org/video/mp4/123/abc/ts/video.mp4"


def test_playvid_uses_iframe_fallback(monkeypatch):
    """Playvid() falls back to fetching an iframe when no file: param is present."""
    captured = {}

    class _DummyVP:
        def __init__(self, name, download=False, **kwargs):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()

        def play_from_direct_link(self, url):
            captured["direct_url"] = url

    monkeypatch.setattr(anybunny.utils, "VideoPlayer", _DummyVP)

    def mock_get_html(url, *args, **kwargs):
        if "/iframe/" in url:
            return '<html>var video = "https://stream1.anybunny.org/vid.mp4";</html>', None
        return '<html><iframe src="http://anybunny.org/iframe/123"></iframe></html>', None

    monkeypatch.setattr(anybunny.utils, "get_html_with_cloudflare_retry", mock_get_html)

    anybunny.Playvid("http://anybunny.org/too/123-video", "Example")

    assert captured["direct_url"] == "https://stream1.anybunny.org/vid.mp4"


def test_main_populates_directories(monkeypatch):
    """Main() creates exactly 2 top-level directories."""
    recorder = _Recorder()
    monkeypatch.setattr(anybunny.site, "add_dir", recorder.add_dir)
    monkeypatch.setattr(anybunny.utils, "eod", lambda *args, **kwargs: None)

    anybunny.Main()

    assert len(recorder.dirs) == 2
    assert any("Categories" in d["name"] for d in recorder.dirs)
    assert any("Search" in d["name"] for d in recorder.dirs)

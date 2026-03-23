from pathlib import Path

from resources.lib.sites import porntn


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "porntn"


def load_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_items_and_next(monkeypatch):
    html = load_fixture("list.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(porntn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    monkeypatch.setattr(porntn.utils, "eod", lambda: None)
    monkeypatch.setattr(
        porntn.site,
        "add_download_link",
        lambda name,
        url,
        mode,
        iconimage,
        desc="",
        contextm=None,
        duration="",
        **kwargs: downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": duration,
                "contextm": contextm,
            }
        ),
    )
    monkeypatch.setattr(
        porntn.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    porntn.List(
        "https://porntn.com/?mode=async&function=get_block&block_id=list_videos_most_recent_videos&sort_by=post_date&from=1",
        1,
    )

    assert len(downloads) == 3
    assert downloads[0]["name"] == "Video One"
    assert downloads[0]["url"] == "https://porntn.com/video-one"
    assert downloads[0]["duration"] == "10:01"
    assert downloads[1]["url"] == "https://porntn.com/video-two"
    assert downloads[2]["icon"].endswith("/images/3.jpg")
    assert downloads[0]["contextm"] is not None

    next_entries = [d for d in dirs if d["mode"] == "List"]
    assert len(next_entries) == 1
    assert "31" in next_entries[0]["name"]
    assert "from=31" in next_entries[0]["url"]


def test_categories(monkeypatch):
    html = load_fixture("categories.html")
    dirs = []

    monkeypatch.setattr(porntn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    monkeypatch.setattr(porntn.utils, "eod", lambda: None)
    monkeypatch.setattr(
        porntn.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    porntn.Categories(
        "https://porntn.com/new/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title"
    )

    assert len(dirs) == 2
    assert dirs[0]["name"] == "Anal [COLOR hotpink](12)[/COLOR]"
    assert dirs[0]["url"].endswith("from=1")
    assert dirs[1]["url"].startswith("/categories/teen")


def test_tags(monkeypatch):
    html = load_fixture("tags.html")
    dirs = []

    monkeypatch.setattr(porntn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    monkeypatch.setattr(porntn.utils, "eod", lambda: None)
    monkeypatch.setattr(
        porntn.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    porntn.Tags("https://porntn.com/tags/")

    assert len(dirs) == 2
    assert dirs[0]["name"] == "Amateur"
    assert dirs[0]["url"].startswith("https://porntn.com/tags/amateur")
    assert "common_videos_list" in dirs[1]["url"]


def test_playvid_uses_kt_helper_for_kvs_pages(monkeypatch):
    html = """
    <script>
    license_code: '12345'
    video_url: 'function/0/https://cdn.example.com/video.mp4', video_url_text: '720p'
    </script>
    """
    calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None):
            self.progress = type(
                "p",
                (),
                {
                    "update": lambda *args, **kwargs: None,
                    "close": lambda *args, **kwargs: None,
                },
            )()

        def play_from_kt_player(self, page_html, referer=None):
            calls.append((page_html, referer))

        def play_from_html(self, html):
            calls.append(("html", html))

    monkeypatch.setattr(
        porntn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False)
    )
    monkeypatch.setattr(porntn.utils, "VideoPlayer", FakeVideoPlayer)

    porntn.Playvid("https://porntn.com/video/test", "Test Video")

    assert calls == [(html, "https://porntn.com/video/test")]


def test_playvid_passes_url_to_html_fallback_without_license(monkeypatch):
    html = "<html><div>fallback player markup</div></html>"
    calls = []

    class FakeVideoPlayer:
        def __init__(self, name, download=None):
            self.progress = type(
                "p",
                (),
                {
                    "update": lambda *args, **kwargs: None,
                    "close": lambda *args, **kwargs: None,
                },
            )()

        def play_from_html(self, page_html, page_url=None):
            calls.append((page_html, page_url))

    monkeypatch.setattr(
        porntn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False)
    )
    monkeypatch.setattr(porntn.utils, "VideoPlayer", FakeVideoPlayer)

    porntn.Playvid("https://porntn.com/video/fallback", "Fallback")

    assert calls == [(html, "https://porntn.com/video/fallback")]

from pathlib import Path
from unittest.mock import MagicMock

import pytest


from resources.lib.sites import pornkai


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "pornkai"


def load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("fixture_name", ["list_response.json"])
def test_list_parses_videos_and_pagination(monkeypatch, fixture_name):
    html = load_fixture(fixture_name)
    monkeypatch.setattr(pornkai.utils, "getHtml", lambda url, referer=None: html)

    downloads = []
    dirs = []

    def fake_add_download_link(
        name,
        url,
        mode,
        iconimage,
        desc="",
        stream=None,
        fav="add",
        noDownload=False,
        contextm=None,
        fanart=None,
        duration="",
        quality="",
    ):
        downloads.append(
            {
                "name": name,
                "url": url,
                "icon": iconimage,
                "duration": duration,
                "context": contextm,
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode, "icon": iconimage})

    monkeypatch.setattr(pornkai.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornkai.site, "add_dir", fake_add_dir)

    pornkai.List("https://pornkai.com/api?query=_best&sort=new&page=0&method=search")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Video One"
    assert downloads[0]["url"] == "https://pornkai.com/videos/12345"
    assert downloads[0]["duration"] == "12:34"
    assert downloads[0]["context"][0][0].startswith("[COLOR violet]Related videos")

    assert downloads[1]["name"] == "Video Two Title"
    assert downloads[1]["icon"] == "https://cdn.example.com/thumb2.jpg"

    next_pages = [entry for entry in dirs if "Next Page" in entry["name"]]
    assert next_pages, "Expected a Next Page entry to be added"
    assert "2/3" in next_pages[0]["name"]
    assert "page=1" in next_pages[0]["url"]


def test_list_handles_missing_results_remaining(monkeypatch):
    html = load_fixture("list_no_results.json")
    monkeypatch.setattr(pornkai.utils, "getHtml", lambda url, referer=None: html)

    dirs = []
    downloads = []

    def fake_add_download_link(
        name,
        url,
        mode,
        iconimage,
        desc="",
        stream=None,
        fav="add",
        noDownload=False,
        contextm=None,
        fanart=None,
        duration="",
        quality="",
    ):
        downloads.append(name)

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        dirs.append(name)

    monkeypatch.setattr(pornkai.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornkai.site, "add_dir", fake_add_dir)

    pornkai.List("https://pornkai.com/api?query=_best&sort=new&page=3&method=search")

    assert downloads == ["Solo Clip"]
    assert all("Next Page" not in entry for entry in dirs)


def test_categories_parse_links(monkeypatch):
    html = load_fixture("categories.html")
    monkeypatch.setattr(pornkai.utils, "getHtml", lambda url, referer=None: html)

    dirs = []

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        dirs.append({"name": name, "url": url, "icon": iconimage})

    monkeypatch.setattr(pornkai.site, "add_dir", fake_add_dir)

    pornkai.Categories("https://pornkai.com/all-categories")

    assert len(dirs) == 2
    assert dirs[0]["name"] == "Amateur"
    assert (
        dirs[0]["url"]
        == "https://pornkai.com/api?query=amateur&sort=best&page=0&method=search"
    )
    assert dirs[0]["icon"] == "https://cdn.example.com/cat1.jpg"

    assert dirs[1]["name"] == "MILF"
    assert (
        dirs[1]["url"]
        == "https://pornkai.com/api?query=milf&sort=best&page=0&method=search"
    )


def test_main_uses_html_feed_url(monkeypatch):
    list_calls = []

    monkeypatch.setattr(pornkai, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(pornkai.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(pornkai.utils, "eod", lambda: None)

    pornkai.Main()

    assert list_calls
    assert "videos?q=&sort=new&page=1" in list_calls[0]


def test_list_prefers_video_title_over_duration(monkeypatch):
    html = """
    {"html":"<div class=\\"thumbnail\\"><div class=\\"thumbnail_inner\\">\
<a class=\\"thumbnail_link th_derp trigger_pop\\" href=\\"/view?key=xv123\\">\
<span class=\\"trigger_pop th_wrap\\"><div class=\\"thumbnail_video_length\\">6:09</div></span></a>\
<div class=\\"vidinfo\\"><a href=\\"/view?key=xv123\\" class=\\"thumbnail_title thumbnail_link trigger_pop\\">\
<span class=\\"trigger_pop th_wrap\\">Actual Video Title</span></a></div></div></div>","results_remaining":0}
    """.strip()
    monkeypatch.setattr(pornkai.utils, "getHtml", lambda url, referer=None: html)

    downloads = []
    monkeypatch.setattr(
        pornkai.site,
        "add_download_link",
        lambda name, *a, **k: downloads.append(name),
    )
    monkeypatch.setattr(pornkai.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(pornkai.utils, "eod", lambda: None)

    pornkai.List("https://pornkai.com/api?query=public&sort=best&page=0&method=search")

    assert downloads == ["Actual Video Title"]


def test_list_filters_categories_and_cam_entries(monkeypatch):
    html = """
    {"html":"<div class=\\"thumbnail\\"><a class=\\"thumbnail_link\\" href=\\"/videos/12345\\"><span class=\\"trigger_pop th_wrap\\">Playable Video</span></a></div>\
<div class=\\"thumbnail\\"><a class=\\"thumbnail_link\\" href=\\"/videos?q=amateur\\"><span class=\\"trigger_pop th_wrap\\">Amateur</span></a></div>\
<div class=\\"thumbnail\\"><a class=\\"thumbnail_link\\" href=\\"/cam?model=tester\\"><span class=\\"trigger_pop th_wrap\\">Live Model</span></a></div>","results_remaining":0}
    """.strip()
    monkeypatch.setattr(pornkai.utils, "getHtml", lambda url, referer=None: html)

    downloads = []
    monkeypatch.setattr(
        pornkai.site,
        "add_download_link",
        lambda name, url, *a, **k: downloads.append((name, url)),
    )
    monkeypatch.setattr(pornkai.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(pornkai.utils, "eod", lambda: None)

    pornkai.List("https://pornkai.com/videos?q=&sort=new&page=1")

    assert downloads == [("Playable Video", "https://pornkai.com/videos/12345")]


def test_playvid_falls_back_to_html_parser(monkeypatch):
    html = "<html><body><video src='https://cdn.example/video.mp4'></video></body></html>"
    played = {}

    class MockPlayer:
        def __init__(self, *args, **kwargs):
            self.progress = MagicMock()

        def play_from_link_to_resolve(self, url):
            raise AssertionError("unexpected direct resolve path")

        def play_from_html(self, markup, url=None):
            played["markup"] = markup
            played["url"] = url

    monkeypatch.setattr(pornkai.utils, "getHtml", lambda url, referer=None: html)
    monkeypatch.setattr(pornkai.utils, "VideoPlayer", MockPlayer)

    pornkai.Playvid("https://pornkai.com/videos/12345", "Name")

    assert played == {"markup": html, "url": "https://pornkai.com/videos/12345"}

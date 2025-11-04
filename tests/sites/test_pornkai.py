import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = ROOT / "plugin.video.cumination"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

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

    def fake_add_download_link(name, url, mode, iconimage, desc="", stream=None, fav='add',
                                noDownload=False, contextm=None, fanart=None, duration="", quality=""):
        downloads.append({
            "name": name,
            "url": url,
            "icon": iconimage,
            "duration": duration,
            "context": contextm,
        })

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode, "icon": iconimage})

    monkeypatch.setattr(pornkai.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornkai.site, "add_dir", fake_add_dir)

    pornkai.List("https://pornkai.com/api?query=_best&sort=new&page=0&method=search")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Video One"
    assert downloads[0]["url"] == "https://pornkai.com/videos/12345"
    assert downloads[0]["duration"] == "12:34"
    assert downloads[0]["context"][0][0].startswith('[COLOR violet]Related videos')

    assert downloads[1]["name"] == "Video Two"
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

    def fake_add_download_link(name, url, mode, iconimage, desc="", stream=None, fav='add',
                                noDownload=False, contextm=None, fanart=None, duration="", quality=""):
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
    assert dirs[0]["url"] == "https://pornkai.com/api?query=amateur&sort=best&page=0&method=search"
    assert dirs[0]["icon"] == "https://cdn.example.com/cat1.jpg"

    assert dirs[1]["name"] == "MILF"
    assert dirs[1]["url"] == "https://pornkai.com/api?query=milf&sort=best&page=0&method=search"

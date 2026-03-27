"""Tests for aagmaal.farm (aagmaalpro) site implementation."""

from pathlib import Path

from resources.lib.sites import aagmaalpro


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "aagmaalpro"


def load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_recent_items(monkeypatch):
    """Test that List correctly parses div.recent-item entries."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    monkeypatch.setattr(aagmaalpro.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaalpro.site, "add_download_link",
                        lambda name, url, mode, icon, desc="", **k: downloads.append({"name": name, "url": url, "icon": icon}))
    monkeypatch.setattr(aagmaalpro.site, "add_dir",
                        lambda name, url, mode, icon=None, **k: dirs.append({"name": name, "url": url}))
    monkeypatch.setattr(aagmaalpro.utils, "eod", lambda: None)

    aagmaalpro.List("https://aagmaal.farm/")

    assert len(downloads) == 3
    assert downloads[0]["name"] == "Hot Desi Girl Strip Show"
    assert downloads[0]["url"] == "https://aagmaal.dog/hot-desi-girl-strip-show/"
    assert downloads[0]["icon"] == "https://aagmaal.dog/thumbs/thumb1.jpg"
    assert downloads[1]["name"] == "Indian Wife Shared"
    assert downloads[2]["name"] == "Desi College Couple"

    # Pagination
    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "Page 1 of 1124" in dirs[0]["name"]
    assert dirs[0]["url"] == "https://aagmaal.dog/page/2/"


def test_list_handles_no_pagination(monkeypatch):
    """Test that List handles pages without pagination."""
    html = """<html><body>
    <div class="recent-item">
        <div class="post-thumbnail">
            <a href="https://aagmaal.dog/test/" rel="bookmark">
                <img src="thumb.jpg" title="Test Video" alt="Test Video"/>
            </a>
        </div>
        <h3 class="post-box-title">
            <a href="https://aagmaal.dog/test/">Test Video</a>
        </h3>
    </div>
    </body></html>"""

    downloads = []
    dirs = []

    monkeypatch.setattr(aagmaalpro.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaalpro.site, "add_download_link",
                        lambda *a, **k: downloads.append(a[0]))
    monkeypatch.setattr(aagmaalpro.site, "add_dir",
                        lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(aagmaalpro.utils, "eod", lambda: None)

    aagmaalpro.List("https://aagmaal.farm/")

    assert len(downloads) == 1
    assert len(dirs) == 0


def test_categories_parses_cat_items(monkeypatch):
    """Test that Categories correctly parses li.cat-item links."""
    html = load_fixture("categories.html")

    dirs = []

    monkeypatch.setattr(aagmaalpro.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaalpro.site, "add_dir",
                        lambda name, url, mode, icon=None, **k: dirs.append({"name": name, "url": url, "mode": mode}))
    monkeypatch.setattr(aagmaalpro.utils, "eod", lambda: None)

    aagmaalpro.Categories("https://aagmaal.farm/")

    assert len(dirs) == 4
    assert dirs[0]["name"] == "Desi Videos"
    assert dirs[0]["url"] == "https://aagmaal.dog/category/desi/"
    assert "List2" in dirs[0]["mode"]
    assert dirs[1]["name"] == "Bhabhi"
    assert dirs[2]["name"] == "Leaked MMS"
    assert dirs[3]["name"] == "Punjabi"


def test_list2_parses_article_title_divs(monkeypatch):
    """Test that List2 correctly parses articles with title divs."""
    html = """<html><body>
    <article>
        <div class="title">
            <a href="https://aagmaal.dog/cat/video1/">Category Video 1</a>
        </div>
        <img src="thumb1.jpg">
    </article>
    <article>
        <h2 class="title">
            <a href="https://aagmaal.dog/cat/video2/">Category Video 2</a>
        </h2>
        <img data-src="thumb2.jpg">
    </article>
    </body></html>"""

    downloads = []

    monkeypatch.setattr(aagmaalpro.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaalpro.site, "add_download_link",
                        lambda *a, **k: downloads.append(a[0]))
    monkeypatch.setattr(aagmaalpro.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(aagmaalpro.utils, "eod", lambda: None)

    aagmaalpro.List2("https://aagmaal.dog/category/desi/")

    assert len(downloads) == 2
    assert downloads[0] == "Category Video 1"
    assert downloads[1] == "Category Video 2"


def test_search_without_keyword(monkeypatch):
    """Test that Search without keyword shows search input dialog."""
    search_called = []
    monkeypatch.setattr(aagmaalpro.site, "search_dir",
                        lambda url, mode: search_called.append(mode))

    aagmaalpro.Search("https://aagmaal.farm/?s=")

    assert len(search_called) == 1
    assert search_called[0] == "Search"


def test_search_with_keyword_calls_list2(monkeypatch):
    """Test that Search with keyword calls List2."""
    list2_calls = []
    monkeypatch.setattr(aagmaalpro, "List2", lambda url: list2_calls.append(url))

    aagmaalpro.Search("https://aagmaal.farm/?s=", keyword="desi bhabhi")

    assert len(list2_calls) == 1
    assert "desi+bhabhi" in list2_calls[0]

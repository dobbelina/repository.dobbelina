"""Tests for aagmaal.bz site implementation."""

from pathlib import Path

from resources.lib.sites import aagmaal


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "aagmaal"


def load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_vp_card_articles(monkeypatch):
    """Test that List correctly parses article.vp-card items."""
    html = load_fixture("listing.html")

    downloads = []
    dirs = []

    monkeypatch.setattr(aagmaal.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaal.site, "add_download_link",
                        lambda name, url, mode, icon, desc="", **k: downloads.append({"name": name, "url": url, "icon": icon}))
    monkeypatch.setattr(aagmaal.site, "add_dir",
                        lambda name, url, mode, icon=None, **k: dirs.append({"name": name, "url": url}))
    monkeypatch.setattr(aagmaal.utils, "eod", lambda: None)

    aagmaal.List("https://aagmaal.bz/")

    assert len(downloads) == 3
    assert downloads[0]["name"] == "Desi Bhabhi Hot Romance"
    assert downloads[0]["url"] == "https://aagmaal.bz/desi-bhabhi-hot-romance/"
    assert downloads[0]["icon"] == "https://i.ibb.co/thumb1.jpg"
    assert downloads[1]["name"] == "Indian Couple Leaked MMS"
    assert downloads[2]["name"] == "Punjabi Girl Bathroom Video"

    # Pagination: next page with current=1, last=15
    assert len(dirs) == 1
    assert "Next Page" in dirs[0]["name"]
    assert "Page 1 of 15" in dirs[0]["name"]
    assert dirs[0]["url"] == "https://aagmaal.bz/page/2/"


def test_list_handles_no_pagination(monkeypatch):
    """Test that List handles pages without pagination gracefully."""
    html = """<html><body>
    <article class="vp-card">
        <a class="vp-card__thumb" href="https://aagmaal.bz/test-video/">
            <img alt="Test Video" src="thumb.jpg"/>
        </a>
    </article>
    </body></html>"""

    downloads = []
    dirs = []

    monkeypatch.setattr(aagmaal.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaal.site, "add_download_link",
                        lambda *a, **k: downloads.append(a[0]))
    monkeypatch.setattr(aagmaal.site, "add_dir",
                        lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(aagmaal.utils, "eod", lambda: None)

    aagmaal.List("https://aagmaal.bz/")

    assert len(downloads) == 1
    assert len(dirs) == 0


def test_categories_parses_footer_widget(monkeypatch):
    """Test that Categories finds the Categories h3 widget and its ul links."""
    html = load_fixture("categories.html")

    dirs = []

    monkeypatch.setattr(aagmaal.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(aagmaal.site, "add_dir",
                        lambda name, url, mode, icon=None, **k: dirs.append({"name": name, "url": url}))
    monkeypatch.setattr(aagmaal.utils, "eod", lambda: None)

    aagmaal.Categories("https://aagmaal.bz/")

    # 4 categories, sorted alphabetically
    assert len(dirs) == 4
    names = [d["name"] for d in dirs]
    assert names == sorted(names, key=str.lower)
    assert any("Desi Videos" in d["name"] for d in dirs)
    assert any("NueFliks" in d["name"] for d in dirs)


def test_search_without_keyword(monkeypatch):
    """Test that Search without keyword shows search input dialog."""
    search_called = []
    monkeypatch.setattr(aagmaal.site, "search_dir",
                        lambda url, mode: search_called.append(mode))

    aagmaal.Search("https://aagmaal.bz/?s=")

    assert len(search_called) == 1
    assert search_called[0] == "Search"


def test_search_with_keyword_calls_list(monkeypatch):
    """Test that Search with keyword calls List (not List2)."""
    list_calls = []
    monkeypatch.setattr(aagmaal, "List", lambda url: list_calls.append(url))

    aagmaal.Search("https://aagmaal.bz/?s=", keyword="desi bhabhi")

    assert len(list_calls) == 1
    assert "desi+bhabhi" in list_calls[0]

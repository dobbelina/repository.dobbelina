from pathlib import Path

from resources.lib.sites import thothub


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "thothub"


def load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_extract_list_items_parses_videos():
    """Test that _extract_list_items correctly parses video items from HTML."""
    html = load_fixture("public_list.html")
    items = thothub._extract_list_items(html)

    assert len(items) == 3, f"Expected 3 items, got {len(items)}"

    # Check first video
    url, name, screenshot = items[0]
    assert "/videos/1430251/" in url
    assert "Blowketing: Cutetati - Sextape" in name
    assert "/contents/videos_screenshots/1430000/1430251/" in screenshot

    # Check second video
    url, name, screenshot = items[1]
    assert "/videos/1430246/" in url
    assert "joi for my cuck husband" in name.lower()
    assert "/contents/videos_screenshots/1430000/1430246/" in screenshot

    # Check third video
    url, name, screenshot = items[2]
    assert "/videos/1430245/" in url
    assert "sensitiveasmrgirl" in name.lower()
    assert "/contents/videos_screenshots/1430000/1430245/" in screenshot


def test_extract_list_items_handles_empty_html():
    """Test that _extract_list_items handles empty HTML gracefully."""
    html = "<html><body></body></html>"
    items = thothub._extract_list_items(html)

    assert items == []


def test_find_next_page_detects_pagination():
    """Test that _find_next_page correctly finds next page URL."""
    html = load_fixture("public_list.html")
    current_url = "https://thothub.mx/public/"

    next_url = thothub._find_next_page(html, current_url)

    assert next_url is not None
    assert "/public/2/" in next_url


def test_find_next_page_handles_no_pagination():
    """Test that _find_next_page returns None when no pagination exists."""
    html = "<html><body><div>No pagination here</div></body></html>"
    current_url = "https://thothub.mx/public/"

    next_url = thothub._find_next_page(html, current_url)

    assert next_url is None


def test_list_integration(monkeypatch):
    """Test the full List function with mocked dependencies."""
    html = load_fixture("public_list.html")
    monkeypatch.setattr(
        thothub.utils, "getHtml", lambda url, referer=None, headers=None: html
    )

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
                "mode": mode,
                "icon": iconimage,
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode})

    monkeypatch.setattr(thothub.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(thothub.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(thothub.utils, "eod", lambda: None)

    thothub.List("https://thothub.mx/public/")

    # Verify videos were added
    assert len(downloads) == 3
    assert "Blowketing: Cutetati - Sextape" in downloads[0]["name"]
    assert "/videos/1430251/" in downloads[0]["url"]

    # Verify pagination was added
    next_pages = [entry for entry in dirs if "Next Page" in entry["name"]]
    assert len(next_pages) == 1
    assert "/public/2/" in next_pages[0]["url"]


def test_find_next_page_search_hash():
    """Test that _find_next_page handles #search hash links."""
    html = '<li class="next"><a href="#search" data-parameters="q:anal;from_videos+from_albums:2">Next</a></li>'
    current_url = "https://thothub.mx/search/anal/"
    nurl = thothub._find_next_page(html, current_url)
    assert nurl == "https://thothub.mx/search/anal/2/"


def test_search_url_format(monkeypatch):
    """Test that Search function uses the correct /search/keyword/ format."""
    searched_url = []

    def fake_list(url):
        searched_url.append(url)

    monkeypatch.setattr(thothub, "List", fake_list)
    thothub.Search("https://thothub.mx/search/", "big tits")

    assert len(searched_url) == 1
    assert searched_url[0] == "https://thothub.mx/search/big-tits/"


def test_main_exposes_navigation(monkeypatch):
    dirs = []

    monkeypatch.setattr(thothub, "List", lambda url: None)
    monkeypatch.setattr(
        thothub.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, *args, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(thothub.utils, "eod", lambda: None)

    thothub.Main()

    assert len(dirs) == 3
    assert dirs[0]["url"] == "https://thothub.mx/latest-updates/"
    assert dirs[1]["url"] == "https://thothub.mx/public/"
    assert dirs[2]["mode"] == "Search"

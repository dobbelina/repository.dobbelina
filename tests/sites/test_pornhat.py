"""Tests for pornhat.com site implementation."""

from resources.lib.sites import pornhat


def test_list_parses_videos(monkeypatch):
    """Test that List correctly parses video items with BeautifulSoup."""
    html = """
    <html>
    <div class="thumb thumb-video">
        <a href="/video/12345/hot-video" title="Hot Video Title">
            <img data-original="https://img.pornhat.com/thumb1.jpg" />
        </a>
        <span class="duration_item">10:30</span>
    </div>
    <div class="thumb">
        <a href="/watch/67890/another-video">
            <img src="//img.pornhat.com/thumb2.jpg" alt="Another Video" />
        </a>
        <span class="fa-clock-o"></span><span>15:45</span>
    </div>
    </html>
    """

    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "icon": iconimage,
                "duration": kwargs.get("duration"),
            }
        )

    monkeypatch.setattr(pornhat.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(pornhat.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pornhat.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(pornhat.utils, "eod", lambda: None)

    pornhat.List("https://www.pornhat.com/")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Hot Video Title"
    assert "https://www.pornhat.com/video/12345/hot-video" in downloads[0]["url"]
    assert "https:" in downloads[0]["icon"]
    assert downloads[0]["duration"] == "10:30"

    assert downloads[1]["name"] == "Another Video"


def test_list_pagination(monkeypatch):
    """Test that List handles pagination correctly."""
    html = """
    <html>
    <div class="thumb">
        <a href="/video/123/test" title="Test">
            <img alt="Test" />
        </a>
    </div>
    <div class="pagination">
        <a href="/2/">Next</a>
    </div>
    </html>
    """

    dirs = []

    def fake_add_dir(name, url, mode, iconimage):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(pornhat.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornhat.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(pornhat.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhat.utils, "eod", lambda: None)

    pornhat.List("https://www.pornhat.com/")

    next_pages = [d for d in dirs if "Next" in d["name"]]
    assert len(next_pages) == 1
    assert "https://www.pornhat.com/2/" in next_pages[0]["url"]


def test_cat_parses_categories(monkeypatch):
    """Test that Cat function parses category listings."""
    html = """
    <html>
    <a class="item" href="/channels/amateur" title="Amateur">
        <img src="thumb1.jpg" alt="Amateur" />
    </a>
    <div class="thumb-bl">
        <a href="/models/jane-doe">
            <img data-src="thumb2.jpg" />
            <div class="title">Jane Doe</div>
        </a>
    </div>
    </html>
    """

    dirs = []

    def fake_add_dir(name, url, mode, iconimage):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(pornhat.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornhat.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(pornhat.utils, "eod", lambda: None)

    pornhat.Cat("https://www.pornhat.com/channels/")

    assert len(dirs) >= 2
    amateur = [d for d in dirs if "Amateur" in d["name"]]
    assert len(amateur) >= 1


def test_search_with_keyword(monkeypatch):
    """Test that Search with keyword calls List with encoded query."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(pornhat, "List", fake_list)

    pornhat.Search("https://www.pornhat.com/search/", keyword="test query")

    assert len(list_calls) == 1
    assert "test-query" in list_calls[0]


def test_get_site_returns_correct_site():
    """Test that getSite function returns the correct site object based on URL."""
    assert pornhat.getSite("https://www.pornhat.com/") == pornhat.site
    assert pornhat.getSite("https://hello.porn/") == pornhat.site1
    assert pornhat.getSite("https://ok.porn/") == pornhat.site2
    assert pornhat.getSite("https://pornstars.tube/") == pornhat.site4
    assert pornhat.getSite("https://max.porn/") == pornhat.site5
    assert pornhat.getSite("https://homo.xxx/") == pornhat.site6
    assert pornhat.getSite("https://www.perfectgirls.xxx/") == pornhat.site7

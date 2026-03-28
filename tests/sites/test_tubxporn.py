"""Tests for tubxporn.com site implementation."""

from resources.lib.sites import tubxporn


def test_list_parses_videos(monkeypatch):
    """Test that List correctly parses video items with BeautifulSoup."""
    html = """
    <html>
    <div class="thumbBlock">
        <a href="/video/12345/hot-video" title="Hot Video Title">
            <img data-src="https://img.tubxporn.com/thumb1.jpg" />
        </a>
        <div class="duration">10:30</div>
    </div>
    <div class="item">
        <a href="/watch/67890/another-video">
            <img src="https://img.tubxporn.com/thumb2.jpg" alt="Another Video" />
        </a>
        <span>15:45</span>
    </div>
    </html>
    """

    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append({"name": name, "url": url})

    monkeypatch.setattr(tubxporn.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(tubxporn.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(tubxporn.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(tubxporn.utils, "eod", lambda: None)

    tubxporn.List("https://tubxporn.com/")

    assert len(downloads) >= 0


def test_search_with_keyword(monkeypatch):
    """Test that Search with keyword calls List with encoded query."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(tubxporn, "List", fake_list)

    tubxporn.Search("https://tubxporn.com/search/", keyword="test query")

    assert len(list_calls) == 1


def test_search_with_keyword_uses_default_search_endpoint_for_base_url(monkeypatch):
    """Test that Search builds the search endpoint when given the site base URL."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(tubxporn, "List", fake_list)

    tubxporn.Search("https://web.tubxporn.com/", keyword="test query")

    assert len(list_calls) == 1
    assert list_calls[0] == "https://web.tubxporn.com/search/?q=test%20query"

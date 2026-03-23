"""Tests for YouPorn site implementation."""

from pathlib import Path

from resources.lib.sites import youporn

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "youporn"


def load_fixture(name):
    """Load a fixture file from the youporn fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_videos(monkeypatch):
    """Test that List correctly parses video items."""
    html_data = load_fixture("listing.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html_data

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(youporn.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(youporn.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(youporn.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(youporn.utils, "eod", lambda: None)

    youporn.List("https://www.youporn.com/")

    # Check that we parsed 2 videos
    assert len(downloads) == 2

    # Check first video
    assert "stepmom's hot blonde sister" in downloads[0]["name"]
    assert downloads[0]["url"] == "https://www.youporn.com/watch/190946451/"
    assert downloads[0]["duration"] == "15:00"
    assert "461057541" in downloads[0]["icon"]

    # Check second video
    assert "Step Mom Squirts" in downloads[1]["name"]
    assert downloads[1]["url"] == "https://www.youporn.com/watch/191010461/"
    assert downloads[1]["duration"] == "07:38"


def test_list_handles_pagination(monkeypatch):
    """Test that List adds Next Page when pagination is present."""
    html_data = load_fixture("listing.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html_data

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url})

    monkeypatch.setattr(youporn.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(youporn.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(youporn.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(youporn.utils, "eod", lambda: None)

    youporn.List("https://www.youporn.com/")

    # Should have Next Page
    next_pages = [d for d in dirs if "Next Page" in d["name"]]
    assert len(next_pages) == 1
    assert "page=3" in next_pages[0]["url"]
    assert "(3)" in next_pages[0]["name"]


def test_categories_parses_and_sorts(monkeypatch):
    """Test that Categories correctly parses categories."""
    html_data = load_fixture("categories.html")

    dirs = []

    def fake_get_html(url, referer=None, headers=None):
        return html_data

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(youporn.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(youporn.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(youporn.utils, "eod", lambda: None)

    youporn.Categories("https://www.youporn.com/categories/")

    assert len(dirs) == 3

    # Check that categories are sorted alphabetically
    assert "Anal" in dirs[0]["name"]
    assert "Blonde" in dirs[1]["name"]
    assert "MILF" in dirs[2]["name"]

    # Check URLs
    assert "/category/anal/" in dirs[0]["url"]
    assert "/category/blonde/" in dirs[1]["url"]
    assert "/category/milf/" in dirs[2]["url"]


def test_search_builds_correct_url(monkeypatch):
    """Test that Search builds the correct URL with search parameter."""
    called_urls = []

    def fake_list(url):
        called_urls.append(url)

    monkeypatch.setattr(youporn, "List", fake_list)

    youporn.Search("https://www.youporn.com/search/", keyword="test search")

    assert len(called_urls) == 1
    assert called_urls[0] == "https://www.youporn.com/search/?query=test+search"


def test_list_skips_short_videos_and_uses_thumbnail_fallback(monkeypatch):
    """Test that List filters sub-minute clips and still extracts lazy thumbs."""
    html_data = """
    <html>
      <body>
        <div class="video-box">
          <a href="/watch/111/" class="video-box-image" data-thumbnail="//cdn.example.com/thumb-111.jpg">
            <div class="video-duration"><span>00:45</span></div>
          </a>
          <div class="video-title-wrapper">
            <a class="video-title-text"><span>Short teaser</span></a>
          </div>
        </div>
        <div class="video-box">
          <a href="/watch/222/" class="video-box-image">
            <img class="thumb-image" src="data:image/png;base64,placeholder" data-original="https://cdn.example.com/thumb-222.jpg" />
            <div class="video-duration"><span>01:01</span></div>
          </a>
          <div class="video-title-wrapper">
            <a class="video-title-text"><span>Keep this one</span></a>
          </div>
        </div>
      </body>
    </html>
    """

    downloads = []

    def fake_get_html(url, referer=None, headers=None):
        return html_data

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name, "url": url, "icon": iconimage})

    monkeypatch.setattr(youporn.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(youporn.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(youporn.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(youporn.utils, "eod", lambda: None)

    youporn.List("https://www.youporn.com/")

    assert len(downloads) == 1
    assert downloads[0]["name"] == "Keep this one"
    assert downloads[0]["url"] == "https://www.youporn.com/watch/222/"
    assert downloads[0]["icon"] == "https://cdn.example.com/thumb-222.jpg"


def test_list_prefers_poster_thumbnail_over_preview_video(monkeypatch):
    html_data = """
    <html>
      <body>
        <article class="video-box pc js_video-box js-pop">
          <a href="/watch/333/" class="video-box-image">
            <div class="thumb-image-container">
              <img
                class="thumb-image js_lazy js-mediabook js-videoThumbWebm js-videoPreview"
                data-src="https://cdn.example.com/preview-333.mp4"
                data-poster="https://cdn.example.com/poster-333.jpg"
                alt="Poster wins"
                src="data:image/gif;base64,placeholder"
              />
            </div>
            <div class="video-duration"><span>12:34</span></div>
          </a>
          <div class="video-title-wrapper">
            <a class="video-title-text"><span>Poster wins</span></a>
          </div>
        </article>
      </body>
    </html>
    """

    downloads = []

    def fake_get_html(url, referer=None, headers=None):
        return html_data

    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        downloads.append({"name": name, "url": url, "icon": iconimage})

    monkeypatch.setattr(youporn.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(youporn.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(youporn.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(youporn.utils, "eod", lambda: None)

    youporn.List("https://www.youporn.com/browse/time/")

    assert len(downloads) == 1
    assert downloads[0]["icon"] == "https://cdn.example.com/poster-333.jpg"

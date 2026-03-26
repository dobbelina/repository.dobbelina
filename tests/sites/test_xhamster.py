"""Tests for xhamster.com site implementation."""

import json
from resources.lib.sites import xhamster


def test_list_parses_json_videos(monkeypatch):
    """Test that List correctly parses JSON video data."""
    videos_data = [
        {
            "title": "Hot Video Title",
            "pageURL": "/videos/hot-video-12345",
            "thumbURL": "https://thumb.xhamster.com/thumb1.jpg",
            "duration": 630,
            "isBlockedByGeo": False,
        },
        {
            "title": "Another Video",
            "pageURL": "/videos/another-video-67890",
            "thumbURL": "https://thumb.xhamster.com/thumb2.jpg",
            "duration": 945,
            "isBlockedByGeo": False,
        },
    ]

    json_data = {
        "layoutPage": {
            "videoListProps": {"videoThumbProps": videos_data},
            "categoryInfoProps": {"pageTitle": "Test Category"},
        }
    }

    html = f"""
    <html>
    <title>Test Page</title>
    <script>window.initials={json.dumps(json_data)};</script>
    </html>
    """

    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return html

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append({"name": name, "url": url, "icon": iconimage})

    monkeypatch.setattr(xhamster.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(xhamster.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(xhamster.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(xhamster.utils, "eod", lambda: None)
    monkeypatch.setattr(xhamster.utils.addon, "getSetting", lambda x: "all")
    monkeypatch.setattr(xhamster, "update_url", lambda url: url)
    monkeypatch.setattr(xhamster, "get_setting", lambda x: "All")

    # Mock Thumbnails class
    class FakeThumbnails:
        def __init__(self, site_name):
            pass

        def get(self, urls):
            return urls[0] if urls else ""

    monkeypatch.setattr(xhamster.utils, "Thumbnails", FakeThumbnails)

    xhamster.List("https://xhamster.com/newest")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Hot Video Title"
    assert "/videos/hot-video-12345" in downloads[0]["url"]


def test_list_skips_geo_blocked_videos(monkeypatch):
    """Test that List skips videos blocked by geo-restriction."""
    videos_data = [
        {
            "title": "Available Video",
            "pageURL": "/videos/available-123",
            "thumbURL": "thumb1.jpg",
            "duration": 90,
            "isBlockedByGeo": False,
        },
        {
            "title": "Blocked Video",
            "pageURL": "/videos/blocked-456",
            "thumbURL": "thumb2.jpg",
            "duration": 120,
            "isBlockedByGeo": True,
        },
    ]

    json_data = {"layoutPage": {"videoListProps": {"videoThumbProps": videos_data}}}

    html = f"""
    <html>
    <script>window.initials={json.dumps(json_data)};</script>
    </html>
    """

    downloads = []

    class FakeThumbnails:
        def __init__(self, site_name):
            pass

        def get(self, urls):
            return urls[0] if urls else ""

    monkeypatch.setattr(xhamster.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        xhamster.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(xhamster.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(xhamster.utils, "eod", lambda: None)
    monkeypatch.setattr(xhamster.utils.addon, "getSetting", lambda x: "all")
    monkeypatch.setattr(xhamster, "update_url", lambda url: url)
    monkeypatch.setattr(xhamster, "get_setting", lambda x: "All")
    monkeypatch.setattr(xhamster.utils, "Thumbnails", FakeThumbnails)

    xhamster.List("https://xhamster.com/newest")

    # Only available video should be added
    assert len(downloads) == 1
    assert "Available Video" in downloads[0]


def test_categories_parses_json(monkeypatch):
    """Test that Categories function parses category data."""
    html = """
    <html>
    <a class="thumbItem-abc" href="/categories/amateur">
        <img data-thumb-url="thumb1.jpg" />
        <h3>Amateur</h3>
    </a>
    <a class="thumbItem-def" href="/categories/milf">
        <img data-thumb-url="thumb2.jpg" />
        <h3>MILF</h3>
    </a>
    </html>
    """

    dirs = []

    monkeypatch.setattr(xhamster.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(xhamster.site, "add_dir", lambda *a, **k: dirs.append(a[0]))
    monkeypatch.setattr(xhamster.utils, "eod", lambda: None)

    xhamster.Categories("https://xhamster.com/categories")

    assert len(dirs) == 2
    assert "Amateur" in dirs[0]
    assert "MILF" in dirs[1]


def test_search_with_keyword(monkeypatch):
    """Test that Search with keyword calls List with encoded query."""
    list_calls = []

    def fake_list(url):
        list_calls.append(url)

    monkeypatch.setattr(xhamster, "List", fake_list)

    xhamster.Search("https://xhamster.com/search/", keyword="test query")

    assert len(list_calls) == 1
    assert "test+query" in list_calls[0] or "test%20query" in list_calls[0]


def test_list_handles_layout_page_missing_video_list_props(monkeypatch):
    """Test that List does not crash when layoutPage lacks videoListProps (KeyError regression)."""
    videos_data = [
        {
            "title": "Newest Video",
            "pageURL": "/videos/newest-123",
            "thumbURL": "https://thumb.xhamster.com/newest.jpg",
            "duration": 300,
            "isBlockedByGeo": False,
        }
    ]
    # layoutPage exists but has no videoListProps; pagesNewestComponent has the videos
    json_data = {
        "layoutPage": {
            "categoryInfoProps": {"pageTitle": "Newest"},
        },
        "pagesNewestComponent": {
            "videoListProps": {"videoThumbProps": videos_data},
            "paginationProps": {
                "currentPageNumber": 1,
                "lastPageNumber": 2,
                "pageLinkTemplate": "https://xhamster.com/newest/{#}",
            },
        },
    }

    html = f"""<html><title>Newest</title>
    <script>window.initials={json.dumps(json_data)};</script>
    </html>"""

    downloads = []

    class FakeThumbnails:
        def __init__(self, site_name):
            pass

        def get(self, urls):
            return urls[0] if urls else ""

    monkeypatch.setattr(xhamster.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        xhamster.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc, **kwargs: downloads.append(
            {"name": name, "url": url}
        ),
    )
    monkeypatch.setattr(xhamster.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(xhamster.utils, "eod", lambda: None)
    monkeypatch.setattr(xhamster.utils.addon, "getSetting", lambda x: "all")
    monkeypatch.setattr(xhamster, "update_url", lambda url: url)
    monkeypatch.setattr(xhamster, "get_setting", lambda x: "All")
    monkeypatch.setattr(xhamster.utils, "Thumbnails", FakeThumbnails)

    xhamster.List("https://xhamster.com/newest")

    assert len(downloads) == 1
    assert downloads[0]["name"] == "Newest Video"


def test_list_handles_missing_initials_json(monkeypatch):
    """Search pages without embedded initials JSON should fail closed."""
    downloads = []
    notifications = []

    class FakeThumbnails:
        def __init__(self, site_name):
            pass

        def get(self, urls):
            return urls[0] if urls else ""

    monkeypatch.setattr(
        xhamster.utils, "getHtml", lambda *a, **k: "<html><title>Search</title></html>"
    )
    monkeypatch.setattr(
        xhamster.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(xhamster.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(xhamster.utils, "eod", lambda: None)
    monkeypatch.setattr(
        xhamster.utils, "notify", lambda title, msg: notifications.append((title, msg))
    )
    monkeypatch.setattr(xhamster.utils.addon, "getSetting", lambda x: "all")
    monkeypatch.setattr(xhamster, "update_url", lambda url: url)
    monkeypatch.setattr(xhamster, "get_setting", lambda x: "All")
    monkeypatch.setattr(xhamster.utils, "Thumbnails", FakeThumbnails)

    xhamster.List("https://xhamster.com/search/test?orientations=straight")

    assert downloads == []
    assert notifications == [("Oh Oh", "No video found.")]


def test_list_finds_nested_video_list_props_and_pagination(monkeypatch):
    videos_data = [
        {
            "title": "Nested Video",
            "pageURL": "/videos/nested-123",
            "thumbURL": "https://thumb.xhamster.com/nested.jpg",
            "duration": 120,
            "isBlockedByGeo": False,
        }
    ]

    json_data = {
        "layoutPage": {"categoryInfoProps": {"pageTitle": "Nested"}},
        "newestPage": {
            "sections": {
                "primary": {
                    "videoListProps": {"videoThumbProps": videos_data},
                    "paginationProps": {
                        "currentPageNumber": 1,
                        "lastPageNumber": 3,
                        "pageLinkTemplate": "https://xhamster.com/newest/{#}",
                    },
                }
            }
        },
    }

    html = f"""<html><title>Nested</title>
    <script id="initials-script">window.initials={json.dumps(json_data)};</script>
    </html>"""

    downloads = []
    dirs = []

    class FakeThumbnails:
        def __init__(self, site_name):
            pass

        def get(self, urls):
            return urls[0] if urls else ""

        def fix_img(self, url):
            return url

    monkeypatch.setattr(xhamster.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        xhamster.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc, **kwargs: downloads.append(
            {"name": name, "url": url}
        ),
    )
    monkeypatch.setattr(
        xhamster.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url}
        ),
    )
    monkeypatch.setattr(xhamster.utils, "eod", lambda: None)
    monkeypatch.setattr(xhamster.utils.addon, "getSetting", lambda x: "all")
    monkeypatch.setattr(xhamster, "update_url", lambda url: url)
    monkeypatch.setattr(xhamster, "get_setting", lambda x: "All")
    monkeypatch.setattr(xhamster.utils, "Thumbnails", FakeThumbnails)

    xhamster.List("https://xhamster.com/newest")

    assert downloads == [{"name": "Nested Video", "url": "/videos/nested-123"}]
    assert dirs
    assert dirs[0]["url"] == "https://xhamster.com/newest/2"

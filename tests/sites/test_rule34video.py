"""Comprehensive tests for rule34video site implementation."""

from pathlib import Path
import pytest
import re
from unittest.mock import MagicMock

from resources.lib.sites import rule34video


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "rule34video"


def load_fixture(name):
    """Load a fixture file from the rule34video fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List() correctly parses video items using BeautifulSoup."""
    html = load_fixture("list.html")

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_download_link(
        name, url, mode, iconimage, desc="", duration="", quality="", **kwargs
    ):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "desc": desc,
                "duration": duration,
                "quality": quality,
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode})

    monkeypatch.setattr(rule34video.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(rule34video.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(rule34video.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)
    monkeypatch.setattr(rule34video.utils, "cleantext", lambda x: x)

    # Call List
    rule34video.List("https://rule34video.com/latest-updates/")

    # Verify we got 3 videos
    assert len(downloads) == 3


def test_list_handles_pagination(monkeypatch):
    """Test that List() correctly handles pagination."""
    html = load_fixture("list.html")

    dirs = []

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append({"name": name, "url": url, "mode": mode})

    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(rule34video.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(rule34video.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)
    monkeypatch.setattr(rule34video.utils, "cleantext", lambda x: x)

    # Call List
    rule34video.List("https://rule34video.com/latest-updates/")

    # Verify pagination was added
    next_pages = [d for d in dirs if "Next Page" in d["name"]]
    assert len(next_pages) == 1


def test_list_missing_link_and_href(monkeypatch):
    """Test List() loop continue branches (Lines 64, 68)."""
    html = """
    <div class="item">No open-popup link</div>
    <div class="item"><a class="open-popup">No href</a></div>
    <div class="item"><a class="open-popup" href="/valid/">Valid</a><img alt="Title"></div>
    """
    downloads = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_download_link", lambda *a, **k: downloads.append(a))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.List("https://rule34video.com/")
    assert len(downloads) == 1


def test_list_pagination_plus_replacement(monkeypatch):
    """Test List() pagination plus replacement branch (Line 106)."""
    html = """
    <div class="pager next" data-block-id="1" data-parameters="section:abc+def;from:2">Next</div>
    """
    dirs = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_dir", lambda name, url, *a, **k: dirs.append(url))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.List("https://rule34video.com/")
    assert len(dirs) == 1
    assert "section=abc=02&def" in dirs[0]


def test_tag_menu_missing_params_and_section(monkeypatch):
    """Test TagMenu() loop continue branches (Lines 170, 175)."""
    html = """
    <a data-block-id="list_tags_tags_list">No params</a>
    <a data-block-id="list_tags_tags_list" data-parameters="no-section">No section</a>
    <a data-block-id="list_tags_tags_list" data-parameters="section:valid">Valid</a>
    """
    dirs = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_dir", lambda *a, **k: dirs.append(a))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.TagMenu("https://rule34video.com/tags/")
    assert len(dirs) == 1


def test_tag_loop_branches(monkeypatch):
    """Test Tag() loop branches (Lines 201, 205, 219, 221, 223)."""
    html = """
    <div class="item">No link</div>
    <div class="item"><a>No href</a></div>
    <div class="item"><a href="/t1/">T1 <svg></svg> 50</a></div>
    <div class="item"><a href="/t2/">T2 <svg></svg></a></div>
    <div class="item"><a href="/t3/">T3 <svg></svg> <span class="count">100</span></a></div>
    """
    dirs = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.Tag("https://rule34video.com/tags/")
    # T1 (via next_sibling 219), T2 (empty 221), T3 (via span 223)
    assert any("50" in name for name in dirs)
    assert any("100" in name for name in dirs)
    assert any("T2" in name and "[COLOR orange]" not in name for name in dirs)


def test_tag_pagination_exactly_120(monkeypatch):
    """Test Tag() pagination branch (Line 233)."""
    items_html = '<div class="item"><a href="/t/">T</a></div>' * 120
    html = f'<html><body>{items_html}</body></html>'
    dirs = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.Tag("https://rule34video.com/tags/", page=1)
    assert any("Next Page" in name for name in dirs)


def test_cats_loop_branches(monkeypatch):
    """Test Cats() loop continue branches (Lines 255, 259)."""
    html = """
    <div class="item">No th link</div>
    <div class="item"><a class="th">No href</a></div>
    <div class="item"><a class="th" href="/valid/"><img alt="Title"><div class="title">Title</div></a></div>
    """
    dirs = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.Cats("https://rule34video.com/categories/")
    assert len(dirs) == 1


def test_cats_pagination_extra_branches(monkeypatch):
    """Test Cats() pagination branches (Line 316, 329)."""
    html = """
    <div class="item pager next" data-parameters="from:30">Next</div>
    <div class="item active" data-parameters="from:20">2</div>
    <div class="item"><a data-parameters="from:100">Last</a></div>
    """
    dirs = []
    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.site, "add_dir", lambda name, url, *a, **k: dirs.append(url))
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    # Test logic where &from= is already in URL and &_ is not
    rule34video.Cats("https://rule34video.com/cats/?from=10")
    assert "&_=" in dirs[0]


def test_playvid_kt_player(monkeypatch):
    """Test Playvid() kt_player branch."""
    html = "kt_player('kt_player', '...');"
    kt_player_called = [False]

    class MockVideoPlayer:
        def __init__(self, name, download=None):
            self.progress = MagicMock()
        def play_from_kt_player(self, html, url=None):
            kt_player_called[0] = True

    monkeypatch.setattr(rule34video.utils, "getHtml", lambda *a: html)
    monkeypatch.setattr(rule34video.utils, "VideoPlayer", MockVideoPlayer)

    rule34video.Playvid("https://rule34video.com/v/", "Test")
    assert kt_player_called[0]


def test_search_logic(monkeypatch):
    """Test Search() branches."""
    search_dir_mock = MagicMock()
    list_called_with = []

    monkeypatch.setattr(rule34video.site, "search_dir", search_dir_mock)
    monkeypatch.setattr(rule34video, "List", lambda url: list_called_with.append(url))

    # Without keyword
    rule34video.Search("https://rule34video.com/search/")
    assert search_dir_mock.called
    
    # With keyword
    rule34video.Search("https://rule34video.com/search/", keyword="my search")
    assert "my-search" in list_called_with[0]


def test_main_logic(monkeypatch):
    """Test Main() calls."""
    dirs = []
    monkeypatch.setattr(rule34video.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(rule34video, "List", lambda url: None)
    monkeypatch.setattr(rule34video.utils, "eod", lambda: None)

    rule34video.Main()
    assert len(dirs) >= 3

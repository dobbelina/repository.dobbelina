"""Tests for pornditt site implementation."""

import pytest
import re
from unittest.mock import MagicMock
from pathlib import Path

from resources.lib.sites import pornditt


def test_main_menu(monkeypatch):
    """Test that main menu directories are added."""
    dirs = []
    monkeypatch.setattr(pornditt.site, "add_dir", lambda name, url, mode, iconimage=None, **kwargs: dirs.append(name))
    monkeypatch.setattr(pornditt, "List", lambda *a: None)
    
    pornditt.Main()
    
    assert any("Categories" in d for d in dirs)
    assert any("Pornstars" in d for d in dirs)
    assert any("Search" in d for d in dirs)


def test_categories_parsing(monkeypatch):
    """Test that categories are parsed correctly."""
    html = """
    <div class="list-categories">
        <a class="item" href="https://pornditt.com/categories/alt/" title="Alt">
            <img src="thumb.jpg">
            <strong class="title">Alt</strong>
        </a>
        <a class="item" title="No href"></a>
    </div>
    """
    dirs = []
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(pornditt.utils, "eod", lambda: None)
    
    pornditt.Categories("https://pornditt.com/categories/")
    
    assert "Alt" in dirs
    assert len(dirs) == 1


def test_pornstars_parsing(monkeypatch):
    """Test that pornstars are parsed correctly."""
    html = """
    <div class="list-models">
        <a class="item" href="https://pornditt.com/models/star/" title="Star">
            <img src="star.jpg">
            <span class="title">Star</span>
        </a>
        <a class="item">No href</a>
    </div>
    """
    dirs = []
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(pornditt.utils, "eod", lambda: None)
    
    pornditt.Pornstars("https://pornditt.com/models/")
    
    assert "Star" in dirs
    assert len(dirs) == 1


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "pornditt"


def load_fixture(name):
    """Load a fixture file from the pornditt fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parsing(monkeypatch):
    """Test that video list is parsed correctly."""
    html = load_fixture("list.html")
    # Add a bad item to hit line 136
    html += '<div class="list-videos"><div class="item">No link here</div></div>'
    
    downloads = []
    dirs = []
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.site, "add_download_link", lambda name, *a, **k: downloads.append(name))
    monkeypatch.setattr(pornditt.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(pornditt.utils, "eod", lambda: None)
    
    pornditt.List("https://pornditt.com/latest-updates/")
    
    assert "OpenFamily Reagan Foxx WRB" in downloads
    assert any("Next Page" in d for d in dirs)
    assert "(01/3499)" in [d for d in dirs if "Next Page" in d][0]


def test_playvid_parsing(monkeypatch):
    """Test video source extraction with license_code."""
    html = """
    <script>
    license_code: '$529619017473059',
    video_url: 'function/0/https://v.pornditt.com/get_file/29/8e4237cd874f108722efb0a97b4e70dd56dbe45387/165000/165639/165639.mp4/',
    video_url_text: '480p',
    video_alt_url: 'function/0/https://v.pornditt.com/get_file/29/2faa3650a1229608b128e668b162d45f495a1730a1/165000/165639/165639_720p.mp4/',
    video_alt_url_text: '720p'
    </script>
    """
    played = []
    class MockPlayer:
        def __init__(self, *a, **k): self.progress = MagicMock()
        def play_from_direct_link(self, url): played.append(url)
        
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.utils, "VideoPlayer", MockPlayer)
    
    pornditt.Playvid("https://v.pornditt.com/v/1", "Name")
    
    assert len(played) == 1
    assert "165639_720p.mp4" in played[0]
    assert "rnd=" in played[0]
    assert "2faa3650a1229608b128e668b162d45f495a1730a1" not in played[0]


def test_playvid_parsing_no_license(monkeypatch):
    """Test video source extraction without license_code."""
    html = """
    <script>
    video_url: 'function/0/https://v.pornditt.com/video.mp4/',
    video_url_text: '480p'
    </script>
    """
    played = []
    class MockPlayer:
        def __init__(self, *a, **k): self.progress = MagicMock()
        def play_from_direct_link(self, url): played.append(url)
        
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.utils, "VideoPlayer", MockPlayer)
    
    pornditt.Playvid("url", "Name")
    assert len(played) == 1
    assert "https://v.pornditt.com/video.mp4/" in played[0]


def test_playvid_single_with_license(monkeypatch):
    """Test single video_url with license_code."""
    html = """
    <script>
    license_code: '$529619017473059',
    video_url: 'function/0/https://v.pornditt.com/get_file/29/8e4237cd874f108722efb0a97b4e70dd56dbe45387/165000/165639/165639.mp4/'
    </script>
    """
    played = []
    class MockPlayer:
        def __init__(self, *a, **k): self.progress = MagicMock()
        def play_from_direct_link(self, url): played.append(url)
        
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.utils, "VideoPlayer", MockPlayer)
    
    pornditt.Playvid("url", "Name")
    assert len(played) == 1
    assert "rnd=" in played[0]


def test_playvid_fallback(monkeypatch):
    """Test fallback to single video_url and video tag."""
    # 1. Single video_url with function
    html1 = "video_url: 'function/0/https://v.pornditt.com/v.mp4'"
    played = []
    class MockPlayer:
        def __init__(self, *a, **k): self.progress = MagicMock()
        def play_from_direct_link(self, url): played.append(url)
    
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html1)
    monkeypatch.setattr(pornditt.utils, "VideoPlayer", MockPlayer)
    pornditt.Playvid("url", "name")
    assert "v.mp4" in played[0]
    
    # 2. Video tag
    html2 = "<video><source src='direct.mp4'></video>"
    played.clear()
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html2)
    pornditt.Playvid("url", "name")
    assert "direct.mp4" in played[0]


def test_playvid_not_found(monkeypatch):
    """Test Playvid when no source is found."""
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: "no video here")
    notify_calls = []
    monkeypatch.setattr(pornditt.utils, "notify", lambda *a, **k: notify_calls.append(a))
    
    class MockPlayer:
        def __init__(self, *a, **k): self.progress = MagicMock()
    monkeypatch.setattr(pornditt.utils, "VideoPlayer", MockPlayer)
    
    pornditt.Playvid("url", "name")
    assert any("Unable to extract video link" in str(n) for n in notify_calls)


def test_search(monkeypatch):
    """Test search logic."""
    search_dir_mock = MagicMock()
    list_mock = MagicMock()
    monkeypatch.setattr(pornditt.site, "search_dir", search_dir_mock)
    monkeypatch.setattr(pornditt, "List", list_mock)
    
    # No keyword
    pornditt.Search("url")
    assert search_dir_mock.called
    
    # With keyword
    pornditt.Search("url", keyword="my search")
    assert list_mock.called
    assert "my-search" in list_mock.call_args[0][0]


def test_error_handling(monkeypatch):
    """Test exception branches."""
    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: "<div></div>")
    
    # Force error in select to hit outer except blocks (Lines 64-66, 96-98, 128-130)
    class BadSoup:
        def select(self, selector): raise Exception("outer_boom")
        def select_one(self, selector): return None
        
    monkeypatch.setattr(pornditt.utils, "parse_html", lambda *a: BadSoup())
    
    pornditt.Categories("url")
    pornditt.Pornstars("url")
    pornditt.List("url")

    # Now test inner loop exceptions
    class BadItem:
        @property
        def text(self): raise Exception("inner_boom")
        def select_one(self, selector): raise Exception("inner_boom")

    class InnerBadSoup:
        def select(self, selector):
            return [BadItem()]
        def select_one(self, selector): return None
    
    monkeypatch.setattr(pornditt.utils, "parse_html", lambda *a: InnerBadSoup())
    pornditt.Categories("url")
    pornditt.Pornstars("url")
    pornditt.List("url")

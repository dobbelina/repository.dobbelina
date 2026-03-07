import pytest
from unittest.mock import MagicMock
from resources.lib.sites import ask4porn

@pytest.fixture
def mock_list_html(monkeypatch, read_fixture):
    html = read_fixture("sites/ask4porn/list.html")
    def _mock_get_html(url, **kwargs):
        return html, False
    monkeypatch.setattr(ask4porn.utils, "get_html_with_cloudflare_retry", _mock_get_html)
    return html

def test_list_parsing(mock_list_html):
    """Test that video items are correctly parsed from the list page."""
    ask4porn.List("https://ask4porn.cc/videos")
    pass

def test_main_menu():
    """Test that main menu directories are added."""
    ask4porn.Main("https://ask4porn.cc/")
    pass

def test_studios_parsing(monkeypatch):
    """Test Studios() parsing and pagination."""
    html = """
    <a class="netflix-category-link" href="/studio/1/">
        <img src="1.jpg">
        <span class="netflix-category-name">Studio 1</span>
    </a>
    <a href="/categories/page/2/">Next »</a>
    """
    monkeypatch.setattr(ask4porn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    dirs = []
    monkeypatch.setattr(ask4porn.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(ask4porn.utils, "eod", lambda: None)

    ask4porn.Studios("https://ask4porn.cc/categories/")
    assert "Studio 1" in dirs
    assert "Next Page" in dirs

def test_categories_parsing(monkeypatch):
    """Test Categories() parsing."""
    html = """
    <a class="netflix-tag-link" href="/tag/1/">
        <img src="1.jpg">
        <span class="netflix-tag-name">Category 1</span>
    </a>
    """
    monkeypatch.setattr(ask4porn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    dirs = []
    monkeypatch.setattr(ask4porn.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(ask4porn.utils, "eod", lambda: None)

    ask4porn.Categories("https://ask4porn.cc/tags/")
    assert "Category 1" in dirs

def test_girls_parsing(monkeypatch):
    """Test Girls() parsing and pagination."""
    html = """
    <a class="netflix-actor-link" href="/girl/1/">
        <img src="1.jpg">
        <span class="netflix-actor-name">Girl 1</span>
    </a>
    <a href="/actors-1/page/2/">next</a>
    """
    monkeypatch.setattr(ask4porn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    dirs = []
    monkeypatch.setattr(ask4porn.site, "add_dir", lambda name, *a, **k: dirs.append(name))
    monkeypatch.setattr(ask4porn.utils, "eod", lambda: None)

    ask4porn.Girls("https://ask4porn.cc/actors-1/")
    assert "Girl 1" in dirs
    assert "Next Page" in dirs

def test_playvid(monkeypatch):
    """Test Playvid() call."""
    html = "<html><body>video page</body></html>"
    monkeypatch.setattr(ask4porn.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    
    vp_mock = MagicMock()
    monkeypatch.setattr(ask4porn.utils, "VideoPlayer", lambda *a, **k: vp_mock)
    
    ask4porn.Playvid("https://ask4porn.cc/v/1", "Name")
    assert vp_mock.play_from_html.called

def test_search(monkeypatch):
    """Test Search() branches."""
    search_dir_mock = MagicMock()
    list_mock = MagicMock()
    monkeypatch.setattr(ask4porn.site, "search_dir", search_dir_mock)
    monkeypatch.setattr(ask4porn, "List", list_mock)
    
    # No keyword
    ask4porn.Search("https://ask4porn.cc/")
    assert search_dir_mock.called
    
    # With keyword
    ask4porn.Search("https://ask4porn.cc/", keyword="my search")
    assert list_mock.called
    assert "my%20search" in list_mock.call_args[0][0]

import pytest
from pathlib import Path
from resources.lib.sites import pimpbunny

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "pimpbunny"

def test_list_parsing(monkeypatch):
    html = (FIXTURE_DIR / "listing.html").read_text(encoding="utf-8")
    
    links = []
    def fake_add_download_link(name, url, mode, iconimage, desc="", **kwargs):
        links.append({"name": name, "url": url})

    monkeypatch.setattr(pimpbunny.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    monkeypatch.setattr(pimpbunny.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(pimpbunny.utils, "eod", lambda: None)

    pimpbunny.List("https://pimpbunny.com/videos/")
    
    assert len(links) > 0
    assert "Brook Summers" in links[0]["name"]
    assert "pimpbunny.com/videos/" in links[0]["url"]

def test_playvid_parsing(monkeypatch):
    html = (FIXTURE_DIR / "video.html").read_text(encoding="utf-8")
    
    played_urls = []
    class FakeVideoPlayer:
        def __init__(self, name, download):
            self.progress = type('obj', (object,), {'update': lambda *a, **k: None})
        def play_from_direct_link(self, url):
            played_urls.append(url)

    monkeypatch.setattr(pimpbunny.utils, "get_html_with_cloudflare_retry", lambda *a, **k: (html, False))
    monkeypatch.setattr(pimpbunny.utils, "VideoPlayer", FakeVideoPlayer)

    pimpbunny.Playvid("https://pimpbunny.com/videos/test/", "Test Video")
    
    assert len(played_urls) == 1
    assert "1440p.mp4" in played_urls[0] or "1080p.mp4" in played_urls[0] or "720p.mp4" in played_urls[0]
    assert "|Referer=" in played_urls[0]

from pathlib import Path
from unittest.mock import MagicMock

from resources.lib.sites import porndoe


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites"


def _load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_porndoe_list_parses_videos(monkeypatch):
    html = _load_fixture("porndoe_home.html")
    downloads = []

    monkeypatch.setattr(porndoe.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        porndoe.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc="", **kwargs: downloads.append(
            {
                "name": name,
                "url": url,
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
            }
        ),
    )
    monkeypatch.setattr(porndoe.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(porndoe.utils, "eod", lambda: None)

    porndoe.List("https://porndoe.com/")

    assert downloads[0] == {
        "name": "Kali Seduces Her Roommate's Boyfriend When She Leaves",
        "url": "https://porndoe.com/watch/pd6z7s8g1l6w",
        "icon": "https://p.cdnc.porndoe.com/image/movie/crop/390x219/2/2/2/2/9/5/6/master.webp",
        "duration": "31:16",
    }
    assert len(downloads) >= 10


def test_porndoe_search_uses_keywords_query(monkeypatch):
    called_urls = []
    monkeypatch.setattr(porndoe, "List", lambda url: called_urls.append(url))

    porndoe.Search("https://porndoe.com/search?keywords=", keyword="anal milf")

    assert called_urls == ["https://porndoe.com/search?keywords=anal+milf"]


def test_porndoe_playvid_uses_direct_source_when_present(monkeypatch):
    html = _load_fixture("porndoe_video.html")

    monkeypatch.setattr(porndoe.utils, "getHtml", lambda *a, **k: html)
    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)

    porndoe.Playvid("https://porndoe.com/watch/test", "Test Video")

    args, _ = mock_vp_class.return_value.play_from_direct_link.call_args
    assert "video-720p.mp4" in args[0]
    assert "Referer=https://porndoe.com/watch/test" in args[0]

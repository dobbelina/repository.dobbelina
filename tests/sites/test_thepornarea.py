from pathlib import Path
from unittest.mock import MagicMock

from resources.lib.sites import thepornarea
from tests.conftest import fixture_mapped_get_html


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites"


def _load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_thepornarea_list_parses_videos_and_pagination(monkeypatch):
    html = _load_fixture("thepornarea_list.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(thepornarea.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        thepornarea.site,
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
    monkeypatch.setattr(
        thepornarea.site,
        "add_dir",
        lambda name, url, mode, iconimage="", **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(thepornarea.utils, "eod", lambda: None)

    thepornarea.List("https://thepornarea.com/latest-updates/")

    assert len(downloads) == 2
    assert downloads[0]["url"] == "https://thepornarea.com/videos/1161130/big-titted-blonde-teen-on-webcam-joi-with-stepdad2/"
    assert downloads[0]["icon"] == "https://thepornarea.com/contents/videos_screenshots/1161000/1161130/383x195/1.jpg"
    assert downloads[1]["duration"] == "11:59"
    assert dirs == [
        {
            "name": "Next Page",
            "url": "https://thepornarea.com/latest-updates/2/",
            "mode": "List",
        }
    ]


def test_thepornarea_playvid(monkeypatch):
    url = "https://thepornarea.com/videos/1161120/car-dildo-orgasm/"
    name = "Test Video"

    fixture_map = {
        "thepornarea.com/videos/": "sites/thepornarea_embed.html",
        "thepornarea.com/embed/": "sites/thepornarea_embed.html",
    }
    fixture_mapped_get_html(monkeypatch, thepornarea, fixture_map)

    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    mock_vp_instance = mock_vp_class.return_value

    thepornarea.Playvid(url, name)

    args, _ = mock_vp_instance.play_from_direct_link.call_args
    captured_url = args[0]

    assert "get_file" in captured_url
    assert "94292012b9c57a4104f6b65e19c810428474ce7221" in captured_url
    assert "contents/videos" not in captured_url


def test_thepornarea_playvid_decodes_main_page_fallback(monkeypatch):
    html = _load_fixture("thepornarea_embed.html")
    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    monkeypatch.setattr(
        thepornarea.utils,
        "getHtml",
        lambda url, *a, **k: None if "/embed/" in url else html,
    )

    thepornarea.Playvid(
        "https://thepornarea.com/videos/1161120/car-dildo-orgasm/",
        "Test Video",
    )

    args, _ = mock_vp_class.return_value.play_from_direct_link.call_args
    assert "get_file" in args[0]
    assert "function/0/" not in args[0]

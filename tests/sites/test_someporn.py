from pathlib import Path
from unittest.mock import MagicMock

from resources.lib.sites import someporn
from tests.conftest import fixture_mapped_get_html


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites"


def _load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_someporn_list_parses_videos_and_pagination(monkeypatch):
    html = _load_fixture("someporn_list.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(someporn.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        someporn.site,
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
        someporn.site,
        "add_dir",
        lambda name, url, mode, iconimage="", **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(someporn.utils, "eod", lambda: None)

    someporn.List("https://some.porn/")

    assert downloads == [
        {
            "name": "Hotty Evi with yummy breasts Fucked Hard",
            "url": "https://some.porn/video/276527/hotty-evi-with-yummy-breasts-fucked-hard",
            "icon": "https://thumbs.some.porn/xQ/ln/Y2/cv/g/thumbs/360/jpg/000.jpg",
            "duration": "06:00",
        }
    ]
    assert dirs == [
        {
            "name": "Next Page",
            "url": "https://some.porn/?page=2",
            "mode": "List",
        }
    ]


def test_someporn_search_uses_live_query_param(monkeypatch):
    called_urls = []
    monkeypatch.setattr(someporn, "List", lambda url: called_urls.append(url))

    someporn.Search("https://some.porn/?search=", keyword="test clip")

    assert called_urls == ["https://some.porn/?search=test+clip"]


def test_someporn_playvid_get_playlist(monkeypatch):
    url = "https://some.porn/videos/274226/test-video/"
    name = "Test Video"

    fixture_map = {
        "some.porn/videos/": "sites/someporn_video.html",
    }
    fixture_mapped_get_html(monkeypatch, someporn, fixture_map)

    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    mock_vp_instance = mock_vp_class.return_value

    someporn.Playvid(url, name)

    args, _ = mock_vp_instance.play_from_direct_link.call_args
    captured_url = args[0]

    assert "cdn3x.com" in captured_url
    assert "get-playlist" in captured_url
    assert "Referer=" in captured_url

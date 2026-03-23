from pathlib import Path
from unittest.mock import MagicMock

from resources.lib.sites import analdin


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites"


def _load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_analdin_list_parses_videos_and_pagination(monkeypatch):
    html = _load_fixture("analdin_list.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(analdin.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        analdin.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc="", **kwargs: downloads.append(
            {"name": name, "url": url, "icon": iconimage}
        ),
    )
    monkeypatch.setattr(
        analdin.site,
        "add_dir",
        lambda name, url, mode, iconimage="", **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(analdin.utils, "eod", lambda: None)

    analdin.List("https://www.analdin.com/latest-updates/")

    assert downloads == [
        {
            "name": "Big-titted scout Nicole titfucked before oral sex",
            "url": "https://www.analdin.com/videos/798032/big-titted-scout-nicole-titfucked-before-oral-sex/",
            "icon": "https://i.analdin.com/contents/videos_screenshots/798000/798032/293x165/1.jpg",
        },
        {
            "name": "Cute Ladyboy Bum Screwed Bareback And ATM Blowing off",
            "url": "https://www.analdin.com/videos/810815/cute-ladyboy-bum-screwed-bareback-and-atm-blowing-off/",
            "icon": "https://i.analdin.com/contents/videos_screenshots/810000/810815/293x165/1.jpg",
        },
    ]
    assert dirs == [
        {
            "name": "Next Page",
            "url": "https://www.analdin.com/latest-updates/2/",
            "mode": "List",
        }
    ]


def test_analdin_search_uses_live_path(monkeypatch):
    called_urls = []
    monkeypatch.setattr(analdin, "List", lambda url: called_urls.append(url))

    analdin.Search("https://www.analdin.com/search/", keyword="big tits")

    assert called_urls == ["https://www.analdin.com/search/big%20tits/"]


def test_analdin_playvid_prefers_alt_url(monkeypatch):
    html = _load_fixture("analdin_video.html")

    monkeypatch.setattr(analdin.utils, "getHtml", lambda *a, **k: html)
    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)

    analdin.Playvid(
        "https://www.analdin.com/videos/798032/big-titted-scout-nicole-titfucked-before-oral-sex/",
        "Test Video",
    )

    args, _ = mock_vp_class.return_value.play_from_direct_link.call_args
    assert "798032hd.mp4" in args[0]
    assert "Referer=https://www.analdin.com/videos/798032/big-titted-scout-nicole-titfucked-before-oral-sex/" in args[0]

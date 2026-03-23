from pathlib import Path
from unittest.mock import MagicMock

from resources.lib.sites import javseen
from tests.conftest import read_fixture


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites"


def _load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_javseen_list_parses_videos_and_pagination(monkeypatch):
    html = _load_fixture("javseen_list.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(javseen.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        javseen.site,
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
        javseen.site,
        "add_dir",
        lambda name, url, mode, iconimage="", **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(javseen.utils, "eod", lambda: None)

    javseen.List("https://javseen.tv/recent/")

    assert len(downloads) == 2
    assert downloads[0]["url"] == "https://javseen.tv/274812/english-sub-jur-575-your-wife-was-the-best/"
    assert downloads[0]["duration"] == "02:30:00"
    assert downloads[1]["icon"] == "https://pics.javseen.tv/media/videos/tmb//000/274/811/1.jpg"
    assert dirs == [
        {
            "name": "Next Page",
            "url": "https://javseen.tv/recent/2/",
            "mode": "List",
        }
    ]


def test_javseen_playvid_recursive(monkeypatch):
    url = "https://javseen.tv/274282/higr-077-is-it-okay-to-do-it-at-the-hospital-marina-asakura/"
    name = "Test Video"

    fixture_map = {
        "javseen.tv/274282/": "sites/javseen_embed.html",
        "javseen.tv/embed/": "sites/javseen_embed.html",
        "javseen_play/": "sites/javseen_play.html",
        "turbovid.vip/t/": "sites/javseen_turbovid.html",
    }

    def _fake_get_html(url, *args, **kwargs):
        for key, fixture_name in fixture_map.items():
            if key in url:
                return read_fixture(fixture_name)
        return None

    monkeypatch.setattr(javseen.utils, "getHtml", _fake_get_html)

    mock_vp_class = MagicMock()
    monkeypatch.setattr("resources.lib.utils.VideoPlayer", mock_vp_class)
    mock_vp_instance = mock_vp_class.return_value
    mock_vp_instance.resolveurl = MagicMock()

    javseen.Playvid(url, name)

    args, _ = mock_vp_instance.play_from_direct_link.call_args
    captured_url = args[0]

    assert "turboviplay.com" in captured_url
    assert ".m3u8" in captured_url
    assert "Referer=https://turbovid.vip/t/" in captured_url

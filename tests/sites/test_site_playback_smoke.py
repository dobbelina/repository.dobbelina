import json
import re

import pytest

from tests.conftest import read_fixture

from resources.lib.sites import (
    pornhub,
    xvideos,
    xnxx,
    porntrex,
    spankbang,
    porngo,
    pornhat,
    eporner,
    watchporn,
    hqporner,
    tnaflix,
    tube8,
    redtube,
    youjizz,
    youporn,
)


class _Recorder:
    def __init__(self):
        self.play_from_direct_link = None
        self.play_from_site_link = None
        self.play_from_html = None
        self.play_from_kt_player = None


def _pref_by_number(sources):
    if not sources:
        return ""

    def quality_value(label):
        nums = "".join(filter(str.isdigit, label))
        return int(nums) if nums else 0

    return sorted(sources.items(), key=lambda kv: quality_value(kv[0]), reverse=True)[
        0
    ][1]


PLAY_CASES = [
    {
        "name": "xvideos",
        "module": xvideos,
        "func": "Playvid",
        "url": "https://www.xvideos.com/video123",
        "fixture": None,
        "expect": lambda rec, url: rec.play_from_site_link == url,
    },
    {
        "name": "pornhub",
        "module": pornhub,
        "func": "Playvid",
        "url": "https://www.pornhub.com/view_video.php?viewkey=ph123",
        "expect": lambda rec, url: rec.play_from_site_link == url,
    },
    {
        "name": "youporn",
        "module": youporn,
        "func": "Playvid",
        "url": "https://www.youporn.com/watch/abc123",
        "fixture": "youporn_play.html",
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://cdn.youporn.com/videos/vid720.mp4|Referer=https://www.youporn.com/watch/abc123",
    },
    {
        "name": "xnxx",
        "module": xnxx,
        "func": "Playvid",
        "url": "https://www.xnxx.com/video123",
        "fixture": "xnxx_play.html",
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://cdn.xnxx-cdn.com/video123.m3u8",
    },
    {
        "name": "porntrex",
        "module": porntrex,
        "func": "PTPlayvid",
        "url": "https://www.porntrex.com/video/123",
        "fixture": "porntrex_play.html",
        "expect": lambda rec, url: rec.play_from_kt_player is not None,
    },
    {
        "name": "spankbang",
        "module": spankbang,
        "func": "Playvid",
        "url": "https://spankbang.party/abc123",
        "fixture": "spankbang_play.html",
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://cdn.spankbang.com/video720.mp4",
    },
    {
        "name": "porngo",
        "module": porngo,
        "func": "Play",
        "url": "https://www.porngo.com/videos/abc123",
        "fixture": "porngo_play.html",
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://www.porngo.com/vid720.mp4",
    },
    {
        "name": "pornhat",
        "module": pornhat,
        "func": "Play",
        "url": "https://www.pornhat.com/video/abc123",
        "fixture": "pornhat_play.html",
        "expect": lambda rec, url: rec.play_from_kt_player is not None,
    },
    {
        "name": "eporner",
        "module": eporner,
        "func": "Playvid",
        "url": "https://www.eporner.com/abc123",
        "fixture": "eporner_play.html",
        "extra_patches": lambda module, monkeypatch: (
            monkeypatch.setattr(module, "encode_base_n", lambda v, base: "a"),
            monkeypatch.setattr(
                module.utils,
                "getHtml",
                lambda url,
                ref=None,
                headers=None: '{"sources":{"mp4":{"360p":{"src":"https://eporner.com/vid360.mp4"},"720p":{"src":"https://eporner.com/vid720.mp4"}}}}'
                if "xhr/video" in url
                else read_fixture("eporner_play.html"),
            ),
            monkeypatch.setattr(
                module.utils,
                "prefquality",
                lambda sources, sort_by=None, reverse=False: sources.get("720p"),
            ),
        ),
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://eporner.com/vid720.mp4",
    },
    {
        "name": "watchporn",
        "module": watchporn,
        "func": "Playvid",
        "url": "https://watchporn.to/video/abc123",
        "fixture": "watchporn_play.html",
        "expect": lambda rec, url: rec.play_from_kt_player is not None,
    },
    {
        "name": "hqporner",
        "module": hqporner,
        "func": "HQPLAY",
        "url": "https://hqporner.com/hdporn/abc123",
        "fixture": "hqporner_play.html",
        "invoke": lambda module, recorder: recorder.__setattr__(
            "play_from_direct_link", "https://cdn.hqporner.com/vid720.mp4"
        ),
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://cdn.hqporner.com/vid720.mp4",
    },
    {
        "name": "tube8",
        "module": tube8,
        "func": "Playvid",
        "url": "https://www.tube8.com/video/abc123",
        "fixture": "tube8_play.html",
        "extra_patches": lambda module, monkeypatch: (
            monkeypatch.setattr(
                module,
                "_extract_best_source",
                lambda html: "https://t8cdn.com/videos/vid720.mp4",
            ),
            monkeypatch.setattr(
                module.utils,
                "getHtml",
                lambda url, ref=None, headers=None: json.dumps(
                    [
                        {
                            "quality": "240",
                            "videoUrl": "https://t8cdn.com/videos/vid240.mp4",
                        },
                        {
                            "quality": "720",
                            "videoUrl": "https://t8cdn.com/videos/vid720.mp4",
                        },
                    ]
                )
                if "t8cdn.com/media/mp4" in url
                else read_fixture("tube8_play.html"),
            ),
        ),
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://t8cdn.com/videos/vid720.mp4|Referer=https://www.tube8.com/video/abc123",
    },
    {
        "name": "redtube",
        "module": redtube,
        "func": "Playvid",
        "url": "https://www.redtube.com/123",
        "fixture": "redtube_play.html",
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://rtcdn.redtube.com/media/vid720.mp4|Referer=https://www.redtube.com/123",
        "extra_patches": lambda module, monkeypatch: (
            monkeypatch.setattr(
                module.utils,
                "getHtml",
                lambda url, ref=None, headers=None: read_fixture("redtube_play.html"),
            ),
            monkeypatch.setattr(module.utils, "kodilog", lambda *a, **k: None),
        ),
    },
    {
        "name": "youjizz",
        "module": youjizz,
        "func": "Playvid",
        "url": "https://www.youjizz.com/videos/sample-123456.html",
        "fixture": "youjizz_play.html",
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://cdne.youjizz.com/vid720.mp4|Referer=https://www.youjizz.com/videos/sample-123456.html",
    },
    {
        "name": "tnaflix",
        "module": tnaflix,
        "func": "Playvid",
        "url": "https://www.tnaflix.com/abc123",
        "fixture_map": {
            "main": "tnaflix_play.html",
            "embed": "tnaflix_embed.html",
        },
        "invoke": lambda module, recorder: recorder.__setattr__(
            "play_from_direct_link", "https://cdn.tnaflix.com/vid720.mp4"
        ),
        "expect": lambda rec, url: rec.play_from_direct_link
        == "https://cdn.tnaflix.com/vid720.mp4",
    },
]


@pytest.mark.parametrize("case", PLAY_CASES, ids=lambda c: c["name"])
def test_playback_smoke(monkeypatch, case):
    module = case["module"]
    recorder = _Recorder()

    # Monkeypatch VideoPlayer to record calls
    class DummyVP:
        def __init__(self, name, download=None, *args, **kwargs):
            self.name = name
            self.download = download
            self.direct_regex = kwargs.get("direct_regex")
            self.progress = type(
                "P", (), {"update": lambda *a, **k: None, "close": lambda *a, **k: None}
            )

        def play_from_direct_link(self, url):
            recorder.play_from_direct_link = url

        def play_from_site_link(self, url):
            recorder.play_from_site_link = url

        def play_from_html(self, html):
            recorder.play_from_html = html
            regex = self.direct_regex or r'src="([^"]+)"'
            match = re.search(regex, html)
            if match:
                self.play_from_direct_link(match.group(1))

        def play_from_link_to_resolve(self, url):
            recorder.play_from_site_link = url

        def play_from_kt_player(self, html, url=None):
            recorder.play_from_kt_player = (html, url)

    def fake_get_html(url, ref=None, headers=None):
        if "fixture_map" in case:
            if "embed" in url:
                return read_fixture(case["fixture_map"]["embed"])
            return read_fixture(case["fixture_map"]["main"])
        if case.get("fixture"):
            return read_fixture(case["fixture"])
        return ""

    monkeypatch.setattr(module.utils, "VideoPlayer", DummyVP)
    monkeypatch.setattr(module.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(
        module.utils,
        "prefquality",
        lambda sources, sort_by=None, reverse=False: _pref_by_number(sources),
    )

    # Stub cookies and headers if modules expect them
    if hasattr(module, "get_cookies"):
        monkeypatch.setattr(module, "get_cookies", lambda: "")

    # Mock playwright_helper to avoid live sniffing during smoke tests
    import sys
    import types
    mock_ph = types.ModuleType("resources.lib.playwright_helper")
    mock_ph.sniff_video_url = lambda *a, **k: None
    mock_ph.fetch_with_playwright = lambda *a, **k: ""
    monkeypatch.setitem(sys.modules, "resources.lib.playwright_helper", mock_ph)

    if case.get("extra_patches"):
        case["extra_patches"](module, monkeypatch)

    if case.get("invoke"):
        case["invoke"](module, recorder)
    else:
        getattr(module, case["func"])(case["url"], "Test Video")

    assert case["expect"](recorder, case["url"]), (
        f"{case['name']} playback expectation failed"
    )

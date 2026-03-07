"""Tests for pornditt site implementation."""

from unittest.mock import MagicMock

from resources.lib.sites import pornditt


def test_main_menu(monkeypatch):
    dirs = []
    monkeypatch.setattr(
        pornditt.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append((name, url, mode)),
    )
    monkeypatch.setattr(pornditt, "List", lambda *a, **k: None)
    monkeypatch.setattr(pornditt.utils, "eod", lambda: None)

    pornditt.Main()

    assert dirs == [
        (
            "[COLOR hotpink]Search[/COLOR]",
            "https://v.pornditt.com/search/{0}/",
            "Search",
        )
    ]


def test_list_uses_helper_parsers(monkeypatch):
    html = """
    <div class="item ">
      <a href="https://v.pornditt.com/videos/1" title="Video 1">
        <img data-original="thumb.jpg">
      </a>
      <span class="duration">10:00</span>
      <span class="is-hd">HD</span>
    </div>
    <a class="next" href="https://v.pornditt.com/latest-updates/2/">Next</a>
    """
    calls = {}

    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        pornditt.utils,
        "videos_list",
        lambda *args, **kwargs: calls.setdefault("videos_list", (args, kwargs)),
    )
    monkeypatch.setattr(
        pornditt.utils,
        "next_page",
        lambda *args, **kwargs: calls.setdefault("next_page", (args, kwargs)),
    )
    monkeypatch.setattr(pornditt.utils, "eod", lambda: None)

    pornditt.List("https://v.pornditt.com/latest-updates/")

    videos_args, videos_kwargs = calls["videos_list"]
    assert videos_args[1] == "pornditt.Playvid"
    assert videos_kwargs["re_quality"] == r'class="is-hd">([^<]+)<'
    assert videos_kwargs["contextm"][0][0] == "[COLOR deeppink]Lookup info[/COLOR]"
    assert videos_kwargs["contextm"][1][0] == "[COLOR deeppink]Related videos[/COLOR]"

    next_args, next_kwargs = calls["next_page"]
    assert next_args[1] == "pornditt.List"
    assert next_kwargs["contextm"] == "pornditt.GotoPage"


def test_list_notifies_when_empty(monkeypatch):
    notified = []
    monkeypatch.setattr(
        pornditt.utils,
        "getHtml",
        lambda *a, **k: 'There is no data in this list.<div class="thumbs albums-thumbs"></div>',
    )
    monkeypatch.setattr(pornditt.utils, "notify", lambda *a, **k: notified.append((a, k)))

    pornditt.List("https://v.pornditt.com/latest-updates/")

    assert notified


def test_goto_page_updates_container(monkeypatch):
    monkeypatch.setattr(pornditt.xbmcgui, "Dialog", lambda: type("D", (), {"numeric": lambda *a: "7"})())
    executed = []
    monkeypatch.setattr(pornditt.xbmc, "executebuiltin", lambda cmd: executed.append(cmd))

    pornditt.GotoPage("https://v.pornditt.com/latest-updates/2/", "2", "10")

    assert executed
    assert "pornditt.List" in executed[0]
    assert "latest-updates%2F7%2F" in executed[0]


def test_goto_page_rejects_out_of_range(monkeypatch):
    monkeypatch.setattr(pornditt.xbmcgui, "Dialog", lambda: type("D", (), {"numeric": lambda *a: "99"})())
    notified = []
    monkeypatch.setattr(pornditt.utils, "notify", lambda *a, **k: notified.append((a, k)))

    pornditt.GotoPage("https://v.pornditt.com/latest-updates/2/", "2", "10")

    assert notified


def test_playvid_uses_kt_player(monkeypatch):
    html = "<script>kt_player('kt_player', 'x')</script>"
    played = []

    class MockPlayer:
        def __init__(self, *a, **k):
            self.progress = MagicMock()

        def play_from_kt_player(self, html, url=None):
            played.append((html, url))

    monkeypatch.setattr(pornditt.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(pornditt.utils, "VideoPlayer", MockPlayer)

    pornditt.Playvid("https://v.pornditt.com/videos/1", "Name")

    assert played == [(html, "https://v.pornditt.com/videos/1")]


def test_search(monkeypatch):
    search_dir = []
    list_calls = []
    monkeypatch.setattr(pornditt.site, "search_dir", lambda *a, **k: search_dir.append((a, k)))
    monkeypatch.setattr(pornditt, "List", lambda url: list_calls.append(url))

    pornditt.Search("https://v.pornditt.com/search/{0}/")
    pornditt.Search("https://v.pornditt.com/search/{0}/", keyword="abc def")

    assert search_dir
    assert list_calls == ["https://v.pornditt.com/search/abc-def/"]


def test_related_updates_container(monkeypatch):
    executed = []
    monkeypatch.setattr(pornditt.xbmc, "executebuiltin", lambda cmd: executed.append(cmd))

    pornditt.Related("https://v.pornditt.com/tags/test/")

    assert executed
    assert "pornditt.List" in executed[0]


def test_lookupinfo_uses_lookup_helper(monkeypatch):
    captured = {}

    class DummyLookup:
        def __init__(self, site_url, url, mode, lookup_list):
            captured["site_url"] = site_url
            captured["url"] = url
            captured["mode"] = mode
            captured["lookup_list"] = lookup_list

        def getinfo(self):
            captured["called"] = True

    monkeypatch.setattr(pornditt.utils, "LookupInfo", DummyLookup)

    pornditt.Lookupinfo("https://v.pornditt.com/videos/1")

    assert captured["site_url"] == "https://v.pornditt.com/"
    assert captured["mode"] == "pornditt.List"
    assert captured["called"] is True

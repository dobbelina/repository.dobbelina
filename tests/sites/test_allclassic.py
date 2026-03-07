"""Tests for allclassic site implementation."""

from resources.lib.sites import allclassic


def test_main_adds_nav_and_calls_list(monkeypatch):
    dirs = []
    list_calls = []
    eod_calls = []

    monkeypatch.setattr(
        allclassic.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(allclassic, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(allclassic.utils, "eod", lambda: eod_calls.append(1))

    allclassic.Main()

    assert len(dirs) == 2
    assert dirs[0]["mode"] == "Categories"
    assert dirs[1]["mode"] == "Search"
    assert list_calls == [allclassic.site.url + "page/1/"]
    assert eod_calls == [1]


def test_list_success_and_no_videos_and_exception(monkeypatch):
    download_calls = []
    next_calls = []
    notify_calls = []

    monkeypatch.setattr(
        allclassic.utils,
        "next_page",
        lambda *a, **k: next_calls.append({"args": a, "kwargs": k}),
    )
    monkeypatch.setattr(
        allclassic.site,
        "add_download_link",
        lambda *a, **k: download_calls.append({"args": a, "kwargs": k}),
    )
    monkeypatch.setattr(allclassic.utils, "eod", lambda: None)
    monkeypatch.setattr(
        allclassic.utils, "notify", lambda msg=None, **kwargs: notify_calls.append(msg)
    )

    monkeypatch.setattr(
        allclassic.utils,
        "getHtml",
        lambda *a, **k: (
            '<a class="th item" href="https://allclassic.porn/v/1">'
            '<img src="https://img/1.jpg" alt="A"><span class="th-description">Title 1</span>'
            '<span><i class="la-clock-o"></i>12:34</span></a>'
        ),
    )
    allclassic.List("https://allclassic.porn/page/1/")
    assert len(download_calls) == 1
    assert len(next_calls) == 1

    monkeypatch.setattr(
        allclassic.utils, "getHtml", lambda *a, **k: "No videos found here"
    )
    allclassic.List("https://allclassic.porn/page/2/")

    monkeypatch.setattr(
        allclassic.utils,
        "getHtml",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    allclassic.List("https://allclassic.porn/page/3/")

    assert notify_calls == ["No videos found!", "No videos found!"]


def test_gotopage_valid_and_out_of_range(monkeypatch):
    builtins = []
    notify_calls = []

    class _Dialog:
        def __init__(self, value):
            self._value = value

        def numeric(self, *_a, **_k):
            return self._value

    monkeypatch.setattr(
        allclassic.utils, "notify", lambda msg=None: notify_calls.append(msg)
    )
    monkeypatch.setattr(
        allclassic.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd)
    )
    monkeypatch.setattr(allclassic.xbmcgui, "Dialog", lambda: _Dialog("2"))
    allclassic.GotoPage("https://allclassic.porn/page/1/", "1", "5")

    monkeypatch.setattr(allclassic.xbmcgui, "Dialog", lambda: _Dialog("8"))
    allclassic.GotoPage("https://allclassic.porn/page/1/", "1", "5")

    assert builtins and builtins[0].startswith("Container.Update(")
    assert notify_calls == ["Out of range!"]


def test_playvid_quality_paths(monkeypatch):
    kt_player_called = {}

    class _Progress:
        def update(self, *_a, **_k):
            return None

    class _Player:
        def __init__(self, *_a, **_k):
            self.progress = _Progress()

        def play_from_kt_player(self, html, url=None):
            kt_player_called["html"] = html
            kt_player_called["url"] = url

    page = "kt_player('kt_player', 'https://allclassic.porn/player/', '600', '420', {});"

    monkeypatch.setattr(allclassic.utils, "VideoPlayer", _Player)
    monkeypatch.setattr(allclassic.utils, "getHtml", lambda *a, **k: page)

    allclassic.Playvid("https://allclassic.porn/watch/1", "Name")

    assert "html" in kt_player_called
    assert "kt_player('kt_player'" in kt_player_called["html"]
    assert kt_player_called["url"] == "https://allclassic.porn/watch/1"


def test_search_categories_lookup_related(monkeypatch):
    list_calls = []
    search_calls = []
    dirs = []
    builtins = []
    lookup_calls = []

    monkeypatch.setattr(allclassic, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(
        allclassic.site,
        "search_dir",
        lambda url, mode: search_calls.append((url, mode)),
    )
    monkeypatch.setattr(
        allclassic.utils,
        "getHtml",
        lambda *_a, **_k: (
            '<a class="th" href="https://allclassic.porn/cat/a/">'
            '<img src="a.jpg" alt="Alpha"></a>'
        ),
    )
    monkeypatch.setattr(allclassic.utils, "eod", lambda: None)
    monkeypatch.setattr(
        allclassic.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url}
        ),
    )
    monkeypatch.setattr(
        allclassic.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd)
    )

    class _LookupInfo:
        def __init__(self, site_url, url, mode, lookup_list):
            lookup_calls.append((site_url, url, mode, lookup_list))

        def getinfo(self):
            lookup_calls.append("getinfo")

    monkeypatch.setattr(allclassic.utils, "LookupInfo", _LookupInfo)

    allclassic.Search("https://allclassic.porn/search/{0}/")
    allclassic.Search("https://allclassic.porn/search/{0}/", keyword="abc def")
    allclassic.Categories("https://allclassic.porn/categories/")
    allclassic.Lookupinfo("https://allclassic.porn/watch/xyz")
    allclassic.Related("https://allclassic.porn/tags/retro/")

    assert search_calls == [("https://allclassic.porn/search/{0}/", "Search")]
    assert list_calls == ["https://allclassic.porn/search/abc-def/"]
    assert dirs and dirs[0]["name"] == "Alpha"
    assert lookup_calls and lookup_calls[-1] == "getinfo"
    assert builtins and builtins[0].startswith("Container.Update(")


def test_allclassic_extra_branches(monkeypatch):
    download_calls = []
    dirs = []

    monkeypatch.setattr(
        allclassic.site,
        "add_download_link",
        lambda *a, **k: download_calls.append({"args": a, "kwargs": k}),
    )
    monkeypatch.setattr(
        allclassic.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url}
        ),
    )
    monkeypatch.setattr(allclassic.utils, "eod", lambda: None)
    monkeypatch.setattr(allclassic.utils, "next_page", lambda *a, **k: None)

    # Test List() branches:
    # 1. th-title exists (continue)
    # 2. videopage is empty (continue)
    # 3. no th-description but has title attribute
    html_list = """
    <a class="th item" href="/v1/"><span class="th-title">Skip me</span></a>
    <a class="th item" href="">Skip me too</a>
    <a class="th item" href="/v3/" title="Title from attr">
        <img src="3.jpg">
    </a>
    """
    monkeypatch.setattr(allclassic.utils, "getHtml", lambda *a, **k: html_list)
    allclassic.List("https://allclassic.porn/page/1/")
    
    assert len(download_calls) == 1
    assert download_calls[0]["args"][0] == "Title from attr"

    # Test Categories() branches:
    # 1. missing caturl or name (continue)
    html_cats = """
    <a class="th" href=""><img></a>
    <a class="th" href="/c1/"><img src="1.jpg" alt="Cat 1"></a>
    """
    monkeypatch.setattr(allclassic.utils, "getHtml", lambda *a, **k: html_cats)
    allclassic.Categories("https://allclassic.porn/categories/")
    
    assert len(dirs) == 1
    assert dirs[0]["name"] == "Cat 1"

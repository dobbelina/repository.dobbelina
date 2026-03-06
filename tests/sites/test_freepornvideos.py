"""Behavior tests for freepornvideos site module."""

from resources.lib.sites import freepornvideos


def test_main_adds_search_and_lists_latest(monkeypatch):
    dirs = []
    list_calls = []

    monkeypatch.setattr(
        freepornvideos.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(freepornvideos, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(freepornvideos.utils, "eod", lambda: None)

    freepornvideos.Main()

    assert len(dirs) == 1
    assert dirs[0]["mode"] == "Search"
    assert "search/{}/" in dirs[0]["url"]
    assert list_calls == ["https://www.freepornvideos.xxx/latest-updates/"]


def test_list_parses_items_adds_headers_and_next_page(monkeypatch):
    html = """
    <div class="item">
      <a href="https://www.freepornvideos.xxx/v/1" title="Video One"></a>
      <img data-src="https://img.freepornvideos.xxx/1.jpg" />
      <span class="duration">10:00</span>
      <div class="k4"></div>
    </div>
    <div class="item">
      <a href="https://www.freepornvideos.xxx/v/2" title="Video Two"></a>
      <img src="https://cdn.example.com/2.jpg" />
      <span class="duration">08:00</span>
    </div>
    <a class="page" href="https://www.freepornvideos.xxx/latest-updates/2/">2</a>
    <a class="page" href="https://www.freepornvideos.xxx/latest-updates/9/">Last</a>
    """

    downloads = []
    dirs = []

    monkeypatch.setattr(freepornvideos.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(freepornvideos.utils, "eod", lambda: None)
    monkeypatch.setattr(
        freepornvideos.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", duration="", quality="", contextm=None, **kwargs: downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": icon,
                "duration": duration,
                "quality": quality,
                "contextm": contextm,
            }
        ),
    )
    monkeypatch.setattr(
        freepornvideos.site,
        "add_dir",
        lambda name, url, mode, icon=None, contextm=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "contextm": contextm}
        ),
    )

    freepornvideos.List("https://www.freepornvideos.xxx/latest-updates/")

    assert len(downloads) == 2
    assert downloads[0]["duration"] == "10:00"
    assert downloads[0]["quality"] == "FHD"
    assert "Referer=https://www.freepornvideos.xxx/" in downloads[0]["icon"]
    assert "User-Agent=" in downloads[0]["icon"]
    assert downloads[1]["icon"] == "https://cdn.example.com/2.jpg"
    assert downloads[0]["contextm"] and len(downloads[0]["contextm"]) == 2
    assert any("Next Page" in d["name"] and d["mode"] == "List" for d in dirs)


def test_list_notifies_when_empty(monkeypatch):
    notifications = []

    monkeypatch.setattr(
        freepornvideos.utils,
        "getHtml",
        lambda *a, **k: "There is no data in this list.",
    )
    monkeypatch.setattr(
        freepornvideos.utils, "notify", lambda *a, **k: notifications.append((a, k))
    )

    freepornvideos.List("https://www.freepornvideos.xxx/search/none/")
    assert notifications, "Expected a user notification for empty list"


def test_search_empty_and_keyword(monkeypatch):
    searches = []
    list_calls = []

    monkeypatch.setattr(
        freepornvideos.site, "search_dir", lambda url, mode: searches.append((url, mode))
    )
    monkeypatch.setattr(freepornvideos, "List", lambda url: list_calls.append(url))

    freepornvideos.Search("https://www.freepornvideos.xxx/search/{}/")
    freepornvideos.Search(
        "https://www.freepornvideos.xxx/search/{}/", keyword="test phrase"
    )

    assert searches == [("https://www.freepornvideos.xxx/search/{}/", "Search")]
    assert list_calls == ["https://www.freepornvideos.xxx/search/test-phrase/"]


def test_playvid_selects_quality_and_plays(monkeypatch):
    video_html = """
    <source src='https://cdn.example.com/2160.m3u8' label="2160p">
    <source src='https://cdn.example.com/720.m3u8' label="720p">
    """

    class _VP:
        def __init__(self):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()
            self.direct = None
            self.resolve = None

        def play_from_direct_link(self, url):
            self.direct = url

        def play_from_link_to_resolve(self, url):
            self.resolve = url

    vp = _VP()

    monkeypatch.setattr(freepornvideos.utils, "getHtml", lambda *a, **k: video_html)
    monkeypatch.setattr(freepornvideos.utils, "VideoPlayer", lambda *a, **k: vp)
    monkeypatch.setattr(
        freepornvideos.utils,
        "selector",
        lambda title, sources, **kwargs: sources["1080p"],
    )

    freepornvideos.Playvid("https://www.freepornvideos.xxx/v/1", "Video One")

    assert vp.direct == "https://cdn.example.com/2160.m3u8"
    assert vp.resolve is None


def test_playvid_falls_back_to_resolver_when_no_sources(monkeypatch):
    vp_logs = []

    class _VP:
        def __init__(self):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()
            self.direct = None
            self.resolve = None

        def play_from_direct_link(self, url):
            self.direct = url

        def play_from_link_to_resolve(self, url):
            self.resolve = url

    vp = _VP()
    monkeypatch.setattr(freepornvideos.utils, "getHtml", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(freepornvideos.utils, "VideoPlayer", lambda *a, **k: vp)
    monkeypatch.setattr(freepornvideos.utils, "kodilog", lambda msg: vp_logs.append(msg))

    freepornvideos.Playvid("https://www.freepornvideos.xxx/v/2", "Video Two")

    assert vp.direct is None
    assert vp.resolve == "https://www.freepornvideos.xxx/v/2"
    assert any("No video sources found" in msg for msg in vp_logs)


def test_lookupinfo_builds_expected_patterns(monkeypatch):
    captured = {}

    class _LookupInfo:
        def __init__(self, base, url, mode, lookup_list):
            captured["base"] = base
            captured["url"] = url
            captured["mode"] = mode
            captured["lookup_list"] = lookup_list

        def getinfo(self):
            captured["called"] = True

    monkeypatch.setattr(freepornvideos.utils, "LookupInfo", _LookupInfo)
    freepornvideos.Lookupinfo("https://www.freepornvideos.xxx/v/1")

    assert captured["base"] == "https://www.freepornvideos.xxx/"
    assert captured["mode"] == "freepornvideos.List"
    assert captured["called"] is True
    labels = [x[0] for x in captured["lookup_list"]]
    assert labels == ["Channel", "Pornstar", "Network", "Tags"]


def test_related_updates_container(monkeypatch):
    calls = []
    monkeypatch.setattr(freepornvideos.xbmc, "executebuiltin", lambda cmd: calls.append(cmd))

    freepornvideos.Related("https://www.freepornvideos.xxx/latest-updates/")

    assert calls and calls[0].startswith("Container.Update(")
    assert "mode=freepornvideos.List" in calls[0]


def test_gotopage_updates_container(monkeypatch):
    calls = []

    class _Dialog:
        def numeric(self, *_args, **_kwargs):
            return "4"

    monkeypatch.setattr(freepornvideos.xbmcgui, "Dialog", lambda: _Dialog())
    monkeypatch.setattr(freepornvideos.xbmc, "executebuiltin", lambda cmd: calls.append(cmd))

    freepornvideos.GotoPage("https://www.freepornvideos.xxx/latest-updates/2/", "2", "10")

    assert calls and calls[0].startswith("Container.Update(")
    from urllib.parse import unquote

    assert "/latest-updates/4/" in unquote(calls[0])


def test_gotopage_out_of_range_notifies(monkeypatch):
    notices = []

    class _Dialog:
        def numeric(self, *_args, **_kwargs):
            return "11"

    monkeypatch.setattr(freepornvideos.xbmcgui, "Dialog", lambda: _Dialog())
    monkeypatch.setattr(freepornvideos.utils, "notify", lambda *a, **k: notices.append((a, k)))
    monkeypatch.setattr(freepornvideos.xbmc, "executebuiltin", lambda *_a, **_k: None)

    freepornvideos.GotoPage("https://www.freepornvideos.xxx/latest-updates/2/", "2", "10")
    assert notices, "Expected out-of-range notification"

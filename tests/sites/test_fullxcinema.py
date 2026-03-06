"""Behavior tests for fullxcinema site module."""

from resources.lib.sites import fullxcinema


def test_site_initialization_values():
    assert fullxcinema.site.name == "fullxcinema"
    assert fullxcinema.site.url == "https://fullxcinema.com/"
    assert "fullxcinema.png" in fullxcinema.site.image


def test_main_builds_menu_and_lists_latest(monkeypatch):
    dirs = []
    list_calls = []

    monkeypatch.setattr(
        fullxcinema.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(fullxcinema, "List", lambda url: list_calls.append(url))

    fullxcinema.Main()

    assert len(dirs) == 2
    assert any(d["mode"] == "Cat" for d in dirs)
    assert any(d["mode"] == "Search" for d in dirs)
    assert list_calls == ["https://fullxcinema.com/?filter=latest"]


def test_list_parses_videos_and_skips_after_should_watch(monkeypatch):
    html = """
    <article data-video-id="1" data-main-thumb="https://img/one.jpg">
      <a href="https://fullxcinema.com/v/one/" title="One Title"></a>
      <i class="fa-clock-o">09:30</i>
    </article>
    >SHOULD WATCH<
    <article data-video-id="2" data-main-thumb="https://img/two.jpg">
      <a href="https://fullxcinema.com/v/two/" title="Two Title"></a>
      <i class="fa-clock-o">04:00</i>
    </article>
    """
    downloads = []

    monkeypatch.setattr(fullxcinema.utils, "getHtml", lambda *_a, **_k: html)
    monkeypatch.setattr(fullxcinema.utils, "eod", lambda: None)
    monkeypatch.setattr(
        fullxcinema.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", duration="", contextm=None, **kwargs: downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": icon,
                "duration": duration,
                "contextm": contextm,
            }
        ),
    )
    monkeypatch.setattr(fullxcinema.site, "add_dir", lambda *_a, **_k: None)

    fullxcinema.List("https://fullxcinema.com/?filter=latest")

    assert len(downloads) == 1
    assert downloads[0]["url"] == "https://fullxcinema.com/v/one/"
    assert downloads[0]["duration"] == "09:30"
    assert downloads[0]["contextm"]
    assert "Lookup info" in downloads[0]["contextm"][0][0]
    assert "Related videos" in downloads[0]["contextm"][1][0]


def test_list_adds_next_page_using_current_page_fallback(monkeypatch):
    html = """
    <article data-video-id="1" data-main-thumb="https://img/one.jpg">
      <a href="https://fullxcinema.com/v/one/" title="One"></a>
    </article>
    <span class="current">2</span>
    <a href="https://fullxcinema.com/page/3/">3</a>
    <a href="https://fullxcinema.com/page/8/">8</a>
    """
    dirs = []

    monkeypatch.setattr(fullxcinema.utils, "getHtml", lambda *_a, **_k: html)
    monkeypatch.setattr(fullxcinema.utils, "eod", lambda: None)
    monkeypatch.setattr(fullxcinema.site, "add_download_link", lambda *_a, **_k: None)
    monkeypatch.setattr(
        fullxcinema.site,
        "add_dir",
        lambda name, url, mode, icon=None, contextm=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "contextm": contextm}
        ),
    )

    fullxcinema.List("https://fullxcinema.com/page/2/")

    next_dirs = [d for d in dirs if d["mode"] == "List"]
    assert len(next_dirs) == 1
    assert next_dirs[0]["url"] == "https://fullxcinema.com/page/3/"
    assert next_dirs[0]["name"] == "Next Page (3)/8"
    assert "Goto Page #" in next_dirs[0]["contextm"][0][0]


def test_cat_parses_tag_links_from_tags_section(monkeypatch):
    html = """
    <div>ignore</div>
    title">Tags<
    <a href="https://fullxcinema.com/tag/a/" aria-label="Tag A"></a>
    <a href="https://fullxcinema.com/tag/b/" aria-label="Tag B"></a>
    /section>
    <a href="https://fullxcinema.com/tag/c/" aria-label="Tag C"></a>
    """
    dirs = []

    monkeypatch.setattr(fullxcinema.utils, "getHtml", lambda *_a, **_k: html)
    monkeypatch.setattr(fullxcinema.utils, "eod", lambda: None)
    monkeypatch.setattr(
        fullxcinema.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    fullxcinema.Cat(fullxcinema.site.url)

    assert len(dirs) == 2
    assert all(d["mode"] == "List" for d in dirs)
    assert {d["name"] for d in dirs} == {"Tag A", "Tag B"}


def test_search_routes_to_search_dir_or_list(monkeypatch):
    searches = []
    list_calls = []

    monkeypatch.setattr(
        fullxcinema.site,
        "search_dir",
        lambda url, mode: searches.append((url, mode)),
    )
    monkeypatch.setattr(fullxcinema, "List", lambda url: list_calls.append(url))

    fullxcinema.Search("https://fullxcinema.com/?s=")
    fullxcinema.Search("https://fullxcinema.com/?s=", keyword="test phrase")

    assert searches == [("https://fullxcinema.com/?s=", "Search")]
    assert list_calls == ["https://fullxcinema.com/?s=test%20phrase"]


def test_play_uses_resolver_for_hosted_media(monkeypatch):
    video_html = 'player">\n<iframe src="https://host/video-page"></iframe>'

    class _Hosted:
        @staticmethod
        def valid_url():
            return True

    class _Resolver:
        @staticmethod
        def HostedMediaFile(_link):
            return _Hosted()

    class _VP:
        def __init__(self):
            self.resolveurl = _Resolver()
            self.played_link = None
            self.played_html = None

        def play_from_link_to_resolve(self, link):
            self.played_link = link

        def play_from_html(self, html):
            self.played_html = html

    vp = _VP()
    monkeypatch.setattr(fullxcinema.utils, "VideoPlayer", lambda *_a, **_k: vp)
    monkeypatch.setattr(fullxcinema.utils, "getHtml", lambda url: video_html)

    fullxcinema.Play("https://fullxcinema.com/v/one/", "One")

    assert vp.played_link == "https://host/video-page"
    assert vp.played_html is None


def test_play_falls_back_to_iframe_html_when_not_hosted(monkeypatch):
    video_html = 'player">\n<iframe src="https://embed/page"></iframe>'
    embed_html = "<source src='https://cdn/vid.mp4'>"

    class _Resolver:
        @staticmethod
        def HostedMediaFile(_link):
            return None

    class _VP:
        def __init__(self):
            self.resolveurl = _Resolver()
            self.played_link = None
            self.played_html = None

        def play_from_link_to_resolve(self, link):
            self.played_link = link

        def play_from_html(self, html):
            self.played_html = html

    def _get_html(url):
        if "embed/page" in url:
            return embed_html
        return video_html

    vp = _VP()
    monkeypatch.setattr(fullxcinema.utils, "VideoPlayer", lambda *_a, **_k: vp)
    monkeypatch.setattr(fullxcinema.utils, "getHtml", _get_html)

    fullxcinema.Play("https://fullxcinema.com/v/two/", "Two")

    assert vp.played_link is None
    assert vp.played_html == embed_html


def test_gotopage_updates_container_when_in_range(monkeypatch):
    builtins = []

    class _Dialog:
        @staticmethod
        def numeric(_kind, _title):
            return "7"

    monkeypatch.setattr(fullxcinema.xbmcgui, "Dialog", lambda: _Dialog())
    monkeypatch.setattr(fullxcinema.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd))
    monkeypatch.setattr(fullxcinema.utils, "notify", lambda **_k: (_ for _ in ()).throw(AssertionError("unexpected notify")))

    fullxcinema.GotoPage(
        "fullxcinema.List",
        "https://fullxcinema.com/page/3/",
        np="3",
        lp="10",
    )

    assert builtins
    assert "page%2F7%2F" in builtins[0]
    assert "Container.Update(" in builtins[0]


def test_gotopage_notifies_when_out_of_range(monkeypatch):
    notices = []
    builtins = []

    class _Dialog:
        @staticmethod
        def numeric(_kind, _title):
            return "11"

    monkeypatch.setattr(fullxcinema.xbmcgui, "Dialog", lambda: _Dialog())
    monkeypatch.setattr(fullxcinema.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd))
    monkeypatch.setattr(fullxcinema.utils, "notify", lambda **k: notices.append(k))

    fullxcinema.GotoPage(
        "fullxcinema.List",
        "https://fullxcinema.com/page/3/",
        np="3",
        lp="10",
    )

    assert notices and notices[0]["msg"] == "Out of range!"
    assert builtins == []


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

    monkeypatch.setattr(fullxcinema.utils, "LookupInfo", _LookupInfo)

    fullxcinema.Lookupinfo("https://fullxcinema.com/v/one/")

    assert captured["base"] == "https://fullxcinema.com/"
    assert captured["mode"] == "fullxcinema.List"
    assert captured["called"] is True
    assert [entry[0] for entry in captured["lookup_list"]] == ["Actor", "Category", "Tag"]


def test_related_updates_container(monkeypatch):
    builtins = []
    monkeypatch.setattr(fullxcinema.xbmc, "executebuiltin", lambda cmd: builtins.append(cmd))

    fullxcinema.Related("https://fullxcinema.com/v/related/")

    assert builtins
    assert "Container.Update(" in builtins[0]
    assert "mode=fullxcinema.List" in builtins[0]

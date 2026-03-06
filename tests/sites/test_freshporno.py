"""Behavior tests for freshporno site module."""

from resources.lib.sites import freshporno


def test_main_adds_menu_entries_and_lists_home(monkeypatch):
    dirs = []
    list_calls = []

    monkeypatch.setattr(
        freshporno.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(freshporno, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(freshporno.utils, "eod", lambda: None)

    freshporno.Main()

    assert len(dirs) == 4
    assert any(d["mode"] == "Tags" for d in dirs)
    assert any(d["mode"] == "Channels" for d in dirs)
    assert any(d["mode"] == "Models" for d in dirs)
    assert any(d["mode"] == "Search" for d in dirs)
    assert list_calls == ["https://freshporno.org/"]


def test_list_calls_soup_videos_list_with_spec_and_context_builder(monkeypatch):
    captured = {}

    monkeypatch.setattr(freshporno.utils, "getHtml", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(
        freshporno.utils,
        "parse_html",
        lambda html: type("S", (), {"dummy": True})(),
    )
    monkeypatch.setattr(freshporno.utils, "eod", lambda: None)

    def _fake_soup_videos_list(site_obj, soup, spec, contextm=None):
        captured["site"] = site_obj
        captured["soup"] = soup
        captured["spec"] = spec
        captured["contextm"] = contextm

    monkeypatch.setattr(freshporno.utils, "soup_videos_list", _fake_soup_videos_list)

    freshporno.List("https://freshporno.org/")

    assert captured["site"] is freshporno.site
    assert captured["spec"]["items"] == ".thumbs-inner"
    assert captured["spec"]["pagination"]["selector"] == "a.next[href]"
    cm = captured["contextm"]("https://freshporno.org/v/1", "Title")
    assert "Lookup info" in cm[0][0]
    assert "mode=freshporno.Lookupinfo" in cm[0][1]


def test_search_routes_keyword_and_empty(monkeypatch):
    searches = []
    list_calls = []

    monkeypatch.setattr(
        freshporno.site, "search_dir", lambda url, mode: searches.append((url, mode))
    )
    monkeypatch.setattr(freshporno, "List", lambda url: list_calls.append(url))

    freshporno.Search("https://freshporno.org/search/")
    freshporno.Search("https://freshporno.org/search/", keyword="test phrase")

    assert searches == [("https://freshporno.org/search/", "Search")]
    assert list_calls == ["https://freshporno.org/search/test-phrase"]


def test_playvid_uses_kt_player_path(monkeypatch):
    class _VP:
        def __init__(self):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()
            self.kt = None

        def play_from_kt_player(self, html, url=None):
            self.kt = (html, url)

    vp = _VP()
    monkeypatch.setattr(
        freshporno.utils, "getHtml", lambda *a, **k: "kt_player('kt_player' ... )"
    )
    monkeypatch.setattr(freshporno.utils, "VideoPlayer", lambda *a, **k: vp)

    freshporno.Playvid("https://freshporno.org/video/1", "name")
    assert vp.kt == ("kt_player('kt_player' ... )", "https://freshporno.org/video/1")


def test_tags_parses_only_tag_items(monkeypatch):
    html = """
    <a href="/tags/tag-one/"><i class="fa-tag"></i> icon Tag One </a>
    <a href="/tags/tag-two/">Tag Two without icon</a>
    <a href="/tags/tag-three/"><i class="fa-tag"></i>Tag Three</a>
    """
    dirs = []

    monkeypatch.setattr(freshporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(freshporno.utils, "eod", lambda: None)
    monkeypatch.setattr(
        freshporno.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    freshporno.Tags("https://freshporno.org/tags/")

    assert len(dirs) == 2
    assert all(d["mode"] == "List" for d in dirs)
    assert any("tag-one" in d["url"] for d in dirs)
    assert any("Tag Three" in d["name"] for d in dirs)


def test_channels_parses_count_and_image(monkeypatch):
    html = """
    <div class="content-wrapper">
      <div><a href="https://freshporno.org/channels/ch-1/" title="Channel One">123 videos</a>
        <img data-original="https://img/ch1.jpg"/>
      </div>
      <div class="no image"><a href="https://freshporno.org/channels/ch-2/" title="Channel Two">25 videos</a></div>
    </div>
    """
    dirs = []

    monkeypatch.setattr(freshporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(freshporno.utils, "eod", lambda: None)
    monkeypatch.setattr(
        freshporno.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "icon": icon}
        ),
    )

    freshporno.Channels("https://freshporno.org/channels/")

    assert len(dirs) == 2
    assert dirs[0]["mode"] == "List"
    assert " - 123" in dirs[0]["name"]
    assert dirs[0]["icon"] == "https://img/ch1.jpg"
    assert dirs[1]["icon"] == ""


def test_models_parses_and_adds_next_page(monkeypatch):
    html = """
    <div class="content-wrapper">
      <div><a href="https://freshporno.org/models/m-1/" title="Model One">88 videos</a>
        <img data-original="https://img/m1.jpg"/>
      </div>
    </div>
    <a class="next" href="/models/page/3/"></a>
    """
    dirs = []

    monkeypatch.setattr(freshporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(freshporno.utils, "eod", lambda: None)
    monkeypatch.setattr(
        freshporno.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "icon": icon}
        ),
    )

    freshporno.Models("https://freshporno.org/models/")

    assert any(d["mode"] == "List" and "Model One - 88" in d["name"] for d in dirs)
    assert any(
        d["mode"] == "Models"
        and "Next Page (3)" == d["name"]
        and d["url"].endswith("/models/page/3/")
        for d in dirs
    )


def test_lookupinfo_selects_and_updates_container(monkeypatch):
    html = """
    <a href="/channels/ch-one/" title="Channel One">Channel One</a>
    <a href="/tags/tag-one/"><i class="fa-tag"></i>Tag One</a>
    <a href="/models/model-one/" title="Model One">Model One</a>
    """
    commands = []

    monkeypatch.setattr(freshporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(
        freshporno.utils,
        "selector",
        lambda title, choices, show_on_one=True: choices["Tag - Tag One"],
    )
    monkeypatch.setattr(
        freshporno.utils.xbmc, "executebuiltin", lambda cmd: commands.append(cmd)
    )

    freshporno.Lookupinfo("https://freshporno.org/video/1")

    assert commands and commands[0].startswith("Container.Update(")
    assert "mode=freshporno.List" in commands[0]
    assert "tags%2Ftag-one%2F" in commands[0]


def test_lookupinfo_notifies_when_no_info(monkeypatch):
    notices = []

    monkeypatch.setattr(freshporno.utils, "getHtml", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(
        freshporno.utils, "notify", lambda *a, **k: notices.append((a, k))
    )

    freshporno.Lookupinfo("https://freshporno.org/video/2")
    assert notices and notices[0][0][1] == "No info found"

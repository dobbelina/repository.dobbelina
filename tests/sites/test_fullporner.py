"""Behavior tests for fullporner site module."""

from resources.lib.sites import fullporner


def test_site_initialization_values():
    assert fullporner.site.name == "fullporner"
    assert fullporner.site.url == "https://fullporner.org/"
    assert "fullporner.png" in fullporner.site.image


def test_main_builds_menu_and_lists_latest(monkeypatch):
    dirs = []
    list_calls = []
    eod_calls = []

    monkeypatch.setattr(
        fullporner.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(fullporner, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(fullporner.utils, "eod", lambda: eod_calls.append(True))

    fullporner.Main()

    assert len(dirs) == 4
    assert any(d["mode"] == "Categories" for d in dirs)
    assert any(d["mode"] == "Actors" and "Pornstars" in d["name"] for d in dirs)
    assert any(d["mode"] == "Actors" and "Channels" in d["name"] for d in dirs)
    assert any(d["mode"] == "Search" for d in dirs)
    assert list_calls == ["https://fullporner.org/porn-channels/latest-videos/page/1/"]
    assert eod_calls == [True]


def test_list_parses_articles_and_adds_next_page(monkeypatch):
    html = """
    <article>
      <a href="https://fullporner.org/v/one/" title="One"></a>
      <img poster="https://img/one.jpg"/>
      <i>10:00</i>
    </article>
    <article>
      <a href="https://fullporner.org/v/two/" title="Two"></a>
      <img src="https://img/two.jpg"/>
      <i>08:00</i>
    </article>
    <div class="pagination"><span class="current">1</span><a href="https://fullporner.org/page/2/">2</a></div>
    """
    downloads = []
    dirs = []

    monkeypatch.setattr(fullporner.utils, "getHtml", lambda *_a, **_k: html)
    monkeypatch.setattr(fullporner.utils, "eod", lambda: None)
    monkeypatch.setattr(
        fullporner.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", duration="", **kwargs: downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": icon,
                "duration": duration,
            }
        ),
    )
    monkeypatch.setattr(
        fullporner.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    fullporner.List("https://fullporner.org/porn-channels/latest-videos/page/1/")

    assert len(downloads) == 2
    assert downloads[0]["mode"] == "Playvid"
    assert downloads[0]["icon"] == "https://img/one.jpg"
    assert downloads[1]["icon"] == "https://img/two.jpg"
    assert downloads[0]["duration"] == "10:00"

    next_dirs = [d for d in dirs if d["mode"] == "List"]
    assert len(next_dirs) == 1
    assert next_dirs[0]["name"] == "Next Page (2)"
    assert next_dirs[0]["url"] == "https://fullporner.org/page/2/"


def test_list_returns_early_when_no_articles(monkeypatch):
    monkeypatch.setattr(fullporner.utils, "getHtml", lambda *_a, **_k: "<html></html>")
    monkeypatch.setattr(
        fullporner.site,
        "add_download_link",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("unexpected add")),
    )
    monkeypatch.setattr(
        fullporner.utils,
        "eod",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected eod")),
    )

    fullporner.List("https://fullporner.org/none")


def test_categories_parses_and_sorts_with_filter(monkeypatch):
    html = """
    <article>
      <a href="https://fullporner.org/cat/z/"></a>
      <img src="https://img/z.jpg"/>
      <div class="cat-title"> Zeta </div>
    </article>
    <article>
      <a href="https://fullporner.org/cat/a/"></a>
      <img src="https://img/a.jpg"/>
      <div class="cat-title"> Alpha </div>
    </article>
    """
    dirs = []

    monkeypatch.setattr(fullporner.utils, "getHtml", lambda *_a, **_k: html)
    monkeypatch.setattr(fullporner.utils, "eod", lambda: None)
    monkeypatch.setattr(
        fullporner.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "icon": icon}
        ),
    )

    fullporner.Categories(fullporner.site.url)

    assert [d["name"] for d in dirs] == ["Alpha", "Zeta"]
    assert all(d["mode"] == "List" for d in dirs)
    assert dirs[0]["url"].endswith("&filter=latest")


def test_actors_parses_sorted_and_adds_next_page(monkeypatch):
    html = """
    <article>
      <a href="https://fullporner.org/actor/z/" title="Zed"></a>
      <img src="https://img/z.jpg"/>
    </article>
    <article>
      <a href="https://fullporner.org/actor/a/" title="Adam"></a>
      <img src="https://img/a.jpg"/>
    </article>
    <div class="pagination"><span class="current">3</span><a href="https://fullporner.org/porno-actors/page/4/">4</a></div>
    """
    dirs = []

    monkeypatch.setattr(fullporner.utils, "getHtml", lambda *_a, **_k: html)
    monkeypatch.setattr(fullporner.utils, "eod", lambda: None)
    monkeypatch.setattr(
        fullporner.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "icon": icon}
        ),
    )

    fullporner.Actors("https://fullporner.org/porno-actors/page/3/")

    actor_dirs = [d for d in dirs if d["mode"] == "List"]
    assert [d["name"] for d in actor_dirs] == ["Adam", "Zed"]
    next_dirs = [d for d in dirs if d["mode"] == "Actors"]
    assert len(next_dirs) == 1
    assert next_dirs[0]["name"] == "Next Page (4)"


def test_search_routes_empty_and_keyword(monkeypatch):
    searches = []
    list_calls = []

    monkeypatch.setattr(fullporner.site, "search_dir", lambda url, mode: searches.append((url, mode)))
    monkeypatch.setattr(fullporner, "List", lambda url: list_calls.append(url))

    fullporner.Search("https://fullporner.org/?s=")
    fullporner.Search("https://fullporner.org/?s=", keyword="red shoes")

    assert searches == [("https://fullporner.org/?s=", "Search")]
    assert list_calls == ["https://fullporner.org/?s=red+shoes"]


def test_playvid_uses_site_link_playback(monkeypatch):
    captured = {}

    class _VP:
        def play_from_site_link(self, source_url, page_url):
            captured["source_url"] = source_url
            captured["page_url"] = page_url

    monkeypatch.setattr(fullporner.utils, "VideoPlayer", lambda *_a, **_k: _VP())

    fullporner.Playvid("https://fullporner.org/v/one/", "One")

    assert captured == {
        "source_url": "https://fullporner.org/v/one/",
        "page_url": "https://fullporner.org/v/one/",
    }

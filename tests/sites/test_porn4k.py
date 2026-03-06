"""Behavior tests for porn4k site module."""

from resources.lib.sites import porn4k


def test_main_builds_menu_and_lists_first_page(monkeypatch):
    dirs = []
    list_calls = []

    monkeypatch.setattr(
        porn4k.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(porn4k, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(porn4k.utils, "eod", lambda: None)

    porn4k.Main()

    assert len(dirs) == 3
    assert any(d["mode"] == "Everything" for d in dirs)
    assert any(d["mode"] == "Categories" for d in dirs)
    assert any(d["mode"] == "Search" for d in dirs)
    assert list_calls == ["https://porn4k.to/page/1/"]


def test_list_parses_articles_and_adds_next_page(monkeypatch):
    html = """
    <article>
      <a href="https://porn4k.to/v/1/" title="One"></a>
      <img src="https://img/1.jpg"/>
    </article>
    <article>
      <a href="https://porn4k.to/v/2/" title="Two"></a>
      <img src="https://img/2.jpg"/>
    </article>
    <a rel="next" href="https://porn4k.to/page/3/"></a>
    """
    downloads = []
    dirs = []

    monkeypatch.setattr(porn4k.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(porn4k.utils, "eod", lambda: None)
    monkeypatch.setattr(
        porn4k.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", contextm=None, **kwargs: downloads.append(
            {"name": name, "url": url, "mode": mode, "icon": icon, "contextm": contextm}
        ),
    )
    monkeypatch.setattr(
        porn4k.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    porn4k.List("https://porn4k.to/page/1/")

    assert len(downloads) == 2
    assert downloads[0]["url"] == "https://porn4k.to/v/1/"
    assert downloads[0]["contextm"] and "Lookup info" in downloads[0]["contextm"][0][0]
    assert any(d["mode"] == "List" and "Next Page (3)" == d["name"] for d in dirs)


def test_search_routes_empty_and_keyword(monkeypatch):
    searches = []
    list_calls = []

    monkeypatch.setattr(porn4k.site, "search_dir", lambda url, mode: searches.append((url, mode)))
    monkeypatch.setattr(porn4k, "List", lambda url: list_calls.append(url))

    porn4k.Search("https://porn4k.to/?s=")
    porn4k.Search("https://porn4k.to/?s=", keyword="hello world")

    assert searches == [("https://porn4k.to/?s=", "Search")]
    assert list_calls == ["https://porn4k.to/?s=hello+world"]


def test_categories_parses_cat_items(monkeypatch):
    html = """
    <li class="cat-item"><a href="https://porn4k.to/cat/a/"> A Cat </a></li>
    <li class="cat-item"><a href="https://porn4k.to/cat/b/">B Cat</a></li>
    """
    dirs = []

    monkeypatch.setattr(porn4k.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(porn4k.utils, "eod", lambda: None)
    monkeypatch.setattr(
        porn4k.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    porn4k.Categories("https://porn4k.to/")
    assert len(dirs) == 2
    assert all(d["mode"] == "List" for d in dirs)


def test_everything_parses_links(monkeypatch):
    html = """
    <li><a href="https://porn4k.to/v/10/"> Movie One </a></li>
    <li><a href="https://porn4k.to/v/11/">Movie Two</a></li>
    """
    downloads = []

    monkeypatch.setattr(porn4k.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(porn4k.utils, "eod", lambda: None)
    monkeypatch.setattr(
        porn4k.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", **kwargs: downloads.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    porn4k.Everything("https://porn4k.to/filme-von-a-z/")
    assert len(downloads) == 2
    assert all(d["mode"] == "Playvid" for d in downloads)


def test_playvid_selects_and_plays_resolved_link(monkeypatch):
    html = """
    <a href="https://host/one" target="_blank" rel="nofollow">one</a>
    <a href="https://host/two" target="_blank" rel="nofollow">two</a>
    """

    class _Resolved:
        def __init__(self, ok):
            self._ok = ok

        def valid_url(self):
            return self._ok

    class _Resolver:
        @staticmethod
        def HostedMediaFile(link):
            return _Resolved(link.endswith("/one"))

    class _Progress:
        def update(self, *_a, **_k):
            return None

        def close(self):
            return None

    class _VP:
        def __init__(self):
            self.progress = _Progress()
            self.resolveurl = _Resolver()
            self.played = None

        @staticmethod
        def bypass_hosters_single(link):
            return link.endswith("/two")

        def play_from_link_to_resolve(self, link):
            self.played = link

    vp = _VP()
    monkeypatch.setattr(porn4k.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(porn4k.utils, "VideoPlayer", lambda *a, **k: vp)
    monkeypatch.setattr(porn4k.utils, "selector", lambda *_a, **_k: "https://host/one")

    porn4k.Playvid("https://porn4k.to/v/1/", "name")
    assert vp.played == "https://host/one"


def test_playvid_notifies_when_no_playable_links(monkeypatch):
    html = '<a href="https://host/one" target="_blank" rel="nofollow">one</a>'
    notices = []

    class _Resolved:
        @staticmethod
        def valid_url():
            return False

    class _Resolver:
        @staticmethod
        def HostedMediaFile(_link):
            return _Resolved()

    class _Progress:
        def update(self, *_a, **_k):
            return None

        def close(self):
            return None

    class _VP:
        def __init__(self):
            self.progress = _Progress()
            self.resolveurl = _Resolver()

        @staticmethod
        def bypass_hosters_single(_link):
            return False

        def play_from_link_to_resolve(self, _link):
            raise AssertionError("should not play")

    monkeypatch.setattr(porn4k.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(porn4k.utils, "VideoPlayer", lambda *a, **k: _VP())
    monkeypatch.setattr(porn4k.utils, "notify", lambda *a, **k: notices.append((a, k)))

    porn4k.Playvid("https://porn4k.to/v/2/", "name")
    assert notices and notices[0][0][1] == "No playable links found"


def test_lookupinfo_uses_expected_lookup_list(monkeypatch):
    captured = {}

    class _LookupInfo:
        def __init__(self, base, url, mode, lookup_list):
            captured["base"] = base
            captured["url"] = url
            captured["mode"] = mode
            captured["lookup_list"] = lookup_list

        def getinfo(self):
            captured["called"] = True

    monkeypatch.setattr(porn4k.utils, "LookupInfo", _LookupInfo)
    porn4k.Lookupinfo("https://porn4k.to/v/3/")

    assert captured["base"] == "https://porn4k.to/"
    assert captured["mode"] == "porn4k.List"
    assert captured["called"] is True
    assert [x[0] for x in captured["lookup_list"]] == ["Cat", "Tag"]

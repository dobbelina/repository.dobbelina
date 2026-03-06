"""Behavior tests for hdporn92 site module."""

from resources.lib.sites import hdporn92


def test_main_adds_expected_menu_and_lists_latest(monkeypatch):
    dirs = []
    list_calls = []

    monkeypatch.setattr(
        hdporn92.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )
    monkeypatch.setattr(hdporn92, "List", lambda url: list_calls.append(url))
    monkeypatch.setattr(hdporn92.utils, "eod", lambda: None)

    hdporn92.Main()

    assert len(dirs) == 4
    assert any("Categories" in d["name"] and d["mode"] == "Categories" for d in dirs)
    assert any("Actors" in d["name"] and d["mode"] == "Categories" for d in dirs)
    assert any("Tags" in d["name"] and d["mode"] == "Tags" for d in dirs)
    assert any("Search" in d["name"] and d["mode"] == "Search" for d in dirs)
    assert list_calls == ["https://hdporn92.com/?filter=latest"]


def test_list_parses_videos_and_next_page(monkeypatch):
    html = """
    <article>
      <a href="https://hdporn92.com/video-1" title=" First Video "></a>
      <img poster="https://cdn/1.jpg"/>
    </article>
    <article>
      <a href="https://hdporn92.com/video-2" title="Second Video"></a>
      <img src="https://cdn/2.jpg"/>
    </article>
    <div class="pagination">
      <span class="current">1</span>
      <a href="https://hdporn92.com/page/2/">2</a>
    </div>
    """
    downloads = []
    dirs = []

    monkeypatch.setattr(hdporn92.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(hdporn92.utils, "eod", lambda: None)
    monkeypatch.setattr(
        hdporn92.site,
        "add_download_link",
        lambda name, url, mode, icon, desc="", contextm=None, **kwargs: downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": icon,
                "contextm": contextm,
            }
        ),
    )
    monkeypatch.setattr(
        hdporn92.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    hdporn92.List("https://hdporn92.com/?filter=latest")

    assert len(downloads) == 2
    assert downloads[0]["url"] == "https://hdporn92.com/video-1"
    assert downloads[0]["icon"] == "https://cdn/1.jpg"
    assert downloads[1]["icon"] == "https://cdn/2.jpg"
    assert downloads[0]["contextm"] and "Lookup info" in downloads[0]["contextm"][0][0]
    assert any(d["mode"] == "List" and "Next Page" in d["name"] for d in dirs)


def test_list_handles_nothing_found(monkeypatch):
    notices = []

    monkeypatch.setattr(hdporn92.utils, "getHtml", lambda *a, **k: "<h1>Nothing found</h1>")
    monkeypatch.setattr(hdporn92.utils, "notify", lambda *a, **k: notices.append((a, k)))
    monkeypatch.setattr(hdporn92.utils, "eod", lambda: None)

    hdporn92.List("https://hdporn92.com/?s=none")

    assert notices, "Expected a user notification for empty results"


def test_categories_parses_and_sorts_and_paginates(monkeypatch):
    html = """
    <article><a href="https://hdporn92.com/category/z-cat" title="Z Cat"></a><img src="z.jpg"/></article>
    <article><a href="https://hdporn92.com/category/a-cat" title="A Cat"></a><img poster="a.jpg"/></article>
    <div class="pagination">
      <span class="current">1</span>
      <a href="https://hdporn92.com/categories/page/2/">2</a>
    </div>
    """
    dirs = []

    monkeypatch.setattr(hdporn92.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(hdporn92.utils, "eod", lambda: None)
    monkeypatch.setattr(
        hdporn92.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode, "icon": icon}
        ),
    )

    hdporn92.Categories("https://hdporn92.com/categories/")

    cat_names = [d["name"] for d in dirs if d["mode"] == "List"]
    assert cat_names[:2] == sorted(cat_names[:2], key=lambda x: x.lower())
    assert all("?filter=latest" in d["url"] for d in dirs if d["mode"] == "List")
    assert any(d["mode"] == "Categories" and "Next Page" in d["name"] for d in dirs)


def test_tags_extracts_tag_links(monkeypatch):
    html = """
    <a href="https://hdporn92.com/tag/amateur" aria-label=" Amateur "></a>
    <a href="https://hdporn92.com/tag/milf" aria-label="Milf"></a>
    <a href="https://hdporn92.com/other/path" aria-label="Ignore"></a>
    """
    dirs = []

    monkeypatch.setattr(hdporn92.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(hdporn92.utils, "eod", lambda: None)
    monkeypatch.setattr(
        hdporn92.site,
        "add_dir",
        lambda name, url, mode, icon=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    hdporn92.Tags("https://hdporn92.com/tags/")

    assert len(dirs) == 2
    assert all(d["mode"] == "List" for d in dirs)
    assert all("?filter=latest" in d["url"] for d in dirs)
    assert any("amateur" in d["url"] for d in dirs)


def test_search_routes_keyword_and_empty(monkeypatch):
    searches = []
    lists = []

    monkeypatch.setattr(
        hdporn92.site, "search_dir", lambda url, mode: searches.append((url, mode))
    )
    monkeypatch.setattr(hdporn92, "List", lambda url: lists.append(url))

    hdporn92.Search("https://hdporn92.com/?s=")
    hdporn92.Search("https://hdporn92.com/?s=", keyword="test phrase")

    assert searches == [("https://hdporn92.com/?s=", "Search")]
    assert lists == ["https://hdporn92.com/?s=test+phrase"]


def test_playvid_resolver_branch_uses_head_redirect(monkeypatch):
    playhtml = '<iframe src="https://host/embed/abc" allowfullscreen></iframe>'

    class _DummyVP:
        def __init__(self, *a, **k):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()
            self.resolveurl = type(
                "R", (), {"HostedMediaFile": lambda *a, **k: True}
            )()
            self.resolved = None
            self.direct = None

        def play_from_link_to_resolve(self, link):
            self.resolved = link

        def play_from_direct_link(self, link):
            self.direct = link

    vp = _DummyVP()

    monkeypatch.setattr(hdporn92.utils, "getHtml", lambda *a, **k: playhtml)
    monkeypatch.setattr(hdporn92.utils, "VideoPlayer", lambda *a, **k: vp)
    monkeypatch.setattr(
        hdporn92.requests,
        "head",
        lambda *a, **k: type("R", (), {"url": "https://redir/final"})(),
    )

    hdporn92.Playvid("https://hdporn92.com/video-1", "name")

    assert vp.resolved == "https://redir/final"
    assert vp.direct is None


def test_playvid_embed_branch_extracts_hls(monkeypatch):
    playhtml = '<iframe src="https://embed/page" allowfullscreen></iframe>'
    embedhtml = "<html>embed</html>"

    class _DummyVP:
        def __init__(self, *a, **k):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()
            self.resolveurl = type(
                "R", (), {"HostedMediaFile": lambda *a, **k: False}
            )()
            self.resolved = None
            self.direct = None

        def play_from_link_to_resolve(self, link):
            self.resolved = link

        def play_from_direct_link(self, link):
            self.direct = link

    vp = _DummyVP()
    gethtml_calls = []

    def _gethtml(url, *args, **kwargs):
        gethtml_calls.append(url)
        if url == "https://hdporn92.com/video-2":
            return playhtml
        return embedhtml

    monkeypatch.setattr(hdporn92.utils, "getHtml", _gethtml)
    monkeypatch.setattr(hdporn92.utils, "VideoPlayer", lambda *a, **k: vp)
    monkeypatch.setattr(
        hdporn92.utils,
        "get_packed_data",
        lambda _html: 'var links={"hls2":"https://cdn/video.m3u8"}',
    )

    hdporn92.Playvid("https://hdporn92.com/video-2", "name")

    assert "https://embed/page" in gethtml_calls
    assert vp.direct == "https://cdn/video.m3u8"
    assert vp.resolved is None


def test_playvid_not_found_notifies(monkeypatch):
    notices = []

    class _DummyVP:
        def __init__(self, *a, **k):
            self.progress = type("P", (), {"update": lambda *a, **k: None})()
            self.resolveurl = type(
                "R", (), {"HostedMediaFile": lambda *a, **k: False}
            )()

    monkeypatch.setattr(hdporn92.utils, "getHtml", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(hdporn92.utils, "VideoPlayer", lambda *a, **k: _DummyVP())
    monkeypatch.setattr(hdporn92.utils, "notify", lambda *a, **k: notices.append((a, k)))

    hdporn92.Playvid("https://hdporn92.com/video-3", "name")

    assert notices and notices[0][0][1] == "No Videos found"


def test_lookupinfo_uses_expected_patterns(monkeypatch):
    captured = {}

    class _FakeLookupInfo:
        def __init__(self, base, url, mode, lookup_list):
            captured["base"] = base
            captured["url"] = url
            captured["mode"] = mode
            captured["lookup_list"] = lookup_list

        def getinfo(self):
            captured["called"] = True

    monkeypatch.setattr(hdporn92.utils, "LookupInfo", _FakeLookupInfo)

    hdporn92.Lookupinfo("https://hdporn92.com/video-4")

    assert captured["base"] == "https://hdporn92.com/"
    assert captured["mode"] == "hdporn92.List"
    assert captured["called"] is True
    labels = [x[0] for x in captured["lookup_list"]]
    assert labels == ["Cat", "Model"]

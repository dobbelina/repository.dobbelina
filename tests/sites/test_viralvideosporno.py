from pathlib import Path

from resources.lib.sites import viralvideosporno


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "viralvideosporno"


def load_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_uses_soup_and_pagination(monkeypatch):
    html = load_fixture("list.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(viralvideosporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(viralvideosporno.utils, "eod", lambda: None)
    monkeypatch.setattr(
        viralvideosporno.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc="", **kwargs: downloads.append(
            {"name": name, "url": url, "mode": mode, "icon": iconimage, "desc": desc}
        ),
    )
    monkeypatch.setattr(
        viralvideosporno.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    viralvideosporno.List("https://www.viralvideosporno.com/")

    assert len(downloads) == 3
    assert downloads[0]["url"] == "https://video1.viralvideosporno.com/watch/123"
    assert downloads[1]["name"] == "Video Two"
    assert downloads[2]["desc"] == "Third desc"

    next_entries = [d for d in dirs if d["mode"] == "List"]
    assert len(next_entries) == 1
    assert next_entries[0]["url"] == "https://www.viralvideosporno.com/page/3/"
    assert "Next Page" in next_entries[0]["name"]


def test_categories_skip_first_and_parse(monkeypatch):
    html = load_fixture("categories.html")
    dirs = []

    monkeypatch.setattr(viralvideosporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(viralvideosporno.utils, "eod", lambda: None)
    monkeypatch.setattr(
        viralvideosporno.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    viralvideosporno.Categories("https://www.viralvideosporno.com/")

    assert len(dirs) == 3
    assert dirs[0]["name"] == "Amateur"
    assert dirs[0]["url"] == "https://www.viralvideosporno.com/canal/amateur"
    assert dirs[1]["url"] == "https://www.viralvideosporno.com/canal/college"
    assert dirs[2]["name"] == "MILF"


def test_mlist_parses_movies_and_next(monkeypatch):
    html = load_fixture("mlist.html")
    downloads = []
    dirs = []

    monkeypatch.setattr(viralvideosporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(viralvideosporno.utils, "eod", lambda: None)
    monkeypatch.setattr(
        viralvideosporno.site,
        "add_download_link",
        lambda name, url, mode, iconimage, desc="", **kwargs: downloads.append(
            {"name": name, "url": url, "mode": mode, "icon": iconimage}
        ),
    )
    monkeypatch.setattr(
        viralvideosporno.site,
        "add_dir",
        lambda name, url, mode, iconimage=None, **kwargs: dirs.append(
            {"name": name, "url": url, "mode": mode}
        ),
    )

    viralvideosporno.MList("https://www.viralvideosporno.com/peliculas/amateur")

    assert len(downloads) == 2
    assert downloads[0]["name"] == "Movie One"
    assert downloads[0]["url"] == "https://www.viralvideosporno.com/peliculas/video-1"
    assert downloads[1]["icon"].endswith("pel2.jpg")

    assert len(dirs) == 1
    assert (
        dirs[0]["url"] == "https://www.viralvideosporno.com/peliculas/peliculas_3.html"
    )


def test_playvid_passes_context_to_html_fallback(monkeypatch):
    html = "<html><div>player wrapper without direct source</div></html>"
    captured = {}

    class _HostedMediaFile:
        def __init__(self, url):
            self.url = url

        def valid_url(self):
            return False

    class FakeVideoPlayer:
        def __init__(self, name, download=None, **kwargs):
            self.progress = type(
                "p",
                (),
                {
                    "update": lambda *args, **kwargs: None,
                    "close": lambda *args, **kwargs: None,
                },
            )()
            self.resolveurl = type("R", (), {"HostedMediaFile": _HostedMediaFile})()

        def play_from_html(self, page_html, page_url=None):
            captured["html"] = page_html
            captured["url"] = page_url

        def play_from_direct_link(self, url):
            captured["direct"] = url

        def play_from_link_to_resolve(self, source):
            captured["resolved"] = source

    monkeypatch.setattr(viralvideosporno.utils, "getHtml", lambda *a, **k: html)
    monkeypatch.setattr(viralvideosporno.utils, "VideoPlayer", FakeVideoPlayer)

    viralvideosporno.Playvid(
        "https://www.viralvideosporno.com/watch/fallback", "Fallback"
    )

    assert captured["html"] == html
    assert captured["url"] == "https://www.viralvideosporno.com/watch/fallback"

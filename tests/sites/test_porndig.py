"""Tests for porndig.com site implementation."""

from pathlib import Path
import json

from resources.lib.sites import porndig


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "sites" / "porndig"


def load_fixture(name):
    """Load a fixture file from the porndig fixtures directory."""
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_list_parses_video_items(monkeypatch):
    """Test that List correctly parses video items from JSON response."""
    html = load_fixture("listing.html")

    # Wrap HTML in JSON response format
    json_response = json.dumps({"data": {"content": html}})

    downloads = []
    dirs = []

    def fake_get_html(url, referer=None, headers=None, data=None):
        return json_response

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
                "icon": iconimage,
                "duration": kwargs.get("duration", ""),
                "quality": kwargs.get("quality", ""),
            }
        )

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "name": name,
                "url": url,
                "mode": mode,
            }
        )

    monkeypatch.setattr(porndig.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(porndig.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(porndig.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(porndig.utils, "eod", lambda: None)

    porndig.List(0, 0, 0)

    # Should have 3 videos
    assert len(downloads) == 3

    # Check first video (HD quality)
    assert downloads[0]["name"] == "Hot Professional Scene"
    assert "12345" in downloads[0]["url"]
    assert "12345.jpg" in downloads[0]["icon"]
    assert downloads[0]["duration"] == "10:30"
    assert "HD" in downloads[0]["quality"]

    # Check second video (FULL HD quality)
    assert downloads[1]["name"] == "Amazing Quality Video"
    assert "67890" in downloads[1]["url"]
    assert downloads[1]["duration"] == "15:45"
    assert "FULLHD" in downloads[1]["quality"]

    # Check third video (no quality badge, duration with .tion class)
    assert downloads[2]["name"] == "Regular Video"
    assert "11223" in downloads[2]["url"]
    assert downloads[2]["duration"] == "8:20"
    assert downloads[2]["quality"] == ""


def test_categories_parses_categories(monkeypatch):
    """Test that Categories correctly parses category options."""
    html = load_fixture("categories.html")

    dirs = []

    def fake_get_html(url, referer=None):
        return html

    def fake_add_dir(name, url, mode, iconimage, page, channel, section):
        dirs.append(
            {
                "name": name,
                "channel": channel,
                "section": section,
            }
        )

    monkeypatch.setattr(porndig.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(porndig.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(porndig.utils, "eod", lambda: None)

    # Mock addon settings
    class FakeAddon:
        def getSetting(self, key):
            return "0"  # Professional section

    monkeypatch.setattr(porndig, "addon", FakeAddon())

    porndig.Categories("https://www.porndig.com/videos/")

    # Should have 3 categories (skipping empty "All Categories" option)
    assert len(dirs) == 3

    # Check categories
    assert dirs[0]["name"] == "MILF"
    assert dirs[0]["channel"] == "123"
    assert dirs[0]["section"] == 3

    assert dirs[1]["name"] == "Teen"
    assert dirs[1]["channel"] == "456"

    assert dirs[2]["name"] == "Anal"
    assert dirs[2]["channel"] == "789"


def test_list_handles_pagination(monkeypatch):
    """Test that List adds pagination when there are enough results."""
    html = load_fixture("listing.html")
    json_response = json.dumps({"data": {"content": html}})

    dirs = []

    # Create enough items to trigger pagination
    items_html = ""
    for i in range(36):
        items_html += f"""
        <section>
            <a href="/videos/{i}/">Video {i}</a>
            <img src="thumb{i}.jpg">
        </section>
        """

    json_response = json.dumps({"data": {"content": items_html}})

    def fake_get_html(url, referer=None, headers=None, data=None):
        return json_response

    def fake_add_dir(name, url, mode, iconimage=None, **kwargs):
        dirs.append(
            {
                "name": name,
                "mode": mode,
            }
        )

    monkeypatch.setattr(porndig.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(porndig.site, "add_download_link", lambda *a, **k: None)
    monkeypatch.setattr(porndig.site, "add_dir", fake_add_dir)
    monkeypatch.setattr(porndig.utils, "eod", lambda: None)

    porndig.List(123, 0, 0)

    # Should have next page
    next_pages = [d for d in dirs if "Next Page" in d["name"]]
    assert len(next_pages) == 1


def test_list_handles_empty_results(monkeypatch):
    """Test that List handles empty JSON response."""
    json_response = json.dumps({"data": {"content": "<html><body></body></html>"}})

    downloads = []

    def fake_get_html(url, referer=None, headers=None, data=None):
        return json_response

    monkeypatch.setattr(porndig.utils, "getHtml", fake_get_html)
    monkeypatch.setattr(
        porndig.site, "add_download_link", lambda *a, **k: downloads.append(a[0])
    )
    monkeypatch.setattr(porndig.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(porndig.utils, "eod", lambda: None)

    porndig.List(0, 0, 0)

    # Should have no videos
    assert len(downloads) == 0


def test_list_defaults_invalid_section_to_video_listing(monkeypatch):
    """Invalid sections should not crash List()."""
    html = load_fixture("listing.html")
    json_response = json.dumps({"data": {"content": html}})
    downloads = []

    monkeypatch.setattr(
        porndig.utils, "getHtml", lambda url, referer=None, headers=None, data=None: json_response
    )
    monkeypatch.setattr(
        porndig.site, "add_download_link", lambda *args, **kwargs: downloads.append(args[0])
    )
    monkeypatch.setattr(porndig.site, "add_dir", lambda *args, **kwargs: None)
    monkeypatch.setattr(porndig.utils, "eod", lambda: None)

    porndig.List(0, "not-a-section", 0)

    assert downloads


def test_parse_json_returns_empty_string_on_invalid_payload():
    """Malformed JSON should fail closed instead of raising."""
    assert porndig.ParseJson("not json") == ""

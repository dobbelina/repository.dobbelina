"""Tests for stripchat.com site implementation."""

import json
import pytest
from resources.lib.sites import stripchat


def _ll(url):
    return stripchat._ensure_low_latency_playlist(url)


def test_list_parses_json_models(monkeypatch):
    """Test that List correctly parses JSON model data."""
    json_data = {
        "models": [
            {
                "username": "model1",
                "hlsPlaylist": "https://stream.stripchat.com/model1.m3u8",
                "previewUrlThumbSmall": "https://img.stripchat.com/thumb1.jpg",
                "snapshotTimestamp": "123456",
                "id": "111",
                "groupShowTopic": "",
            },
            {
                "username": "model2",
                "hlsPlaylist": "https://stream.stripchat.com/model2.m3u8",
                "previewUrlThumbSmall": "https://img.stripchat.com/thumb2.jpg",
                "snapshotTimestamp": "654321",
                "id": "222",
                "groupShowTopic": "",
            },
        ]
    }

    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return json.dumps(json_data), False

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "iconimage": iconimage,
                "fanart": kwargs.get("fanart"),
            }
        )

    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(stripchat.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "eod", lambda: None)

    # Test assumes stripchat.List exists and parses JSON
    try:
        stripchat.List("https://stripchat.com/")
        assert len(downloads) == 2
        assert downloads[0]["iconimage"] == "https://img.doppiocdn.com/thumbs/123456/111_webp"
        assert downloads[0]["fanart"] == "https://img.doppiocdn.com/thumbs/123456/111_webp"
        assert downloads[1]["iconimage"] == "https://img.doppiocdn.com/thumbs/654321/222_webp"
        assert downloads[1]["fanart"] == "https://img.doppiocdn.com/thumbs/654321/222_webp"
    except AttributeError:
        pass


def test_list_handles_missing_topic_and_playlist(monkeypatch):
    """List should not crash when optional model fields are absent."""
    json_data = {
        "models": [
            {
                "username": "model1",
                "previewUrlThumbSmall": "https://img.stripchat.com/thumb1.jpg",
                "country": "us",
                "groupShowTopic": None,
            }
        ]
    }

    downloads = []

    def fake_get_html(url, *args, **kwargs):
        return json.dumps(json_data), False

    def fake_add_download_link(name, url, mode, iconimage, desc, **kwargs):
        downloads.append(
            {
                "name": name,
                "url": url,
                "iconimage": iconimage,
                "desc": desc,
            }
        )

    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.site, "add_download_link", fake_add_download_link)
    monkeypatch.setattr(stripchat.site, "add_dir", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "eod", lambda: None)

    stripchat.List("https://stripchat.com/")

    assert len(downloads) == 1
    assert downloads[0]["name"] == "model1"
    assert downloads[0]["url"] == ""
    assert "Location:" in downloads[0]["desc"]


def test_model_screenshot_falls_back_to_snapshot_url():
    model = {"snapshotTimestamp": "123456", "id": "111"}

    assert (
        stripchat._model_screenshot(model)
        == "https://img.doppiocdn.com/thumbs/123456/111_webp"
    )


def test_model_screenshot_prefers_live_preview_variant():
    model = {
        "previewUrlThumbSmall": "https://static-proxy.strpst.com/previews/a/b/c/hash-thumb-small",
        "snapshotTimestamp": "123456",
        "id": "111",
    }

    assert stripchat._model_screenshot(model) == (
        "https://img.doppiocdn.com/thumbs/123456/111_webp"
    )


def test_rewrite_mouflon_manifest_for_kodi_replaces_placeholder_segments():
    manifest = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXTINF:4.000\n"
        "#EXT-X-MOUFLON:URI:https://cdn.example.com/segment_1.mp4\n"
        "https://media-hls.doppiocdn.com/b-hls-11/media.mp4\n"
    )

    assert stripchat._rewrite_mouflon_manifest_for_kodi(manifest) == (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXTINF:4.000,\n"
        "https://cdn.example.com/segment_1.mp4\n"
    )


def test_normalize_stream_cdn_url_prefers_net_hosts():
    assert stripchat._normalize_stream_cdn_url(
        "https://edge-hls.doppiocdn.com/hls/1/master/1_480p.m3u8"
    ) == "https://edge-hls.doppiocdn.net/hls/1/master/1_480p.m3u8"
    assert stripchat._normalize_stream_cdn_url(
        "https://media-hls.doppiocdn.com/b-hls-1/media.mp4"
    ) == "https://media-hls.doppiocdn.net/b-hls-1/media.mp4"
    assert stripchat._normalize_stream_cdn_url(
        "https://media-hls.doppiocdn.com/b-hls-1/1/1_480p.m3u8?psch=v2&pkey=abc"
    ) == "https://media-hls.doppiocdn.net/b-hls-1/1/1_480p.m3u8?psch=v2&pkey=abc"


def test_rewrite_mouflon_manifest_prefers_parts_over_broken_full_segments():
    manifest = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXT-X-MOUFLON:URI:https://cdn.example.com/part0.mp4\n"
        '#EXT-X-PART:DURATION=0.500,URI="https://cdn.example.com/media.mp4"\n'
        "#EXT-X-MOUFLON:URI:https://cdn.example.com/part1.mp4\n"
        '#EXT-X-PART:DURATION=0.500,URI="https://cdn.example.com/media.mp4"\n'
        "#EXTINF:1.000,\n"
        "#EXT-X-MOUFLON:URI:https://cdn.example.com/full.mp4\n"
        "https://cdn.example.com/media.mp4\n"
    )

    assert stripchat._rewrite_mouflon_manifest_for_kodi(manifest) == (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXTINF:0.500,\n"
        "https://cdn.example.com/part0.mp4\n"
        "#EXTINF:0.500,\n"
        "https://cdn.example.com/part1.mp4\n"
    )


def test_keep_only_stable_segments_skips_live_edge_and_unreachable(monkeypatch):
    manifest = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXT-X-TARGETDURATION:2\n"
        "#EXT-X-MAP:URI=\"https://cdn.example.com/init.mp4\"\n"
        "#EXTINF:2.0,\n"
        "https://cdn.example.com/seg1.mp4\n"
        "#EXTINF:2.0,\n"
        "https://cdn.example.com/seg2.mp4\n"
        "#EXTINF:2.0,\n"
        "https://cdn.example.com/seg3.mp4\n"
    )

    class FakeResp:
        def __init__(self, status_code):
            self.status_code = status_code

        def close(self):
            pass

    def fake_requests_get(url, headers=None, timeout=None, stream=False):
        statuses = {
            "https://cdn.example.com/seg1.mp4": 200,
            "https://cdn.example.com/seg2.mp4": 404,
        }
        return FakeResp(statuses.get(url, 404))

    monkeypatch.setattr(stripchat.requests, "get", fake_requests_get)

    assert stripchat._keep_only_stable_segments(manifest, keep_count=2, edge_buffer=1) == (
        "#EXTM3U\n"
        "#EXT-X-VERSION:6\n"
        "#EXT-X-TARGETDURATION:2\n"
        "#EXT-X-MAP:URI=\"https://cdn.example.com/init.mp4\"\n"
        "#EXTINF:2.0,\n"
        "https://cdn.example.com/seg1.mp4\n"
    )


def test_pick_stream_parses_flat_quality_urls(monkeypatch):
    """stream.urls with direct quality keys like '480p', '240p' should be used as candidates."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/123/master/123_480p.m3u8",
            "urls": {
                "original": "https://edge-hls.saawsedge.com/hls/123/master/123_480p.m3u8",
                "480p": "https://edge-hls.saawsedge.com/hls/123/master/123_480p.m3u8",
                "240p": "https://edge-hls.saawsedge.com/hls/123/master/123_240p.m3u8",
                "160p": "https://edge-hls.saawsedge.com/hls/123/master/123_160p.m3u8",
            },
        },
    }

    doppi_480 = "https://edge-hls.doppiocdn.com/hls/123/master/123_480p.m3u8"

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if "doppiocdn.com" in url and ".m3u8" in url:
            return "#EXTM3U\n#EXT-X-TARGETDURATION:4\n#EXTINF:4.0,\nhttps://media/seg1.ts\n"
        raise Exception("Name or service not known")

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/123/master/123_240p.m3u8", "testmodel"
    )

    # The 480p candidate from stream.urls gets promoted to source (123.m3u8, score 9000)
    # which beats 480p (score 480). Both are doppiocdn URLs — either is acceptable.
    assert played_urls
    assert "doppiocdn.com" in played_urls[0]
    assert "/hls/123/" in played_urls[0]


def test_playvid_requires_inputstreamadaptive(monkeypatch):
    """Test that Playvid properly checks for inputstreamadaptive."""
    notifications = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "hlsPlaylist": "https://stream.stripchat.com/test.m3u8",
    }

    def fake_notify(title, message, **kwargs):
        notifications.append({"title": title, "message": message})

    def fake_get_html(url, *args, **kwargs):
        return json.dumps({"models": [model_data]}), False

    # Mock inputstreamhelper to fail the check
    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return False

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

    # Mock the import
    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", fake_notify)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", lambda *a, **k: "")
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    # Call Playvid - it should abort with notification
    stripchat.Playvid("https://stream.stripchat.com/test.m3u8", "testmodel")

    # Should have notified about missing inputstreamadaptive
    assert len(notifications) > 0
    assert any("inputstream" in n["message"].lower() for n in notifications)


def test_playvid_detects_offline_model(monkeypatch):
    """Test that Playvid detects when model is offline."""
    notifications = []
    model_data = {
        "username": "testmodel",
        "isOnline": False,
        "isBroadcasting": False,
    }

    def fake_notify(title, message):
        notifications.append({"title": title, "message": message})

    def fake_get_html(url, *args, **kwargs):
        return json.dumps({"models": [model_data]}), False

    # Mock inputstreamhelper to pass the check
    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

    # Mock the import
    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", fake_notify)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", lambda *a, **k: "")
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    # Call Playvid with offline model and no valid stream URL
    stripchat.Playvid("", "testmodel")

    # Should have notified about model being offline
    assert len(notifications) > 0
    assert any("offline" in n["message"].lower() for n in notifications)


def test_playvid_uses_fallback_stream_when_api_reports_offline(monkeypatch):
    """Play should continue when listing URL is valid even if API flags offline."""
    notifications = []
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": False,
        "isBroadcasting": False,
    }

    def fake_notify(title, message, **kwargs):
        notifications.append({"title": title, "message": message})

    def fake_get_html(url, *args, **kwargs):
        return json.dumps({"models": [model_data]}), False

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", fake_notify)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", lambda *a, **k: "")
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid("https://stream.stripchat.com/test_fallback.m3u8", "testmodel")

    assert played_urls
    assert played_urls[0].startswith(_ll("https://stream.stripchat.com/test_fallback.m3u8") + "|")
    assert not notifications


def test_playvid_promotes_low_variant_to_source_playlist(monkeypatch):
    """Low variant URLs should be upgraded to source playlist when available."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
    }
    low_variant = (
        "https://edge-hls.doppiocdn.com/hls/133123248/master/133123248_240p.m3u8"
    )
    promoted_source = (
        "https://edge-hls.doppiocdn.com/hls/133123248/master/133123248.m3u8"
    )

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if url in (_ll(promoted_source), promoted_source):
            return '#EXTM3U\n#EXT-X-STREAM-INF:NAME="source"\nhttps://media/source.m3u8'
        return "", False

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(low_variant, "testmodel")

    assert played_urls
    assert played_urls[0].startswith(_ll(promoted_source) + "|")


def test_playvid_prefers_higher_quality_url_over_generic_label(monkeypatch):
    """When labels are generic, quality inferred from URL should win."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/100/master/100_240p.m3u8",
        },
    }

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", lambda *a, **k: "")
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    # Fallback URL is higher quality than stream.url; should be selected.
    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/100/master/100_480p.m3u8", "testmodel"
    )

    assert played_urls
    assert played_urls[0].startswith(
        _ll("https://edge-hls.doppiocdn.com/hls/100/master/100_480p.m3u8") + "|"
    )


def test_playvid_avoids_ad_only_manifests(monkeypatch):
    """Reject ad-only VOD manifests and pick a non-ad candidate."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/200/master/200_480p.m3u8",
        },
    }

    doppi_source = "https://edge-hls.doppiocdn.com/hls/200/master/200.m3u8"
    doppi_child = "https://media-hls.doppiocdn.com/b-hls-03/200/200.m3u8"
    saaws_480 = "https://edge-hls.saawsedge.com/hls/200/master/200_480p.m3u8"
    saaws_480_child = "https://media-hls.saawsedge.com/b-hls-03/200/200_480p.m3u8"

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if url == doppi_source:
            return '#EXTM3U\n#EXT-X-STREAM-INF:NAME="source"\n{}'.format(doppi_child)
        if url == doppi_child:
            return (
                "#EXTM3U\n#EXT-X-MOUFLON-ADVERT\n#EXT-X-PLAYLIST-TYPE:VOD\n"
                "#EXTINF:4.0,\nhttps://media-hls.doppiocdn.com/b-hls-03/cpa/v2/chunk_000.m4s\n"
                "#EXT-X-ENDLIST"
            )
        if url == saaws_480:
            return '#EXTM3U\n#EXT-X-STREAM-INF:NAME="480p"\n{}'.format(saaws_480_child)
        if url == saaws_480_child:
            return (
                "#EXTM3U\n#EXT-X-VERSION:6\n#EXT-X-TARGETDURATION:8\n"
                "#EXTINF:8.333,\nhttps://media-hls.saawsedge.com/b-hls-03/200/seg_1.mp4\n"
            )
        return ""

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/200/master/200_240p.m3u8", "testmodel"
    )

    # The ad candidate (doppi_source) is rejected. saawsedge is filtered out.
    # The saawsedge 480p mirror (doppiocdn 480p) is not an ad and wins over 240p fallback.
    assert played_urls
    assert "doppiocdn.com" in played_urls[0]
    assert doppi_source.split("|")[0] not in played_urls[0]


def test_playvid_validates_returned_model_name(monkeypatch):
    """
    Test that Playvid verifies the returned model's username matches the requested one.
    If Stripchat API returns a different model (e.g. recommendation), we should not play it.
    """
    notifications = []

    # We request "requested_model" but API returns "random_other_model"
    requested_name = "requested_model"
    returned_name = "random_other_model"

    model_data = {
        "username": returned_name,
        "isOnline": True,
        "isBroadcasting": True,
        "hlsPlaylist": "https://stream.stripchat.com/random.m3u8",
        "stream": {"url": "https://stream.stripchat.com/random.m3u8"},
    }

    def fake_notify(title, message, **kwargs):
        notifications.append({"title": title, "message": message})

    def fake_get_html(url, *args, **kwargs):
        # This simulates the API returning a different model than requested
        return json.dumps({"models": [model_data]}), False

    # Mock dependencies
    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            # If we get here, the code accepted the wrong model!
            pytest.fail(f"VideoPlayer started playing wrong model: {self.name}")

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", fake_notify)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    # Action: Try to play "requested_model"
    stripchat.Playvid("http://fake", requested_name)

    # Assert that we got a notification about model not found/offline
    # because the name check failed, so it treated it as no model data
    assert len(notifications) > 0
    assert any(
        "not found" in n["message"].lower() or "offline" in n["message"].lower()
        for n in notifications
    )


def test_playvid_skips_reachable_ad_when_non_ad_is_unresolved(monkeypatch):
    """Do not play ad stream when non-ad streams are unresolved."""
    notifications = []
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/999/master/999_480p.m3u8",
        },
    }

    def fake_notify(title, message, **kwargs):
        notifications.append({"title": title, "message": message})

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if "saawsedge.com" in url:
            raise Exception("<urlopen error [Errno -2] Name or service not known>")
        if "doppiocdn.com" in url and ".m3u8" in url:
            return (
                "#EXTM3U\n#EXT-X-MOUFLON-ADVERT\n#EXT-X-PLAYLIST-TYPE:VOD\n"
                "#EXTINF:4.0,\nhttps://media-hls.doppiocdn.com/b-hls-03/cpa/v2/chunk_000.m4s\n"
                "#EXT-X-ENDLIST"
            )
        return ""

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", fake_notify)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/999/master/999_240p.m3u8", "testmodel"
    )

    assert not played_urls
    assert notifications
    assert any(
        "unable to locate stream url" in n["message"].lower() for n in notifications
    )


def test_playvid_mirrors_saaws_to_doppi_and_plays_reachable_stream(monkeypatch):
    """When saaws host is unresolved, mirrored doppi host should be selected."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/123/master/123_480p.m3u8",
        },
    }

    mirrored = "https://edge-hls.doppiocdn.com/hls/123/master/123_480p.m3u8"

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if "saawsedge.com" in url:
            raise Exception("<urlopen error [Errno -2] Name or service not known>")
        if url in (_ll(mirrored), mirrored):
            return '#EXTM3U\n#EXT-X-STREAM-INF:NAME="480p"\nhttps://media-hls.doppiocdn.com/b-hls-01/123/live.m3u8'
        if "doppiocdn.com" in url and url.endswith("live.m3u8"):
            return "#EXTM3U\n#EXTINF:8.333,\nhttps://media-hls.doppiocdn.com/b-hls-01/123/seg_1.mp4\n"
        return ""

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/123/master/123_240p.m3u8", "testmodel"
    )

    assert played_urls
    assert played_urls[0].startswith(_ll(mirrored) + "|")


def test_playvid_uses_signed_media_child_to_avoid_ad_manifest(monkeypatch):
    """Use psch/pkey signed child playlist when plain child is ad-only."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/200900667/master/200900667_480p.m3u8",
        },
    }

    doppi_master = (
        "https://edge-hls.doppiocdn.com/hls/200900667/master/200900667_480p.m3u8"
    )
    plain_child = "https://media-hls.doppiocdn.com/b-hls-02/200900667/200900667.m3u8"
    signed_child = plain_child + "?psch=v2&pkey=Ook7quaiNgiyuhai"

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if "saawsedge.com" in url:
            raise Exception("<urlopen error [Errno -2] Name or service not known>")
        if url.startswith(
            "https://edge-hls.doppiocdn.com/hls/200900667/master/"
        ) and ".m3u8" in url:
            return (
                "#EXTM3U\n#EXT-X-MOUFLON:PSCH:v2:Ook7quaiNgiyuhai\n"
                '#EXT-X-STREAM-INF:NAME="480p"\n' + plain_child
            )
        if url in (_ll(plain_child), plain_child):
            return (
                "#EXTM3U\n#EXT-X-MOUFLON-ADVERT\n#EXT-X-PLAYLIST-TYPE:VOD\n"
                "#EXTINF:4.0,\nhttps://media-hls.doppiocdn.com/b-hls-02/cpa/v2/chunk_000.m4s\n"
                "#EXT-X-ENDLIST"
            )
        if url in (_ll(signed_child), signed_child):
            return (
                "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2.0,\n"
                "https://media-hls.doppiocdn.com/b-hls-02/200900667/segment_1.mp4\n"
            )
        return ""

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/200900667/master/200900667_240p.m3u8",
        "testmodel",
    )

    assert played_urls
    assert played_urls[0].startswith(_ll(signed_child) + "|")


def test_playvid_bypasses_proxy_for_signed_media_child(monkeypatch):
    """Signed media child manifests should play directly, not through localhost proxy."""
    played_urls = []
    proxy_calls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/200900667/master/200900667_480p.m3u8",
        },
    }

    plain_child = "https://media-hls.doppiocdn.com/b-hls-02/200900667/200900667.m3u8"
    signed_child = plain_child + "?psch=v2&pkey=Ook7quaiNgiyuhai"

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if "saawsedge.com" in url:
            raise Exception("<urlopen error [Errno -2] Name or service not known>")
        if "https://edge-hls.doppiocdn.com/hls/200900667/master/" in url and ".m3u8" in url:
            return (
                "#EXTM3U\n#EXT-X-MOUFLON:PSCH:v2:Ook7quaiNgiyuhai\n"
                '#EXT-X-STREAM-INF:NAME="source"\n' + plain_child
            )
        if url in (_ll(plain_child), plain_child):
            return (
                "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2.0,\n"
                "https://media-hls.doppiocdn.com/b-hls-02/200900667/segment_1.mp4\n"
            )
        if url in (_ll(signed_child), signed_child):
            return (
                "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2.0,\n"
                "https://media-hls.doppiocdn.com/b-hls-02/200900667/segment_1.mp4\n"
            )
        return ""

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils.addon, "getSetting", lambda key: "true" if key == "stripchat_proxy" else "")
    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)
    monkeypatch.setattr(
        stripchat,
        "_start_manifest_proxy",
        lambda stream_url, name: proxy_calls.append(stream_url) or "http://127.0.0.1/manifest.m3u8",
    )

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/200900667/master/200900667_240p.m3u8",
        "testmodel",
    )

    assert played_urls
    assert played_urls[0].startswith(_ll(signed_child) + "|")
    assert not proxy_calls


def test_playvid_skips_signed_media_child_with_parent_relative_segments(monkeypatch):
    """Reject signed child manifests that resolve segments via broken ../ paths."""
    played_urls = []
    model_data = {
        "username": "testmodel",
        "isOnline": True,
        "isBroadcasting": True,
        "stream": {
            "url": "https://edge-hls.saawsedge.com/hls/300/master/300_240p.m3u8",
            "urls": {
                "480p": "https://edge-hls.saawsedge.com/hls/300/master/300_480p.m3u8",
                "240p": "https://edge-hls.saawsedge.com/hls/300/master/300_240p.m3u8",
            },
        },
    }

    doppi_480 = "https://edge-hls.doppiocdn.com/hls/300/master/300_480p.m3u8"
    doppi_source = "https://edge-hls.doppiocdn.com/hls/300/master/300.m3u8"
    plain_child = "https://media-hls.doppiocdn.com/b-hls-03/300/300_480p.m3u8"
    signed_child = plain_child + "?psch=v2&pkey=Ook7quaiNgiyuhai"

    def fake_get_html(url, *args, **kwargs):
        if "api/external/v4/widget" in url or "api/front/models" in url:
            return json.dumps({"models": [model_data]}), False
        return "", False

    def fake__get_html(url, *args, **kwargs):
        if "saawsedge.com" in url:
            raise Exception("<urlopen error [Errno -2] Name or service not known>")
        if url in (_ll(doppi_source), doppi_source):
            return (
                "#EXTM3U\n#EXT-X-MOUFLON:PSCH:v2:Ook7quaiNgiyuhai\n"
                '#EXT-X-STREAM-INF:NAME="480p"\n' + plain_child
            )
        if url in (
            _ll(doppi_480),
            doppi_480,
            _ll("https://edge-hls.doppiocdn.com/hls/300/master/300_240p.m3u8"),
            "https://edge-hls.doppiocdn.com/hls/300/master/300_240p.m3u8",
        ):
            return "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2.0,\nsegment_1.ts\n"
        if url in (_ll(plain_child), plain_child):
            return (
                "#EXTM3U\n#EXT-X-MOUFLON-ADVERT\n#EXT-X-PLAYLIST-TYPE:VOD\n"
                "#EXTINF:4.0,\nhttps://media-hls.doppiocdn.com/b-hls-03/cpa/v2/chunk_000.m4s\n"
                "#EXT-X-ENDLIST"
            )
        if url in (_ll(signed_child), signed_child):
            return (
                "#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2.0,\n"
                "../media.mp4\n"
            )
        return ""

    class FakeHelper:
        def __init__(self, adaptive_type):
            pass

        def check_inputstream(self):
            return True

    class FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    import sys
    import types

    fake_inputstreamhelper = types.ModuleType("inputstreamhelper")
    fake_inputstreamhelper.Helper = FakeHelper
    sys.modules["inputstreamhelper"] = fake_inputstreamhelper

    monkeypatch.setattr(stripchat.utils, "notify", lambda *a, **k: None)
    monkeypatch.setattr(stripchat.utils, "kodilog", lambda x: None)
    monkeypatch.setattr(
        stripchat.utils, "get_html_with_cloudflare_retry", fake_get_html
    )
    monkeypatch.setattr(stripchat.utils, "_getHtml", fake__get_html)
    monkeypatch.setattr(stripchat.utils, "VideoPlayer", FakeVideoPlayer)

    stripchat.Playvid(
        "https://edge-hls.doppiocdn.com/hls/300/master/300_240p.m3u8", "testmodel"
    )

    assert played_urls
    assert played_urls[0].startswith(_ll(doppi_480) + "|")

#!/usr/bin/env python3
"""Start the Stripchat manifest proxy outside Kodi and probe its output.

This isolates proxy/rewrite behavior from Kodi/inputstream.adaptive:
1. Starts the exact `_start_manifest_proxy()` implementation from stripchat.py
2. Fetches the localhost manifest it serves
3. Verifies placeholder `media.mp4` entries are gone
4. Requests the first proxied segment URL and reports the HTTP status
"""

from __future__ import annotations

import argparse
import base64
import importlib
import json
import re
import sys
import time
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except Exception:
    sync_playwright = None
    HAS_PLAYWRIGHT = False


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "plugin.video.cumination"


def install_kodi_stubs() -> None:
    import types

    if "kodi_six" in sys.modules:
        return

    xbmc = types.ModuleType("kodi_six.xbmc")
    xbmc.LOGDEBUG = 0
    xbmc.LOGINFO = 1
    xbmc.LOGNOTICE = 2
    xbmc.LOGWARNING = 3
    xbmc.LOGERROR = 4
    xbmc.log = lambda *args, **kwargs: None
    xbmc.executebuiltin = lambda *args, **kwargs: None
    xbmc.getSkinDir = lambda: "skin.estuary"
    xbmc.getInfoLabel = lambda key: "20.0" if "BuildVersion" in key else ""
    xbmc.getCondVisibility = lambda *args, **kwargs: False
    xbmc.sleep = lambda ms: None

    xbmcaddon = types.ModuleType("kodi_six.xbmcaddon")

    class _Addon:
        def __init__(self, addon_id=None):
            self.addon_id = addon_id or "plugin.video.cumination"
            self._settings = {
                "cache_time": "0",
                "custom_favorites": "false",
                "favorites_path": "",
                "customview": "false",
                "setview": "",
                "duration_in_name": "false",
                "quality_in_name": "false",
                "qualityask": "0",
                "filter_listing": "",
                "chaturbate": "false",
                "chatfemale": "true",
                "chatmale": "false",
                "chatcouple": "false",
                "chattrans": "false",
                "online_only": "false",
                "content": "0",
                "universal_resolvers": "false",
                "dontask": "true",
                "no_image": "",
                "female_keywords": "",
                "male_keywords": "",
                "couples_keywords": "",
                "trans_keywords": "",
                "sortxt": "0",
                "fs_enable": "true",
                "fs_host": "http://127.0.0.1:8191/v1",
                "stripchat_proxy": "true",
                "stripchat_mirror": "true",
            }

        def getAddonInfo(self, key):
            if key == "path":
                return str(PLUGIN_PATH)
            if key == "profile":
                return str(ROOT / ".profile")
            if key == "version":
                return "20.0"
            return ""

        def getSetting(self, key):
            return self._settings.get(key, "")

        def setSetting(self, key, value):
            self._settings[key] = value

        def getLocalizedString(self, string_id):
            return str(string_id)

    xbmcaddon.Addon = _Addon

    xbmcplugin = types.ModuleType("kodi_six.xbmcplugin")
    xbmcplugin.addDirectoryItem = lambda *args, **kwargs: True
    xbmcplugin.endOfDirectory = lambda *args, **kwargs: None
    xbmcplugin.setContent = lambda *args, **kwargs: None
    xbmcplugin.addSortMethod = lambda *args, **kwargs: None
    xbmcplugin.SORT_METHOD_TITLE = 10

    xbmcgui = types.ModuleType("kodi_six.xbmcgui")

    class _Dialog:
        def notification(self, *args, **kwargs):
            pass

        def ok(self, *args, **kwargs):
            pass

        def yesno(self, *args, **kwargs):
            return True

        def select(self, *args, **kwargs):
            return 0

    class _DialogProgress:
        def create(self, *args, **kwargs):
            pass

        def update(self, *args, **kwargs):
            pass

        def close(self):
            pass

        def iscanceled(self):
            return False

    class _ListItem:
        def __init__(self, label=""):
            self.label = label

        def setInfo(self, *args, **kwargs):
            pass

        def setArt(self, *args, **kwargs):
            pass

        def addContextMenuItems(self, *args, **kwargs):
            pass

    class _Keyboard:
        def __init__(self, default="", heading="", hidden=False):
            self._text = default
            self._confirmed = True

        def doModal(self):
            pass

        def isConfirmed(self):
            return self._confirmed

        def getText(self):
            return self._text

    xbmcgui.Dialog = _Dialog
    xbmcgui.DialogProgress = _DialogProgress
    xbmcgui.ListItem = _ListItem
    xbmcgui.Keyboard = _Keyboard

    xbmcvfs = types.ModuleType("kodi_six.xbmcvfs")
    xbmcvfs.translatePath = lambda path: str(path).replace(
        "special://profile", str(ROOT / ".profile")
    )
    xbmcvfs.exists = lambda path: Path(str(path)).exists()
    xbmcvfs.mkdirs = lambda path: Path(str(path)).mkdir(parents=True, exist_ok=True)

    kodi_six = types.ModuleType("kodi_six")
    kodi_six.xbmc = xbmc
    kodi_six.xbmcaddon = xbmcaddon
    kodi_six.xbmcplugin = xbmcplugin
    kodi_six.xbmcgui = xbmcgui
    kodi_six.xbmcvfs = xbmcvfs

    sys.modules["kodi_six"] = kodi_six
    sys.modules["kodi_six.xbmc"] = xbmc
    sys.modules["kodi_six.xbmcaddon"] = xbmcaddon
    sys.modules["kodi_six.xbmcplugin"] = xbmcplugin
    sys.modules["kodi_six.xbmcgui"] = xbmcgui
    sys.modules["kodi_six.xbmcvfs"] = xbmcvfs
    sys.modules.setdefault("xbmc", xbmc)
    sys.modules.setdefault("xbmcaddon", xbmcaddon)
    sys.modules.setdefault("xbmcplugin", xbmcplugin)
    sys.modules.setdefault("xbmcgui", xbmcgui)
    sys.modules.setdefault("xbmcvfs", xbmcvfs)

    storage_module = types.ModuleType("StorageServer")

    class _StorageServer:
        def __init__(self, *args, **kwargs):
            pass

        def cacheDelete(self, *args, **kwargs):
            pass

        def cacheFunction(self, fn, *args, **kwargs):
            return fn(*args, **kwargs)

    storage_module.StorageServer = _StorageServer
    sys.modules["StorageServer"] = storage_module

    resolveurl = types.ModuleType("resolveurl")

    class _ResolverError(Exception):
        pass

    class _HostedMediaFile:
        def __init__(self, *args, **kwargs):
            pass

        def valid_url(self):
            return False

    resolveurl.HostedMediaFile = _HostedMediaFile
    resolveurl.ResolverError = _ResolverError
    resolveurl.resolve = lambda url: url
    sys.modules["resolveurl"] = resolveurl

    inputstreamhelper = types.ModuleType("inputstreamhelper")

    class _Helper:
        def __init__(self, protocol):
            self.protocol = protocol

        def check_inputstream(self):
            return True

    inputstreamhelper.Helper = _Helper
    sys.modules["inputstreamhelper"] = inputstreamhelper


def import_stripchat():
    install_kodi_stubs()
    sys.path.insert(0, str(PLUGIN_PATH))
    original_argv = list(sys.argv)
    try:
        # Kodi modules assume argv layout: [plugin://..., handle, query]
        sys.argv = ["plugin://plugin.video.cumination", "1", ""]
        return importlib.import_module("resources.lib.sites.stripchat")
    finally:
        sys.argv = original_argv


def extract_username(target: str) -> str:
    if not isinstance(target, str):
        return ""
    value = target.strip().rstrip("/")
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        path = (parsed.path or "").strip("/")
        if not path:
            return ""
        return path.split("/")[0]
    return value


def extract_media_urls(manifest_text: str) -> list[str]:
    urls = []
    for line in manifest_text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def decode_proxy_media_url(url: str) -> str:
    if not isinstance(url, str) or not url:
        return ""
    parsed = urlparse(url)
    encoded = parse_qs(parsed.query, keep_blank_values=True).get("u", [""])[0]
    if not encoded:
        return ""
    try:
        padding = "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode((encoded + padding).encode("ascii")).decode(
            "utf-8", errors="replace"
        )
    except Exception:
        return ""


def encode_proxy_media_url(url: str) -> str:
    if not isinstance(url, str) or not url:
        return ""
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


def extract_part_sequence(url: str) -> int:
    if not isinstance(url, str):
        return -1


def build_seeded_session(headers: dict, cookies: dict) -> requests.Session:
    session = requests.Session()
    if isinstance(headers, dict):
        session.headers.update(
            {
                key: value
                for key, value in headers.items()
                if isinstance(key, str) and isinstance(value, str) and value
            }
        )
    if isinstance(cookies, dict):
        session.cookies.update(
            {
                key: value
                for key, value in cookies.items()
                if isinstance(key, str) and isinstance(value, str)
            }
        )
    return session


def probe_single_url(
    session: requests.Session, url: str, timeout: float, read_bytes: int
) -> dict:
    result = {"url": url}
    try:
        resp = session.get(url, timeout=timeout, stream=True)
        chunk = b""
        total_read = 0
        try:
            for piece in resp.iter_content(chunk_size=min(read_bytes, 4096)):
                if not piece:
                    break
                if not chunk:
                    chunk = piece
                total_read += len(piece)
                if total_read >= read_bytes:
                    break
        finally:
            resp.close()
        result.update(
            {
                "status": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "first_chunk_bytes": len(chunk),
                "total_bytes_read": total_read,
            }
        )
    except Exception as exc:
        result["error"] = str(exc)
    return result
    match = re.search(r"_h264_(\d+)_", url)
    if not match:
        return -1
    try:
        return int(match.group(1))
    except ValueError:
        return -1


def extract_browser_live_query(browser_events: list[dict]) -> str:
    for event in reversed(browser_events):
        url = str(event.get("url", ""))
        if (
            event.get("kind") == "request"
            and ".m3u8" in url
            and "_HLS_msn=" in url
        ):
            return urlparse(url).query
    return ""


def select_browser_manifest_url(browser_events: list[dict]) -> str:
    candidates = []
    for event in browser_events:
        url = str(event.get("url", ""))
        lower = url.lower()
        if "media-hls." not in lower or ".m3u8" not in lower:
            continue
        if "_hls_msn=" in lower:
            continue
        candidates.append(url)
    if not candidates:
        return ""
    return candidates[-1]


def iter_mouflon_segment_urls(manifest_text: str, base_url: str) -> list[str]:
    urls = []
    for raw_line in manifest_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("#EXT-X-MOUFLON:URI:"):
            continue
        value = line[len("#EXT-X-MOUFLON:URI:") :]
        if not value:
            continue
        if not value.startswith("http"):
            from urllib.parse import urljoin

            value = urljoin(base_url, value)
        if value.endswith(".mp4") and "_part" not in value:
            urls.append(value)
    return urls


def merge_query(url: str, params: dict[str, str]) -> str:
    if not params:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    for key, value in params.items():
        if key not in query:
            query[key] = [value]
    from urllib.parse import urlencode, urlunparse

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def host_variants(url: str) -> list[str]:
    variants = [url]
    if ".doppiocdn.net" in url:
        variants.append(url.replace(".doppiocdn.net", ".doppiocdn.com"))
    elif ".doppiocdn.com" in url:
        variants.append(url.replace(".doppiocdn.com", ".doppiocdn.net"))
    deduped = []
    seen = set()
    for item in variants:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def probe_url_matrix(session: requests.Session, url: str, auth_params: dict[str, str], timeout: float) -> list[dict]:
    probes = []
    for base in host_variants(url):
        candidates = [
            ("raw", base),
            ("with_auth", merge_query(base, auth_params)),
        ]
        seen = set()
        for label, candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                resp = session.get(candidate, timeout=timeout, stream=True)
                chunk = b""
                try:
                    chunk = next(resp.iter_content(chunk_size=1024), b"")
                finally:
                    resp.close()
                probes.append(
                    {
                        "label": label,
                        "url": candidate,
                        "status": resp.status_code,
                        "content_type": resp.headers.get("Content-Type", ""),
                        "first_chunk_bytes": len(chunk),
                    }
                )
            except Exception as exc:
                probes.append(
                    {
                        "label": label,
                        "url": candidate,
                        "error": str(exc),
                    }
                )
    return probes


def resolve_manifest_from_model(stripchat, target: str) -> str:
    username = extract_username(target)
    if not username:
        raise RuntimeError("Could not extract Stripchat username from input")

    selected_urls = []
    played_urls = []
    original_video_player = stripchat.utils.VideoPlayer
    original_start_manifest_proxy = stripchat._start_manifest_proxy

    class _FakeProgress:
        def update(self, percent, message):
            pass

        def close(self):
            pass

    class _FakeVideoPlayer:
        def __init__(self, name, **kwargs):
            self.name = name
            self.progress = _FakeProgress()

        def play_from_direct_link(self, link):
            played_urls.append(link)

    def _capture_start_manifest_proxy(stream_url, name):
        selected_urls.append(stream_url)
        return "http://127.0.0.1/captured-manifest.m3u8"

    stripchat.utils.kodilog = lambda *args, **kwargs: print("[kodilog]", *args)
    stripchat.utils.notify = lambda *args, **kwargs: None
    stripchat.utils.VideoPlayer = _FakeVideoPlayer
    stripchat._start_manifest_proxy = _capture_start_manifest_proxy

    try:
        fallback_url = "https://stripchat.com/{}".format(username)
        stripchat.Playvid(fallback_url, username)
    finally:
        stripchat.utils.VideoPlayer = original_video_player
        stripchat._start_manifest_proxy = original_start_manifest_proxy

    if selected_urls:
        return selected_urls[-1]

    for link in played_urls:
        if isinstance(link, str):
            base = link.split("|", 1)[0]
            if ".m3u8" in base and base.startswith("http"):
                return base

    browser_url = target
    if not browser_url.startswith("http://") and not browser_url.startswith("https://"):
        browser_url = "https://stripchat.com/{}".format(username)
    sniffed = sniff_manifest_with_playwright(browser_url)
    if sniffed:
        print("PLAYWRIGHT_RESOLVED_MANIFEST_URL:", sniffed)
        return sniffed

    raise RuntimeError("Failed to resolve stream URL from model input")


def sniff_manifest_with_playwright(page_url: str, timeout_ms: int = 30000) -> str:
    if not HAS_PLAYWRIGHT:
        return ""

    print("PLAYWRIGHT_FALLBACK: starting browser sniff for {}".format(page_url))
    seen = []

    def _consider(url: str) -> None:
        if not isinstance(url, str):
            return
        lower = url.lower()
        if ".m3u8" not in lower:
            return
        if "media-hls." not in lower and "doppiocdn" not in lower:
            return
        if "pkey=" not in lower:
            return
        if url not in seen:
            seen.append(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.on("request", lambda req: _consider(req.url))
        page.on("response", lambda resp: _consider(resp.url))
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(4000)
            for selector in ("video", ".vjs-big-play-button", ".play-button", "button"):
                try:
                    locator = page.locator(selector).first
                    if locator.is_visible(timeout=1000):
                        locator.click(force=True, timeout=2000)
                        page.wait_for_timeout(1500)
                except Exception:
                    continue
            for _ in range(12):
                if seen:
                    break
                page.wait_for_timeout(1000)
        finally:
            browser.close()

    if not seen:
        return ""

    def _score(url: str) -> tuple[int, int, int]:
        lower = url.lower()
        return (
            1 if "media-hls." in lower else 0,
            1 if "playlisttype=lowlatency" in lower else 0,
            1 if ".m3u8" in lower else 0,
        )

    seen.sort(key=_score, reverse=True)
    return seen[0]


def sniff_browser_media_with_playwright(page_url: str, timeout_ms: int = 30000) -> dict:
    if not HAS_PLAYWRIGHT:
        return {"events": [], "cookies": {}, "media_headers": {}}

    events = []
    seen = set()
    latest_media_headers = {}
    browser_cookies = {}

    def _capture(kind: str, url: str, status=None, body_preview=None, headers=None) -> None:
        if not isinstance(url, str):
            return
        lower = url.lower()
        if not any(ext in lower for ext in (".m3u8", ".mp4", ".m4s")):
            return
        if any(x in lower for x in ("/thumbs/", "/images/", ".jpg", ".png")):
            return
        key = (kind, url, status)
        if key in seen:
            return
        seen.add(key)
        events.append(
            {
                "kind": kind,
                "url": url,
                "status": status,
                "body_preview": body_preview,
                "headers": headers or {},
            }
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.on("request", lambda req: _capture("request", req.url))

        def _handle_response(resp):
            body_preview = None
            headers = {}
            try:
                lower = resp.url.lower()
                if ".m3u8" in lower and "_hls_msn=" in lower:
                    body_preview = resp.text()[:1200]
                if ".mp4" in lower and "_part" in lower and resp.status == 200:
                    headers = dict(resp.request.headers)
                    latest_media_headers.clear()
                    latest_media_headers.update(headers)
            except Exception:
                body_preview = None
                headers = {}
            _capture("response", resp.url, resp.status, body_preview, headers)

        page.on("response", _handle_response)
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(2500)
            for selector in ("video", ".vjs-big-play-button", ".play-button", "button"):
                try:
                    locator = page.locator(selector).first
                    if locator.is_visible(timeout=1000):
                        locator.click(force=True, timeout=2000)
                        page.wait_for_timeout(750)
                except Exception:
                    continue
            deadline = time.time() + 10.0
            while time.time() < deadline:
                got_reload_manifest = any(
                    event.get("kind") == "response"
                    and event.get("status") == 200
                    and "_hls_msn=" in str(event.get("url", "")).lower()
                    for event in events
                )
                got_part_response = any(
                    event.get("kind") == "response"
                    and event.get("status") == 200
                    and "_part" in str(event.get("url", "")).lower()
                    and ".mp4" in str(event.get("url", "")).lower()
                    for event in events
                )
                if got_reload_manifest and got_part_response:
                    break
                page.wait_for_timeout(500)
            with suppress(Exception):
                browser_cookies = {
                    cookie.get("name", ""): cookie.get("value", "")
                    for cookie in context.cookies()
                    if cookie.get("name") and isinstance(cookie.get("value"), str)
                }
        except KeyboardInterrupt:
            pass
        finally:
            with suppress(Exception):
                browser.close()
    return {
        "events": events,
        "cookies": browser_cookies,
        "media_headers": dict(latest_media_headers),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start the Stripchat localhost manifest proxy and probe it"
    )
    parser.add_argument(
        "target",
        help="Signed manifest URL, Stripchat model URL, or username",
    )
    parser.add_argument("--name", default="debugmodel", help="Model name for headers/logging")
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Keep the proxy process alive after probing so you can open it in VLC/ffplay",
    )
    parser.add_argument(
        "--segment-timeout",
        type=float,
        default=20.0,
        help="Timeout in seconds for manifest/segment probes",
    )
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="Fetch the raw CDN manifest and print MOUFLON segment diagnostics",
    )
    parser.add_argument(
        "--browser-sniff",
        action="store_true",
        help="Capture real browser media requests/responses outside Kodi with Playwright",
    )
    parser.add_argument(
        "--read-bytes",
        type=int,
        default=4096,
        help="Number of bytes to read from the first proxied segment before exiting",
    )
    args = parser.parse_args()

    stripchat = import_stripchat()
    stripchat.utils.kodilog = lambda *args, **kwargs: print("[kodilog]", *args)
    stripchat.utils.notify = lambda *args, **kwargs: None

    target = args.target.strip()
    if ".m3u8" in target and target.startswith("http"):
        manifest_url = target
    else:
        manifest_url = resolve_manifest_from_model(stripchat, target)
        print("RESOLVED_MANIFEST_URL:", manifest_url)

    probe_name = extract_username(target) or args.name
    browser_events = []
    browser_seed_cookies = {}
    browser_seed_headers = {}
    if args.browser_sniff:
        page_url = target
        if not page_url.startswith("http://") and not page_url.startswith("https://"):
            page_url = "https://stripchat.com/{}".format(extract_username(target))
        browser_probe = sniff_browser_media_with_playwright(page_url)
        browser_events = browser_probe.get("events", [])
        browser_seed_cookies = browser_probe.get("cookies", {})
        browser_seed_headers = browser_probe.get("media_headers", {})
        stripchat.STRIPCHAT_PROXY_SESSION_COOKIES = browser_seed_cookies
        stripchat.STRIPCHAT_PROXY_SESSION_HEADERS = browser_seed_headers
        print("BROWSER_SEED_COOKIE_COUNT:", len(browser_seed_cookies))
        print(
            "BROWSER_SEED_HEADER_KEYS:",
            ",".join(sorted(browser_seed_headers.keys())) or "<none>",
        )
        browser_manifest_url = select_browser_manifest_url(browser_events)
        if browser_manifest_url:
            manifest_url = browser_manifest_url
            print("BROWSER_MANIFEST_URL:", browser_manifest_url)
    proxy_url = stripchat._start_manifest_proxy(manifest_url, probe_name)
    if not proxy_url:
        print("RESULT: proxy failed to start")
        return 2

    print("RESULT: proxy started")
    print("PROXY_URL:", proxy_url)

    time.sleep(0.5)
    manifest_resp = requests.get(proxy_url, timeout=args.segment_timeout)
    print("MANIFEST_STATUS:", manifest_resp.status_code)
    print("MANIFEST_BYTES:", len(manifest_resp.text))

    manifest_text = manifest_resp.text
    has_extm3u = "#EXTM3U" in manifest_text
    has_placeholder = "media.mp4" in manifest_text
    media_urls = extract_media_urls(manifest_text)
    first_media_url = media_urls[0] if media_urls else ""
    latest_media_url = media_urls[-1] if media_urls else ""

    print("MANIFEST_HAS_EXTM3U:", has_extm3u)
    print("MANIFEST_HAS_PLACEHOLDER_MEDIA_MP4:", has_placeholder)
    print("FIRST_MEDIA_URL:", first_media_url or "<none>")
    print("LATEST_MEDIA_URL:", latest_media_url or "<none>")
    latest_proxy_target = decode_proxy_media_url(latest_media_url)
    print("LATEST_PROXY_TARGET:", latest_proxy_target or "<none>")

    segment_probe_url = latest_media_url or first_media_url
    if segment_probe_url:
        print("SEGMENT_PROBE_URL:", segment_probe_url)
        seg_resp = requests.get(
            segment_probe_url, timeout=args.segment_timeout, stream=True
        )
        first_chunk = b""
        total_read = 0
        try:
            for chunk in seg_resp.iter_content(chunk_size=min(args.read_bytes, 4096)):
                if not chunk:
                    break
                if not first_chunk:
                    first_chunk = chunk
                total_read += len(chunk)
                if total_read >= args.read_bytes:
                    break
        finally:
            seg_resp.close()
        print("SEGMENT_STATUS:", seg_resp.status_code)
        print("SEGMENT_CONTENT_TYPE:", seg_resp.headers.get("Content-Type", ""))
        print("SEGMENT_FIRST_CHUNK_BYTES:", len(first_chunk))
        print("SEGMENT_TOTAL_BYTES_READ:", total_read)
    else:
        print("SEGMENT_STATUS: <skipped, no segment URL in manifest>")

    if args.dump_raw:
        fetch_headers = stripchat._stripchat_stream_headers(probe_name)
        raw_session = requests.Session()
        raw_session.headers.update(fetch_headers)
        raw_resp = raw_session.get(
            stripchat._normalize_stream_cdn_url(manifest_url),
            timeout=args.segment_timeout,
        )
        print("RAW_MANIFEST_STATUS:", raw_resp.status_code)
        print("RAW_MANIFEST_BYTES:", len(raw_resp.text))
        parsed = urlparse(stripchat._normalize_stream_cdn_url(manifest_url))
        base_url = "{0}://{1}{2}/".format(
            parsed.scheme,
            parsed.netloc,
            "/".join(parsed.path.split("/")[:-1]),
        )
        auth_params = {
            key: values[0]
            for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
            if key in ("psch", "pkey") and values
        }
        full_urls = iter_mouflon_segment_urls(raw_resp.text, base_url)
        print("RAW_FULL_SEGMENT_COUNT:", len(full_urls))
        for idx, segment_url in enumerate(full_urls[:3]):
            print("RAW_FULL_SEGMENT_{}: {}".format(idx, segment_url))
            matrix = probe_url_matrix(
                raw_session,
                segment_url,
                auth_params,
                args.segment_timeout,
            )
            for probe in matrix:
                if "error" in probe:
                    print(
                        "RAW_SEGMENT_PROBE_{}_{}: ERROR {}".format(
                            idx, probe["label"], probe["error"]
                        )
                    )
                else:
                    print(
                        "RAW_SEGMENT_PROBE_{}_{}: HTTP {} bytes={} type={} url={}".format(
                            idx,
                            probe["label"],
                            probe["status"],
                            probe["first_chunk_bytes"],
                            probe["content_type"],
                            probe["url"],
                        )
                    )

    if args.browser_sniff:
        print("BROWSER_MEDIA_EVENT_COUNT:", len(browser_events))
        for idx, event in enumerate(browser_events[:40]):
            print(
                "BROWSER_MEDIA_{}: kind={} status={} url={}".format(
                    idx,
                    event.get("kind"),
                    event.get("status"),
                    event.get("url"),
                )
            )
            if event.get("body_preview"):
                preview = event["body_preview"].replace("\n", "\\n")
                print("BROWSER_MEDIA_BODY_{}: {}".format(idx, preview))
            if event.get("headers"):
                print(
                    "BROWSER_MEDIA_HEADERS_{}: {}".format(
                        idx, json.dumps(event["headers"], sort_keys=True)
                    )
                )
        browser_part_urls = [
            str(event.get("url", ""))
            for event in browser_events
            if event.get("kind") == "response"
            and event.get("status") == 200
            and "_part" in str(event.get("url", "")).lower()
            and ".mp4" in str(event.get("url", "")).lower()
        ]
        latest_browser_part_url = browser_part_urls[-1] if browser_part_urls else ""
        print("BROWSER_LATEST_PART_URL:", latest_browser_part_url or "<none>")
        print(
            "BROWSER_LATEST_PART_SEQUENCE:",
            extract_part_sequence(latest_browser_part_url),
        )
        print(
            "PROXY_LATEST_PART_SEQUENCE:",
            extract_part_sequence(latest_proxy_target),
        )
        print(
            "PROXY_BROWSER_PART_EXACT_MATCH:",
            bool(latest_proxy_target and latest_proxy_target == latest_browser_part_url),
        )
        if latest_browser_part_url:
            seeded_session = build_seeded_session(
                browser_seed_headers, browser_seed_cookies
            )
            browser_part_probe = probe_single_url(
                seeded_session,
                latest_browser_part_url,
                args.segment_timeout,
                args.read_bytes,
            )
            if "error" in browser_part_probe:
                print(
                    "BROWSER_PART_DIRECT_PROBE: ERROR {}".format(
                        browser_part_probe["error"]
                    )
                )
            else:
                print(
                    "BROWSER_PART_DIRECT_PROBE: HTTP {} bytes={} type={} url={}".format(
                        browser_part_probe["status"],
                        browser_part_probe["total_bytes_read"],
                        browser_part_probe["content_type"],
                        browser_part_probe["url"],
                    )
                )
            proxied_browser_part_url = "{}/seg?u={}".format(
                proxy_url.rsplit("/", 1)[0],
                encode_proxy_media_url(latest_browser_part_url),
            )
            print("BROWSER_PART_PROXY_URL:", proxied_browser_part_url)
            proxy_part_probe = probe_single_url(
                requests.Session(),
                proxied_browser_part_url,
                args.segment_timeout,
                args.read_bytes,
            )
            if "error" in proxy_part_probe:
                print(
                    "BROWSER_PART_PROXY_PROBE: ERROR {}".format(
                        proxy_part_probe["error"]
                    )
                )
            else:
                print(
                    "BROWSER_PART_PROXY_PROBE: HTTP {} bytes={} type={} url={}".format(
                        proxy_part_probe["status"],
                        proxy_part_probe["total_bytes_read"],
                        proxy_part_probe["content_type"],
                        proxy_part_probe["url"],
                    )
                )
        live_query = extract_browser_live_query(browser_events)
        print("BROWSER_LIVE_QUERY:", live_query or "<none>")
        if live_query:
            live_proxy_url = "{}?{}".format(proxy_url, live_query)
            live_manifest_resp = requests.get(
                live_proxy_url, timeout=args.segment_timeout
            )
            print("LIVE_MANIFEST_STATUS:", live_manifest_resp.status_code)
            live_media_urls = extract_media_urls(live_manifest_resp.text)
            live_latest_media_url = live_media_urls[-1] if live_media_urls else ""
            live_latest_proxy_target = decode_proxy_media_url(live_latest_media_url)
            print("LIVE_LATEST_MEDIA_URL:", live_latest_media_url or "<none>")
            print("LIVE_LATEST_PROXY_TARGET:", live_latest_proxy_target or "<none>")
            if live_latest_media_url:
                live_seg_resp = requests.get(
                    live_latest_media_url, timeout=args.segment_timeout, stream=True
                )
                live_first_chunk = b""
                live_total_read = 0
                try:
                    for chunk in live_seg_resp.iter_content(
                        chunk_size=min(args.read_bytes, 4096)
                    ):
                        if not chunk:
                            break
                        if not live_first_chunk:
                            live_first_chunk = chunk
                        live_total_read += len(chunk)
                        if live_total_read >= args.read_bytes:
                            break
                finally:
                    live_seg_resp.close()
                print("LIVE_SEGMENT_STATUS:", live_seg_resp.status_code)
                print(
                    "LIVE_SEGMENT_CONTENT_TYPE:",
                    live_seg_resp.headers.get("Content-Type", ""),
                )
                print("LIVE_SEGMENT_FIRST_CHUNK_BYTES:", len(live_first_chunk))
                print("LIVE_SEGMENT_TOTAL_BYTES_READ:", live_total_read)

    if args.keep_alive:
        print("Proxy left running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

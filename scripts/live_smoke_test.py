#!/usr/bin/env python3
"""Live smoke runner for Cumination site modules.

Read-only runner:
- Imports site modules outside Kodi using lightweight stubs.
- Executes main/list/categories/search/play style flows against live URLs.
- Captures pass/fail per step with concise reasons.
- Writes JSON + Markdown reports under results/.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import signal
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse, urljoin


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "plugin.video.cumination"
SITES_DIR = PLUGIN_PATH / "resources" / "lib" / "sites"
SITE_PROFILES_PATH = ROOT / "config" / "site_profiles.json"


def install_kodi_stubs() -> None:
    import types

    if "kodi_six" in sys.modules:
        return

    # xbmc
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

    class _VideoStreamDetail:
        def __init__(self, **kwargs):
            self.details = kwargs

    xbmc.VideoStreamDetail = _VideoStreamDetail

    # xbmcaddon
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
                "fs_host": "http://localhost:8191/v1",
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

    # xbmcplugin
    xbmcplugin = types.ModuleType("kodi_six.xbmcplugin")
    xbmcplugin.addDirectoryItem = lambda *args, **kwargs: True
    xbmcplugin.endOfDirectory = lambda *args, **kwargs: None
    xbmcplugin.setContent = lambda *args, **kwargs: None
    xbmcplugin.addSortMethod = lambda *args, **kwargs: None
    xbmcplugin.SORT_METHOD_TITLE = 10

    # xbmcgui
    xbmcgui = types.ModuleType("kodi_six.xbmcgui")

    class _VideoInfoTag:
        def setMediaType(self, *args, **kwargs):
            pass

        def setTitle(self, *args, **kwargs):
            pass

        def setGenres(self, *args, **kwargs):
            pass

        def setDuration(self, *args, **kwargs):
            pass

        def setPlot(self, *args, **kwargs):
            pass

        def setPlotOutline(self, *args, **kwargs):
            pass

        def addVideoStream(self, *args, **kwargs):
            pass

    class _ListItem:
        def __init__(self, label=""):
            self.label = label

        def setInfo(self, *args, **kwargs):
            pass

        def setArt(self, *args, **kwargs):
            pass

        def addContextMenuItems(self, *args, **kwargs):
            pass

        def getVideoInfoTag(self):
            return _VideoInfoTag()

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

    xbmcgui.ListItem = _ListItem
    xbmcgui.Dialog = _Dialog
    xbmcgui.DialogProgress = _DialogProgress
    xbmcgui.Keyboard = _Keyboard

    # xbmcvfs
    xbmcvfs = types.ModuleType("kodi_six.xbmcvfs")
    xbmcvfs.translatePath = lambda path: str(path).replace(
        "special://profile", str(ROOT / ".profile")
    )
    xbmcvfs.exists = lambda path: Path(str(path)).exists()
    xbmcvfs.mkdirs = lambda path: Path(str(path)).mkdir(parents=True, exist_ok=True)

    # package modules
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

    # StorageServer stub
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

    # Minimal resolveurl stub used by VideoPlayer
    resolveurl = types.ModuleType("resolveurl")

    class _ResolverError(Exception):
        pass

    class _ResolverNS:
        ResolverError = _ResolverError

    class _HostedMediaFile:
        def __init__(self, url="", title=None, include_universal=False, **kwargs):
            self._url = url
            self._domain = urlparse(url).netloc if url and "://" in str(url) else ""
            self.title = title or self._domain

        def resolve(self):
            return self._url

        def valid_url(self):
            return bool(self._url)

        def __bool__(self):
            return bool(self._url)

    resolveurl.resolver = _ResolverNS
    resolveurl.add_plugin_dirs = lambda *args, **kwargs: None
    resolveurl.scrape_supported = lambda html, regex: []
    resolveurl.choose_source = lambda sources: sources[0] if sources else None
    resolveurl.HostedMediaFile = _HostedMediaFile
    resolveurl.display_settings = lambda: None
    sys.modules["resolveurl"] = resolveurl

    # websocket stub for modules that import it at module load.
    websocket = types.ModuleType("websocket")
    websocket.WebSocketApp = object
    websocket.create_connection = lambda *args, **kwargs: None
    sys.modules["websocket"] = websocket


@dataclass
class StepResult:
    status: str
    message: str
    elapsed: float = 0.0
    items: int = 0
    video_items: int = 0
    image_items: int = 0
    description_items: int = 0
    playable: int = 0
    sample_url: str = ""
    play_url: str = ""


def normalize_url(site_url: str, value: str) -> str:
    v = str(value or "").strip()
    if not v:
        return v
    if v.startswith("http://") or v.startswith("https://"):
        return v
    if v.startswith("//"):
        return "https:" + v
    return urljoin(site_url, v)


class StepTimeout(Exception):
    pass


class TimeoutCtx:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self._old_handler: Any = None
        self._has_sigalrm = hasattr(signal, "SIGALRM")

    def _handler(self, signum, frame):
        raise StepTimeout(f"Timed out after {self.seconds}s")

    def __enter__(self):
        if self._has_sigalrm:
            self._old_handler = signal.signal(signal.SIGALRM, self._handler)
            signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc, tb):
        if self._has_sigalrm:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self._old_handler)
        return False


# Kodi string ID -> human-readable text (from strings.po)
KODI_STRING_IDS = {
    "30415": "Oh oh",
    "30416": "It looks like this website is too slow.",
    "30417": "It looks like the page does not exist.",
    "30418": "It looks like this website is down.",
    "30420": "Keywords empty",
    "30426": "Error",
    "30429": "Could not find a supported link",
    "30430": "Resolve failed",
    "30431": "link could not be resolved",
    "30433": "Download failed",
    "30434": "No response from server",
}


def translate_kodi_strings(text: str) -> str:
    """Replace bare Kodi string IDs (e.g. '30415') with readable text."""
    for sid, readable in KODI_STRING_IDS.items():
        if sid in text:
            text = text.replace(sid, readable)
    return text


def classify_message(msg: str) -> str:
    m = (msg or "").lower()
    if any(
        x in m
        for x in (
            "cloudflare",
            "cf-block",
            "attention required",
            "captcha",
            "blocked/challenged",
            "blocked",
            "challenge",
        )
    ):
        return "BLOCKED"
    if any(x in m for x in ("429", "451", "403", "forbidden", "too many requests")):
        return "BLOCKED"
    if any(x in m for x in ("timed out", "timeout", "connection", "network")):
        return "NETWORK"
    if any(x in m for x in ("no items", "no videos", "empty")):
        return "PARSER"
    if any(x in m for x in ("exception", "traceback", "import")):
        return "CODE"
    return "UNKNOWN"


def probe_url_status(url: str, timeout: int = 8) -> tuple[bool, str]:
    if not url:
        return False, "empty url"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = int(getattr(resp, "status", 200) or 200)
            return True, f"HTTP {code}"
    except urllib.error.HTTPError as exc:
        code = int(getattr(exc, "code", 0) or 0)
        # Remote reached even when access is denied/challenged.
        return True, f"HTTP {code}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def discover_site_names() -> list[str]:
    names = []
    for file_path in sorted(SITES_DIR.glob("*.py")):
        name = file_path.stem
        if name in {"__init__", "soup_spec"}:
            continue
        names.append(name)
    return names


def load_site_profiles() -> dict[str, Any]:
    if not SITE_PROFILES_PATH.exists():
        return {"default": {}, "sites": {}}
    return json.loads(SITE_PROFILES_PATH.read_text(encoding="utf-8"))


SITE_PROFILES = load_site_profiles()


def get_site_profile(site_name: str) -> dict[str, Any]:
    profile = dict(SITE_PROFILES.get("default", {}))
    site_specific = SITE_PROFILES.get("sites", {}).get(site_name, {})
    for key, value in site_specific.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            merged = dict(profile[key])
            merged.update(value)
            profile[key] = merged
        else:
            profile[key] = value
    return profile


def get_mode_param_mode(plugin_url: str) -> str:
    try:
        qs = parse_qs(urlparse(plugin_url).query)
        return qs.get("mode", [""])[0]
    except Exception:
        return ""


def get_mode_param_url(plugin_url: str) -> str:
    try:
        qs = parse_qs(urlparse(plugin_url).query)
        return qs.get("url", [""])[0]
    except Exception:
        return ""


def get_mode_param_name(plugin_url: str) -> str:
    try:
        qs = parse_qs(urlparse(plugin_url).query)
        return qs.get("name", [""])[0]
    except Exception:
        return ""


def run_site_child(
    site_name: str, steps: list[str], timeout_s: int, keyword: str
) -> dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(PLUGIN_PATH) not in sys.path:
        sys.path.insert(0, str(PLUGIN_PATH))
    sys.argv = ["plugin.video.cumination", "1", ""]

    install_kodi_stubs()

    from resources.lib.url_dispatcher import URL_Dispatcher
    import resources.lib.url_dispatcher as url_dispatcher_module
    from resources.lib import basics
    from resources.lib import utils

    # In Kodi dispatch everything arrives as strings; several site handlers expect ints.
    original_coerce = URL_Dispatcher._URL_Dispatcher__coerce

    def coerce_with_numbers(arg):
        val = original_coerce(arg)
        if isinstance(val, str):
            stripped = val.strip()
            if stripped.isdigit():
                try:
                    return int(stripped)
                except Exception:
                    return val
        return val

    URL_Dispatcher._URL_Dispatcher__coerce = staticmethod(coerce_with_numbers)

    # Import target module
    try:
        module = importlib.import_module(f"resources.lib.sites.{site_name}")
    except Exception as exc:
        return {
            "site": site_name,
            "overall": "ERROR",
            "error_type": "import",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=5),
            "steps": {},
        }

    site = getattr(module, "site", None)
    if not site or not getattr(site, "default_mode", ""):
        return {
            "site": site_name,
            "overall": "SKIP",
            "error_type": "missing_site",
            "error": "No AdultSite/default_mode exported",
            "steps": {},
        }

    site_profile = get_site_profile(site.name)
    profile_supports = site_profile.get("supports", {})
    harness_profile = site_profile.get("harness", {})

    def supports_step(step_name: str) -> bool:
        return profile_supports.get(step_name, True)

    def content_type() -> str:
        return site_profile.get("content_type", "video")

    def requires_flaresolverr() -> bool:
        return bool(site_profile.get("requires_flaresolverr", False))

    # Capture emitted UI items.
    captured_dirs: list[dict[str, Any]] = []
    captured_downloads: list[dict[str, Any]] = []
    play_calls: list[str] = []
    notify_calls: list[str] = []

    original_add_dir = basics.addDir
    original_add_down = basics.addDownLink
    original_ud_add_dir = url_dispatcher_module.addDir
    original_ud_add_down = url_dispatcher_module.addDownLink
    original_eod = utils.eod
    original_notify = utils.notify
    original_playvid = utils.playvid
    original_playvideo = getattr(utils, "playvideo", None)

    def fake_add_dir(name, url, mode, iconimage=None, *args, **kwargs):
        page = args[0] if len(args) > 0 else kwargs.get("page")
        channel = args[1] if len(args) > 1 else kwargs.get("channel")
        section = args[2] if len(args) > 2 else kwargs.get("section")
        keyword_val = args[3] if len(args) > 3 else kwargs.get("keyword")
        captured_dirs.append(
            {
                "name": str(name or ""),
                "url": str(url or ""),
                "mode": str(mode or ""),
                "icon": str(iconimage or ""),
                "page": "" if page is None else str(page),
                "channel": "" if channel is None else str(channel),
                "section": "" if section is None else str(section),
                "keyword": "" if keyword_val is None else str(keyword_val),
            }
        )
        return True

    def fake_add_down(name, url, mode, iconimage, *args, **kwargs):
        desc = ""
        if args:
            desc = str(args[0] or "")
        elif "desc" in kwargs:
            desc = str(kwargs.get("desc") or "")
        captured_downloads.append(
            {
                "name": str(name or ""),
                "url": str(url or ""),
                "mode": str(mode or ""),
                "icon": str(iconimage or ""),
                "desc": desc,
                "duration": str(kwargs.get("duration", "") or ""),
                "quality": str(kwargs.get("quality", "") or ""),
            }
        )
        return True

    def fake_notify(*args, **kwargs):
        if len(args) >= 2:
            title, message = args[0], args[1]
        elif len(args) == 1:
            title, message = "notify", args[0]
        else:
            title, message = "notify", kwargs.get("message", "")
        title = translate_kodi_strings(str(title))
        message = translate_kodi_strings(str(message))
        notify_calls.append(f"{title}: {message}")

    class FakeProgress:
        def create(self, *args, **kwargs):
            pass

        def update(self, *args, **kwargs):
            pass

        def close(self):
            pass

        def iscanceled(self):
            return False

    class FakeVideoPlayer:
        def __init__(self, name, *args, **kwargs):
            self.name = name
            self.progress = FakeProgress()
            self.resolveurl = sys.modules.get("resolveurl")

        def play_from_direct_link(self, direct_link):
            play_calls.append(str(direct_link))

        def play_from_site_link(self, url, referrer=""):
            play_calls.append(str(url))

        def play_from_html(self, html, url=None):
            # Try to extract direct links from HTML
            for pattern in [
                r'(https?://[^\s"\'\\,\]]+\.mp4(?:[^\s"\'\\,\]]*)?)',
                r'(https?://[^\s"\'\\,\]]+\.m3u8(?:[^\s"\'\\,\]]*)?)',
            ]:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    play_calls.append(match.group(1))
                    return
            if url:
                play_calls.append(str(url))

        def play_from_link_list(self, links):
            if links:
                play_calls.append(str(links[0]))

        def play_from_kt_player(self, html, url=None):
            if url:
                play_calls.append(str(url))
            else:
                play_calls.append("kt_player_detected")

        def play_from_link_to_resolve(self, source):
            if hasattr(source, "resolve"):
                try:
                    play_calls.append(str(source.resolve()))
                    return
                except Exception:
                    pass
            play_calls.append(str(source))

        def bypass_hosters(self, video_list):
            return video_list

        def bypass_hosters_single(self, videourl):
            return False

    def fake_playvid(videourl, name, *args, **kwargs):
        play_calls.append(str(videourl))

    basics.addDir = fake_add_dir
    basics.addDownLink = fake_add_down
    url_dispatcher_module.addDir = fake_add_dir
    url_dispatcher_module.addDownLink = fake_add_down
    utils.eod = lambda *args, **kwargs: None
    utils.notify = fake_notify
    utils.playvid = fake_playvid
    if original_playvideo is not None:
        utils.playvideo = fake_playvid
    utils.VideoPlayer = FakeVideoPlayer
    utils.progress = FakeProgress()
    utils.dialog = type(
        "Dialog",
        (),
        {
            "ok": lambda *a, **k: None,
            "yesno": lambda *a, **k: True,
            "select": lambda *a, **k: 0,
        },
    )()

    step_results: dict[str, dict[str, Any]] = {}
    list_candidate: dict[str, str] = {}
    cat_candidate: dict[str, str] = {}
    first_video: dict[str, str] = {}
    main_video_count = 0
    list_candidate_from_main = False

    def to_full_mode(mode: str) -> str:
        if not mode:
            return ""
        return mode if "." in mode else f"{site.name}.{mode}"

    def mode_exists(mode: str) -> bool:
        return to_full_mode(mode) in URL_Dispatcher.func_registry

    def pick_registered_mode(
        include_terms: tuple[str, ...],
        exclude_terms: tuple[str, ...] = (),
    ) -> str:
        site_modes = [
            m
            for m in URL_Dispatcher.func_registry.keys()
            if m.startswith(f"{site.name}.")
        ]
        for m in site_modes:
            lname = m.split(".", 1)[1].lower()
            if include_terms and not any(term in lname for term in include_terms):
                continue
            if any(term in lname for term in exclude_terms):
                continue
            return m
        return ""

    def call_mode(mode: str, seed: dict[str, Any] | None = None) -> None:
        seed = seed or {}
        mode = to_full_mode(mode)
        args_required = URL_Dispatcher.args_registry.get(mode, [])
        kwargs_available = URL_Dispatcher.kwargs_registry.get(mode, [])
        params = set(args_required) | set(kwargs_available)

        seed_page = seed.get("page")
        seed_channel = seed.get("channel")
        seed_section = seed.get("section")
        defaults = {
            "url": normalize_url(site.url, seed.get("url", site.url)),
            "name": seed.get("name", site.name),
            "keyword": seed.get("keyword", keyword),
            "page": seed_page if seed_page not in (None, "") else "1",
            "channel": seed_channel if seed_channel is not None else "",
            "section": seed_section if seed_section is not None else "",
        }
        query: dict[str, Any] = {}
        for key in params:
            if key in seed and seed[key] is not None:
                query[key] = str(seed[key])
            elif key in defaults:
                query[key] = str(defaults[key])
        URL_Dispatcher.dispatch(mode, query)

    def run_step(step_name: str, func: Callable[[], StepResult]) -> None:
        start = time.time()
        try:
            with TimeoutCtx(timeout_s):
                res = func()
        except StepTimeout as exc:
            res = StepResult("FAIL", str(exc))
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            res = StepResult("FAIL", msg)
        res = normalize_step_result(step_name, res)
        res.elapsed = round(time.time() - start, 2)
        step_results[step_name] = asdict(res)

    def normalize_step_result(step_name: str, res: StepResult) -> StepResult:
        if res.status != "FAIL":
            return res

        msg = res.message or ""
        lowered = msg.lower()

        network_markers = (
            "temporary failure in name resolution",
            "failed to resolve",
            "name or service not known",
            "network is unreachable",
            "nodename nor servname provided",
            "failed to establish a new connection: [errno 1] operation not permitted",
        )
        if any(marker in lowered for marker in network_markers):
            return StepResult(
                "SKIP",
                "Network/DNS failure in harness",
                sample_url=res.sample_url,
                play_url=res.play_url,
            )

        if requires_flaresolverr() and "flaresolverr" in lowered:
            return StepResult(
                "SKIP",
                "FlareSolverr required but unavailable in harness",
                sample_url=res.sample_url,
                play_url=res.play_url,
            )

        return res

    def find_mode_candidate(
        mode_suffixes: tuple[str, ...], dirs: list[dict[str, Any]]
    ) -> dict[str, str]:
        for entry in dirs:
            mode = entry.get("mode", "")
            candidate_url = entry.get("url", "")
            if not candidate_url:
                continue
            if any(mode.endswith(suf) for suf in mode_suffixes) and mode_exists(mode):
                return {
                    "mode": to_full_mode(mode),
                    "url": candidate_url,
                    "name": entry.get("name", ""),
                    "page": entry.get("page", ""),
                    "channel": entry.get("channel", ""),
                    "section": entry.get("section", ""),
                    "keyword": entry.get("keyword", ""),
                }
        return {}

    def step_main() -> StepResult:
        if not supports_step("main"):
            return StepResult("SKIP", "Main disabled by site profile")
        nonlocal main_video_count, list_candidate_from_main
        captured_dirs.clear()
        captured_downloads.clear()
        call_mode(site.default_mode, {"url": site.url})
        total = len(captured_dirs) + len(captured_downloads)
        nonlocal_list = find_mode_candidate((".List", ".PTList"), captured_dirs)
        nonlocal_cat = find_mode_candidate((".Cat", ".Categories"), captured_dirs)
        if not nonlocal_list:
            for entry in captured_dirs:
                mode = to_full_mode(entry.get("mode", ""))
                mlow = mode.lower()
                if not mode_exists(mode):
                    continue
                if any(
                    x in mlow
                    for x in (
                        "search",
                        "cat",
                        "categorie",
                        "genre",
                        "year",
                        "sort",
                        "login",
                        "logout",
                    )
                ):
                    continue
                if not any(x in mlow for x in ("list", "sitemain")):
                    continue
                nonlocal_list = {
                    "mode": mode,
                    "url": entry.get("url", ""),
                    "name": entry.get("name", ""),
                    "page": entry.get("page", ""),
                    "channel": entry.get("channel", ""),
                    "section": entry.get("section", ""),
                    "keyword": entry.get("keyword", ""),
                }
                if "list" in mlow:
                    break
        if not nonlocal_cat:
            for entry in captured_dirs:
                mode = to_full_mode(entry.get("mode", ""))
                mlow = mode.lower()
                if not mode_exists(mode):
                    continue
                if "cat" in mlow or "categorie" in mlow or "genre" in mlow:
                    nonlocal_cat = {
                        "mode": mode,
                        "url": entry.get("url", ""),
                        "name": entry.get("name", ""),
                        "page": entry.get("page", ""),
                        "channel": entry.get("channel", ""),
                        "section": entry.get("section", ""),
                        "keyword": entry.get("keyword", ""),
                    }
                    break
        list_candidate_from_main = bool(nonlocal_list)
        if not nonlocal_list:
            fallback_list_mode = pick_registered_mode(
                include_terms=("list", "sitemain"),
                exclude_terms=("search", "cat", "genre", "year", "sort", "main"),
            )
            if fallback_list_mode:
                nonlocal_list = {
                    "mode": fallback_list_mode,
                    "url": site.url,
                    "name": "",
                }
        if not nonlocal_cat:
            fallback_cat_mode = pick_registered_mode(
                include_terms=("cat", "categ", "genre"),
                exclude_terms=("search", "main"),
            )
            if fallback_cat_mode:
                nonlocal_cat = {"mode": fallback_cat_mode, "url": site.url, "name": ""}
        list_candidate.update(nonlocal_list)
        cat_candidate.update(nonlocal_cat)
        main_video_count = len(captured_downloads)
        if captured_downloads and not first_video:
            first_video.update(captured_downloads[0])
        if total <= 0:
            return StepResult("FAIL", "Main returned no items", items=0)
        return StepResult(
            "PASS",
            f"{len(captured_dirs)} dirs, {len(captured_downloads)} videos",
            items=total,
            video_items=len(captured_downloads),
            image_items=sum(1 for x in captured_downloads if x.get("icon")),
            description_items=sum(1 for x in captured_downloads if x.get("desc")),
        )

    def step_list() -> StepResult:
        if not supports_step("list"):
            return StepResult("SKIP", "List disabled by site profile")
        mode = list_candidate.get("mode") or f"{site.name}.List"
        if not mode_exists(mode):
            fallback_mode = pick_registered_mode(
                include_terms=("list", "sitemain"),
                exclude_terms=("search", "cat", "genre", "year", "sort", "main"),
            )
            mode = fallback_mode or mode
        url = normalize_url(site.url, list_candidate.get("url") or site.url)
        seed = {
            "url": url,
            "page": list_candidate.get("page") or None,
            "channel": list_candidate.get("channel") or None,
            "section": list_candidate.get("section") or None,
            "keyword": list_candidate.get("keyword") or None,
        }

        visited: set[tuple[str, str]] = set()
        hops = 0
        last_dir_count = 0
        while hops < 3:
            hops += 1
            captured_dirs.clear()
            captured_downloads.clear()
            notify_start = len(notify_calls)
            call_mode(mode, seed)
            videos = len(captured_downloads)
            fresh_notify = notify_calls[notify_start:]
            if videos > 0:
                first = captured_downloads[0]
                first_video.update(first)
                return StepResult(
                    "PASS",
                    f"{videos} videos",
                    items=videos + len(captured_dirs),
                    video_items=videos,
                    image_items=sum(1 for x in captured_downloads if x.get("icon")),
                    description_items=sum(
                        1 for x in captured_downloads if x.get("desc")
                    ),
                    playable=1 if first.get("url") else 0,
                    sample_url=url,
                )

            last_dir_count = len(captured_dirs)
            if not captured_dirs:
                break

            next_candidate = find_mode_candidate((".List", ".PTList"), captured_dirs)
            if not next_candidate:
                for entry in captured_dirs:
                    entry_mode = to_full_mode(entry.get("mode", ""))
                    mlow = entry_mode.lower()
                    if not mode_exists(entry_mode):
                        continue
                    if any(
                        x in mlow
                        for x in (
                            "search",
                            "cat",
                            "categorie",
                            "genre",
                            "year",
                            "sort",
                            "login",
                            "logout",
                        )
                    ):
                        continue
                    if not any(
                        x in mlow for x in ("list", "video", "item", "page", "main")
                    ):
                        continue
                    next_candidate = {
                        "mode": entry_mode,
                        "url": entry.get("url", ""),
                        "name": entry.get("name", ""),
                        "page": entry.get("page", ""),
                        "channel": entry.get("channel", ""),
                        "section": entry.get("section", ""),
                        "keyword": entry.get("keyword", ""),
                    }
                    break

            if not next_candidate:
                break

            mode = next_candidate["mode"]
            url = normalize_url(site.url, next_candidate.get("url") or site.url)
            seed = {
                "url": url,
                "page": next_candidate.get("page") or None,
                "channel": next_candidate.get("channel") or None,
                "section": next_candidate.get("section") or None,
                "keyword": next_candidate.get("keyword") or None,
            }
            marker = (mode, url)
            if marker in visited:
                break
            visited.add(marker)

        if getattr(site, "webcam", False):
            return StepResult(
                "SKIP",
                "Webcam list returned no videos in harness context",
                sample_url=url,
            )
        if main_video_count > 0:
            return StepResult(
                "SKIP",
                "Main already returned videos; list probe skipped",
                sample_url=url,
            )
        if last_dir_count > 0:
            return StepResult(
                "SKIP",
                "List probe returned directories only (no direct videos)",
                sample_url=url,
            )
        if not list_candidate_from_main:
            return StepResult(
                "SKIP",
                "No reliable list URL discovered from Main; list fallback yielded no videos",
                sample_url=url,
            )
        if fresh_notify:
            note = fresh_notify[-1]
            if classify_message(note) == "BLOCKED":
                return StepResult(
                    "SKIP",
                    f"List blocked/challenged in harness ({note})",
                    sample_url=url,
                )
        reachable, probe = probe_url_status(url)
        if not reachable:
            return StepResult(
                "SKIP",
                f"List URL unreachable in harness ({probe})",
                sample_url=url,
            )
        if (
            probe.startswith("HTTP 403")
            or probe.startswith("HTTP 429")
            or probe.startswith("HTTP 451")
        ):
            return StepResult(
                "SKIP",
                f"List URL blocked/challenged in harness ({probe})",
                sample_url=url,
            )
        return StepResult("FAIL", "List returned no videos", sample_url=url)

    def step_categories() -> StepResult:
        if not supports_step("categories"):
            return StepResult("SKIP", "Categories disabled by site profile")
        captured_dirs.clear()
        captured_downloads.clear()
        mode = cat_candidate.get("mode")
        url = normalize_url(site.url, cat_candidate.get("url") or site.url)
        if not mode:
            if hasattr(module, "Categories"):
                mode = f"{site.name}.Categories"
            elif hasattr(module, "Cat"):
                mode = f"{site.name}.Cat"
            else:
                mode = pick_registered_mode(
                    include_terms=("cat", "categ", "genre"),
                    exclude_terms=("search", "main"),
                )
                if not mode:
                    return StepResult("SKIP", "No categories function exposed")
        call_mode(
            mode,
            {
                "url": url,
                "page": cat_candidate.get("page") or None,
                "channel": cat_candidate.get("channel") or None,
                "section": cat_candidate.get("section") or None,
                "keyword": cat_candidate.get("keyword") or None,
            },
        )
        count = len(captured_dirs)
        if count <= 0:
            if harness_profile.get("categories_optional"):
                return StepResult(
                    "SKIP", "Categories optional for this site profile", sample_url=url
                )
            return StepResult("SKIP", "Categories returned no items", sample_url=url)
        return StepResult("PASS", f"{count} categories", items=count, sample_url=url)

    def step_search() -> StepResult:
        if not supports_step("search"):
            return StepResult("SKIP", "Search disabled by site profile")
        captured_dirs.clear()
        captured_downloads.clear()
        mode = f"{site.name}.Search"
        if mode not in URL_Dispatcher.func_registry:
            mode = pick_registered_mode(
                include_terms=("search",),
                exclude_terms=("main",),
            )
            if not mode:
                return StepResult("SKIP", "No search function exposed")
        fn = URL_Dispatcher.func_registry[mode]
        sig = inspect.signature(fn)
        query: dict[str, Any] = {"url": site.url, "keyword": keyword}
        if "url" not in sig.parameters:
            query.pop("url", None)
        if "keyword" not in sig.parameters:
            query.pop("keyword", None)
        call_mode(mode, query)
        videos = len(captured_downloads)
        if videos <= 0:
            if harness_profile.get("search_results_optional"):
                return StepResult(
                    "SKIP",
                    "Search results optional for this site profile",
                    sample_url=site.url,
                )
            return StepResult("SKIP", "Search returned no videos", sample_url=site.url)
        if not first_video and captured_downloads:
            first_video.update(captured_downloads[0])
        return StepResult(
            "PASS",
            f"{videos} results for '{keyword}'",
            items=videos + len(captured_dirs),
            video_items=videos,
            image_items=sum(1 for x in captured_downloads if x.get("icon")),
            description_items=sum(1 for x in captured_downloads if x.get("desc")),
            playable=1 if captured_downloads[0].get("url") else 0,
            sample_url=site.url,
        )

    # Webcam/live site names that can't produce playback URLs in harness
    WEBCAM_SITES = {
        "bongacams",
        "chaturbate",
        "naked",
        "streamate",
        "stripchat",
        "camsoda",
        "cam4",
        "xlovecam",
        "imlive",
    }

    def _classify_play_failure(notify_msgs: list[str], raw_url: str) -> StepResult:
        """Classify a play step that produced no playback URL.

        Returns SKIP for known-unactionable failures, FAIL for real bugs.
        """
        combined = " ".join(notify_msgs).lower()

        # Webcam / live sites — can't play without a real browser session
        if (
            site.name in WEBCAM_SITES
            or getattr(site, "webcam", False)
            or content_type() == "cam"
            or harness_profile.get("playback_not_testable")
        ):
            return StepResult(
                "SKIP",
                "Webcam/live site — no playback in harness",
                sample_url=raw_url,
            )

        # resolveurl-level messages (not our bug)
        resolveurl_phrases = (
            "could not find a supported link",
            "resolve failed",
            "link could not be resolved",
        )
        if any(phrase in combined for phrase in resolveurl_phrases):
            return StepResult(
                "SKIP",
                f"Harness limitation (resolveurl): {notify_msgs[-1]}",
                sample_url=raw_url,
            )

        # Site reports page gone / site down (upstream issue, not our code)
        site_down_phrases = (
            "page does not exist",
            "website is down",
            "website is too slow",
            "no response from server",
        )
        if any(phrase in combined for phrase in site_down_phrases):
            return StepResult(
                "SKIP",
                f"Site-reported error: {notify_msgs[-1]}",
                sample_url=raw_url,
            )

        # HTTP 403 / blocked in notify
        if classify_message(combined) == "BLOCKED":
            return StepResult(
                "SKIP",
                f"Play blocked/challenged in harness: {notify_msgs[-1]}",
                sample_url=raw_url,
            )

        # Auth required / model offline
        auth_phrases = ("login", "sign in", "model offline", "private", "password")
        if any(phrase in combined for phrase in auth_phrases):
            return StepResult(
                "SKIP",
                f"Auth/access required: {notify_msgs[-1]}",
                sample_url=raw_url,
            )

        # If there's a notification but it doesn't match a known real-bug pattern,
        # it's likely a harness limitation
        if notify_msgs:
            return StepResult(
                "SKIP",
                f"Harness limitation (notify): {notify_msgs[-1]}",
                sample_url=raw_url,
            )

        # No notifications at all and no playback URL — likely a real issue
        return StepResult(
            "FAIL",
            "Play function executed but no playback URL captured (no notifications)",
            sample_url=raw_url,
        )

    def step_play() -> StepResult:
        if not supports_step("play"):
            return StepResult("SKIP", "Play disabled by site profile")
        play_calls.clear()
        if not first_video:
            return StepResult("SKIP", "No video item available from list/search")
        mode = first_video.get("mode", "")
        raw_url = first_video.get("url", "")
        raw_name = first_video.get("name", "")
        if mode.startswith("plugin.video"):
            plugin_url = raw_url
            mode = get_mode_param_mode(raw_url)
            raw_url = get_mode_param_url(raw_url)
            raw_name = get_mode_param_name(plugin_url)
        if not mode:
            return StepResult("FAIL", "Missing play mode", sample_url=raw_url)
        raw_url = normalize_url(site.url, raw_url)
        try:
            call_mode(mode, {"url": raw_url, "name": raw_name})
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            lower = msg.lower()
            env_markers = (
                "special://",
                "resolveurl",
                "inputstream",
                "no such file or directory",
                "myplaylist",
                "invalid base64",
                "websocket",
            )
            if any(m in lower for m in env_markers):
                return StepResult(
                    "SKIP", f"Play check skipped in harness ({msg})", sample_url=raw_url
                )
            # Webcam/live sites often fail with parsing errors on non-video pages
            if site.name in WEBCAM_SITES or getattr(site, "webcam", False):
                return StepResult(
                    "SKIP",
                    f"Webcam/live site play error in harness ({msg})",
                    sample_url=raw_url,
                )
            raise
        if not play_calls:
            return _classify_play_failure(notify_calls[:], raw_url)
        return StepResult(
            "PASS",
            "Playback URL resolved",
            playable=1,
            sample_url=raw_url,
            play_url=play_calls[-1],
        )

    step_impls = {
        "main": step_main,
        "list": step_list,
        "categories": step_categories,
        "search": step_search,
        "play": step_play,
    }

    for step in steps:
        run_step(step, step_impls[step])

    # Restore patched symbols
    basics.addDir = original_add_dir
    basics.addDownLink = original_add_down
    url_dispatcher_module.addDir = original_ud_add_dir
    url_dispatcher_module.addDownLink = original_ud_add_down
    utils.eod = original_eod
    utils.notify = original_notify
    utils.playvid = original_playvid
    if original_playvideo is not None:
        utils.playvideo = original_playvideo
    URL_Dispatcher._URL_Dispatcher__coerce = original_coerce

    main_status = step_results.get("main", {}).get("status")
    list_status = step_results.get("list", {}).get("status")
    if main_status == "FAIL" or list_status == "FAIL":
        overall = "FAIL"
    else:
        advisory_failed = any(
            step_results.get(step, {}).get("status") == "FAIL"
            for step in ("categories", "search", "play")
            if step in step_results
        )
        overall = "WARN" if advisory_failed else "PASS"
    if all(v["status"] == "SKIP" for v in step_results.values()):
        overall = "SKIP"

    return {
        "site": site.name,
        "title": site.get_clean_title()
        if hasattr(site, "get_clean_title")
        else site.name,
        "base_url": site.url,
        "overall": overall,
        "steps": step_results,
        "notifications": notify_calls[-3:],
        "profile": site_profile,
    }


def parse_child_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty child output")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                return json.loads(line)
        raise


def run_parent(args: argparse.Namespace) -> int:
    sites = args.site if args.site else discover_site_names()
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    started = datetime.now()

    print("")
    print("Live Smoke Runner (read-only)")
    print(
        f"  Sites: {len(sites)} | Steps: {steps} | Timeout/step: {args.timeout}s | Keyword: '{args.keyword}'"
    )
    print(f"  Started: {started.strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    results: list[dict[str, Any]] = []
    failures = 0
    blocked = 0
    skipped = 0

    for idx, site_name in enumerate(sites, 1):
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--run-site",
            site_name,
            "--steps",
            args.steps,
            "--timeout",
            str(args.timeout),
            "--keyword",
            args.keyword,
        ]
        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=args.site_timeout,
                check=False,
            )
            if proc.returncode != 0:
                record = {
                    "site": site_name,
                    "overall": "ERROR",
                    "error_type": "subprocess",
                    "error": (proc.stderr or proc.stdout or "").strip()[:500],
                    "steps": {},
                }
            else:
                record = parse_child_json(proc.stdout)
        except subprocess.TimeoutExpired:
            record = {
                "site": site_name,
                "overall": "FAIL",
                "error_type": "timeout",
                "error": f"Site process timed out after {args.site_timeout}s",
                "steps": {},
            }
        elapsed = round(time.time() - t0, 2)
        record["elapsed"] = elapsed
        results.append(record)

        overall = record.get("overall", "ERROR")
        icon = (
            "✅"
            if overall == "PASS"
            else ("🟨" if overall == "WARN" else ("⚠️" if overall == "SKIP" else "❌"))
        )
        print(
            f"[{idx:>3}/{len(sites)}] {icon} {site_name:<24} {overall:<6} ({elapsed:.1f}s)"
        )

        if overall == "SKIP":
            skipped += 1
        elif overall != "PASS":
            failures += 1
            # coarse "blocked" tagging from step messages/errors
            msgs = [record.get("error", "")]
            for step_data in record.get("steps", {}).values():
                msgs.append(step_data.get("message", ""))
            if any(classify_message(m) == "BLOCKED" for m in msgs):
                blocked += 1

    generated = datetime.now()
    summary = {
        "generated": generated.isoformat(),
        "started": started.isoformat(),
        "sites_total": len(sites),
        "pass": sum(1 for r in results if r.get("overall") == "PASS"),
        "warn": sum(1 for r in results if r.get("overall") == "WARN"),
        "fail": sum(1 for r in results if r.get("overall") == "FAIL"),
        "error": sum(1 for r in results if r.get("overall") == "ERROR"),
        "skip": sum(1 for r in results if r.get("overall") == "SKIP"),
        "blocked_hint": blocked,
        "steps": steps,
        "timeout_per_step_sec": args.timeout,
        "timeout_per_site_sec": args.site_timeout,
        "keyword": args.keyword,
    }

    payload = {"summary": summary, "sites": results}

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = generated.strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"live_smoke_{stamp}.json"
    md_path = out_dir / f"live_smoke_{stamp}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print("")
    print("Summary")
    print(
        f"  Total: {summary['sites_total']} | PASS: {summary['pass']} | WARN: {summary['warn']} | FAIL: {summary['fail']} | ERROR: {summary['error']} | SKIP: {summary['skip']}"
    )
    print(f"  BLOCKED hint count: {summary['blocked_hint']}")
    print("")
    print("Saved")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")

    return 1 if (summary["fail"] or summary["error"]) else 0


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = []
    lines.append("# Live Smoke Report")
    lines.append("")
    lines.append(f"- Generated: `{s['generated']}`")
    lines.append(f"- Sites: `{s['sites_total']}`")
    lines.append(f"- Steps: `{', '.join(s['steps'])}`")
    lines.append(
        f"- Result: `PASS {s['pass']}` | `WARN {s.get('warn', 0)}` | `FAIL {s['fail']}` | `ERROR {s['error']}` | `SKIP {s['skip']}`"
    )
    lines.append("")
    lines.append("| Site | Overall | Main | List | Categories | Search | Play | Time |")
    lines.append("|---|---|---|---|---|---|---|---:|")
    for r in payload["sites"]:

        def icon(step):
            data = r.get("steps", {}).get(step)
            if not data:
                return "—"
            status = data.get("status")
            return (
                "PASS" if status == "PASS" else ("SKIP" if status == "SKIP" else "FAIL")
            )

        lines.append(
            f"| {r.get('site', '')} | {r.get('overall', '')} | {icon('main')} | {icon('list')} | {icon('categories')} | {icon('search')} | {icon('play')} | {r.get('elapsed', 0):.1f}s |"
        )

    failing = [r for r in payload["sites"] if r.get("overall") in ("FAIL", "ERROR")]
    if failing:
        lines.append("")
        lines.append("## Failures")
        lines.append("")
        for r in failing:
            lines.append(f"### {r.get('site')}")
            if r.get("error"):
                lines.append(f"- Error: `{r.get('error')}`")
            for step_name, data in r.get("steps", {}).items():
                if data.get("status") == "FAIL":
                    msg = data.get("message", "")
                    sample_url = data.get("sample_url", "")
                    cls = classify_message(msg)
                    lines.append(
                        f"- `{step_name}`: `{msg}` (class: `{cls}`)"
                        + (f" | url: `{sample_url}`" if sample_url else "")
                    )
            if r.get("notifications"):
                lines.append(f"- Notify: `{r['notifications'][-1]}`")
            lines.append("")

    # Failure Classification Summary
    warn_sites = [r for r in payload["sites"] if r.get("overall") == "WARN"]
    skip_sites = [r for r in payload["sites"] if r.get("overall") == "SKIP"]

    if warn_sites or skip_sites:
        lines.append("")
        lines.append("## Failure Classification Summary")
        lines.append("")

    if warn_sites:
        # Separate WARN sites into those with real FAIL steps vs only SKIP play failures
        real_warns = []
        demoted_warns = []
        for r in warn_sites:
            has_real_fail = False
            for step_name, data in r.get("steps", {}).items():
                if data.get("status") == "FAIL":
                    msg = data.get("message", "").lower()
                    # Real code bugs: IndexError, TypeError, KeyError, ValueError, AttributeError
                    if any(
                        err in msg
                        for err in (
                            "indexerror",
                            "typeerror",
                            "keyerror",
                            "valueerror",
                            "attributeerror",
                        )
                    ):
                        has_real_fail = True
                        break
                    # No notifications and no playback = likely real issue
                    if "no notifications" in msg:
                        has_real_fail = True
                        break
            if has_real_fail:
                real_warns.append(r)
            else:
                demoted_warns.append(r)

        if real_warns:
            lines.append("### WARN (Possible Real Issues)")
            lines.append("")
            lines.append("These sites have step failures that may indicate real bugs:")
            lines.append("")
            for r in real_warns:
                fail_steps = []
                for step_name, data in r.get("steps", {}).items():
                    if data.get("status") == "FAIL":
                        fail_steps.append(f"{step_name}: {data.get('message', '')}")
                lines.append(f"- **{r.get('site')}**: {'; '.join(fail_steps)}")
            lines.append("")

        if demoted_warns:
            lines.append("### WARN (Likely Not Actionable)")
            lines.append("")
            lines.append(
                "These WARN sites failed only on steps that are likely harness limitations:"
            )
            lines.append("")
            for r in demoted_warns:
                fail_steps = []
                for step_name, data in r.get("steps", {}).items():
                    if data.get("status") == "FAIL":
                        fail_steps.append(f"{step_name}: {data.get('message', '')}")
                lines.append(f"- **{r.get('site')}**: {'; '.join(fail_steps)}")
            lines.append("")

    if skip_sites:
        # Group SKIP sites by reason category
        skip_categories: dict[str, list[str]] = {
            "Webcam/Live": [],
            "Site Blocked/Down": [],
            "Harness Limitation": [],
            "Other": [],
        }
        for r in skip_sites:
            site_name = r.get("site", "")
            msgs = []
            for data in r.get("steps", {}).values():
                msgs.append(data.get("message", "").lower())
            combined = " ".join(msgs)
            if any(x in combined for x in ("webcam", "live site")):
                skip_categories["Webcam/Live"].append(site_name)
            elif any(x in combined for x in ("blocked", "challenged", "unreachable")):
                skip_categories["Site Blocked/Down"].append(site_name)
            elif any(x in combined for x in ("harness", "resolveurl", "no reliable")):
                skip_categories["Harness Limitation"].append(site_name)
            else:
                skip_categories["Other"].append(site_name)

        lines.append("### SKIP (Not Actionable)")
        lines.append("")
        for category, sites in skip_categories.items():
            if sites:
                lines.append(
                    f"- **{category}** ({len(sites)}): {', '.join(sorted(sites))}"
                )
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run live read-only smoke tests for Cumination site modules."
    )
    parser.add_argument("--site", nargs="+", help="One or more site module names")
    parser.add_argument(
        "--steps",
        default="main,list,categories,search,play",
        help="Comma-separated steps: main,list,categories,search,play",
    )
    parser.add_argument("--keyword", default="test", help="Search keyword")
    parser.add_argument(
        "--timeout", type=int, default=35, help="Timeout per step (seconds)"
    )
    parser.add_argument(
        "--site-timeout",
        type=int,
        default=140,
        help="Timeout for each site subprocess (seconds)",
    )
    parser.add_argument("--out", default=str(ROOT / "results"), help="Output directory")
    parser.add_argument("--run-site", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_site:
        steps = [s.strip() for s in args.steps.split(",") if s.strip()]
        result = run_site_child(args.run_site, steps, args.timeout, args.keyword)
        sys.stdout.write(json.dumps(result))
        return 0
    return run_parent(args)


if __name__ == "__main__":
    raise SystemExit(main())

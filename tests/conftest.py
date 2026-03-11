import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "plugin.video.cumination"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Ensure the plugin package is importable when running tests
if str(PLUGIN_PATH) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PATH))

KODI_ARGV = ["plugin.video.cumination", "1", ""]


def _ensure_kodi_stubs():
    """Install lightweight stubs for Kodi specific modules used by the addon."""
    if "kodi_six" in sys.modules:
        return

    # xbmc core module -----------------------------------------------------
    xbmc = types.ModuleType("kodi_six.xbmc")
    xbmc.LOGDEBUG = 0
    xbmc.LOGINFO = 1
    xbmc.LOGNOTICE = 2
    xbmc.LOGWARNING = 3
    xbmc.LOGERROR = 4

    def _noop(*args, **kwargs):
        return None

    xbmc.log = _noop
    xbmc.executebuiltin = _noop
    xbmc.getSkinDir = lambda: "skin.estuary"
    xbmc.getInfoLabel = lambda key: "19.0" if "BuildVersion" in key else ""
    xbmc.getCondVisibility = lambda *args, **kwargs: False

    class _VideoStreamDetail:
        def __init__(self, **kwargs):
            self.details = kwargs

    xbmc.VideoStreamDetail = _VideoStreamDetail

    # xbmcaddon module -----------------------------------------------------
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
                "pdsection": "0",
                "sortxt": "0",
                "sortbt": "0",
                "sortpd": "0",
                "paradisehill": "false",
                "hcaptcha": "false",
                "proxy_use": "false",
            }

        def getAddonInfo(self, key):
            if key == "path":
                return str(PLUGIN_PATH)
            if key == "profile":
                return str(ROOT / ".profile")
            if key == "version":
                return "19.9"
            return ""

        def getSetting(self, key):
            return self._settings.get(key, "")

        def getLocalizedString(self, string_id):
            return str(string_id)

        def setSetting(self, key, value):
            self._settings[key] = value

    xbmcaddon.Addon = _Addon

    # xbmcplugin module ----------------------------------------------------
    xbmcplugin = types.ModuleType("kodi_six.xbmcplugin")
    xbmcplugin.addDirectoryItem = lambda *args, **kwargs: True
    xbmcplugin.endOfDirectory = _noop
    xbmcplugin.setContent = _noop
    xbmcplugin.addSortMethod = _noop
    xbmcplugin.SORT_METHOD_TITLE = 10  # Add sort method constant

    # xbmcgui module -------------------------------------------------------
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

        def addContextMenuItems(self, items, replaceItems=False):
            pass

        def getVideoInfoTag(self):
            return _VideoInfoTag()

    class _Dialog:
        def notification(self, *args, **kwargs):
            pass

    class _DialogProgress:
        def create(self, *args, **kwargs):
            pass

        def update(self, *args, **kwargs):
            pass

        def close(self):
            pass

        def iscanceled(self):
            return False

    xbmcgui.ListItem = _ListItem
    xbmcgui.Dialog = _Dialog
    xbmcgui.DialogProgress = _DialogProgress

    # xbmcvfs module -------------------------------------------------------
    xbmcvfs = types.ModuleType("kodi_six.xbmcvfs")

    def _translate_path(path):
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = ROOT / path
        return str(path_obj)

    xbmcvfs.translatePath = _translate_path
    xbmcvfs.exists = lambda path: Path(path).exists()
    xbmcvfs.mkdirs = lambda path: Path(path).mkdir(parents=True, exist_ok=True)

    # Assemble kodi_six package --------------------------------------------
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

    # Provide top-level aliases that some modules may import directly.
    sys.modules.setdefault("xbmc", xbmc)
    sys.modules.setdefault("xbmcaddon", xbmcaddon)
    sys.modules.setdefault("xbmcplugin", xbmcplugin)
    sys.modules.setdefault("xbmcgui", xbmcgui)
    sys.modules.setdefault("xbmcvfs", xbmcvfs)

    # StorageServer stub ---------------------------------------------------
    storage_module = types.ModuleType("StorageServer")

    class _StorageServer:
        def __init__(self, *args, **kwargs):
            self.table_name = args[0] if args else "default"

        def cacheDelete(self, *args, **kwargs):
            pass

        def cacheFunction(self, *args, **kwargs):
            if args and callable(args[0]):
                return args[0](*args[1:])
            return None

        def get(self, *args, **kwargs):
            return None

        def set(self, *args, **kwargs):
            pass

    storage_module.StorageServer = _StorageServer
    sys.modules["StorageServer"] = storage_module

    # Requests stub --------------------------------------------------------
    requests_module = types.ModuleType("requests")

    class _Response:
        def __init__(self, url):
            self.url = url
            self.status_code = 200
            self.text = ""
            self.content = b""
            self.headers = {}

        def json(self):
            return {}

    def _head(url, allow_redirects=True):
        return _Response(url)

    def _get(url, **kwargs):
        return _Response(url)

    def _post(url, **kwargs):
        return _Response(url)

    class _Session:
        def __init__(self):
            self.headers = {}
            self.cookies = {}

        def get(self, url, **kwargs):
            return _Response(url)

        def post(self, url, **kwargs):
            return _Response(url)

    requests_module.head = _head
    requests_module.get = _get
    requests_module.post = _post
    requests_module.Session = _Session
    sys.modules["requests"] = requests_module

    # websocket stub -------------------------------------------------------
    websocket_module = types.ModuleType("websocket")
    websocket_module.create_connection = lambda *a, **k: None
    sys.modules["websocket"] = websocket_module

    # inputstreamhelper stub -----------------------------------------------
    inputstream_module = types.ModuleType("inputstreamhelper")

    class _Helper:
        def __init__(self, *args, **kwargs):
            pass

        def check_inputstream(self):
            return True

    inputstream_module.Helper = _Helper
    sys.modules["inputstreamhelper"] = inputstream_module

    # playwright_helper stub -----------------------------------------------
    def _playwright_disabled(*args, **kwargs):
        raise ImportError("Playwright disabled during tests")

    playwright_helper = types.ModuleType("resources.lib.playwright_helper")
    playwright_helper.fetch_with_playwright = _playwright_disabled
    playwright_helper.sniff_video_url = _playwright_disabled
    sys.modules["resources.lib.playwright_helper"] = playwright_helper


_ensure_kodi_stubs()


def read_fixture(filename):
    """Return the contents of a fixture file from tests/fixtures."""

    return (ROOT / "tests" / "fixtures" / filename).read_text(encoding="utf-8")


@pytest.fixture(name="read_fixture")
def _read_fixture_fixture():
    """Provide ``read_fixture`` helper as a pytest fixture."""

    return read_fixture


@pytest.fixture(autouse=True)
def _set_kodi_argv(monkeypatch):
    """Provide minimal argv expected by the addon without clobbering pytest options.

    Kodi plugins expect ``sys.argv`` to contain ``[plugin_id, handle, params]``.
    Pytest consumes its CLI arguments before fixtures run, so we can safely
    replace ``sys.argv`` here to satisfy addon expectations in every test.
    """
    monkeypatch.setattr(sys, "argv", KODI_ARGV.copy())


def _block_network_access(*args, **kwargs):
    """Prevent live HTTP requests during tests.

    All site fetches should be routed through fixture helpers such as
    :func:`fixture_mapped_get_html`. If this assertion is raised, add a
    corresponding fixture mapping in your test instead of performing network
    I/O.
    """
    raise AssertionError("Network access attempted during tests")


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


def pytest_configure(config):
    """Install global network guards for test sessions."""
    import urllib.request

    # Set sys.argv before any addon imports to prevent initialization errors
    sys.argv = KODI_ARGV.copy()

    # Prevent accidental outbound calls by ensuring the urllib opener raises.
    urllib.request.urlopen = _block_network_access


def pytest_runtest_setup(item):
    """Ensure resources.lib.utils does not attempt live HTTP requests."""
    try:
        import resources.lib.utils as _utils

        _utils.urlopen = _block_network_access
    except (ImportError, AttributeError):
        # Some unit tests import utils late; allow them to patch manually.
        pass


def fixture_mapped_get_html(monkeypatch, module, url_map):
    """Patch ``module.utils.getHtml`` to return local fixtures.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        module: The site module whose ``utils`` dependency is patched.
        url_map (dict): Mapping of URL substrings to fixture paths under
            ``tests/fixtures``.
    """

    def _fake_get_html(url, *args, **kwargs):
        for key, fixture_name in url_map.items():
            if key in url:
                return read_fixture(fixture_name)
        raise AssertionError(f"No fixture mapped for URL: {url}")

    monkeypatch.setattr(module.utils, "getHtml", _fake_get_html)
    if hasattr(module.utils, "_getHtml"):
        monkeypatch.setattr(module.utils, "_getHtml", _fake_get_html)
    return _fake_get_html

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "plugin.video.cumination"

# Ensure the plugin package is importable when running tests
if str(PLUGIN_PATH) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PATH))

# Kodi-style scripts rely on positional argv entries provided by Kodi.
if len(sys.argv) < 3:
    sys.argv = ['plugin.video.cumination', '1', '']


def _ensure_kodi_stubs():
    """Install lightweight stubs for Kodi specific modules used by the addon."""
    if 'kodi_six' in sys.modules:
        return

    # xbmc core module -----------------------------------------------------
    xbmc = types.ModuleType('kodi_six.xbmc')
    xbmc.LOGDEBUG = 0
    xbmc.LOGINFO = 1
    xbmc.LOGNOTICE = 2
    xbmc.LOGWARNING = 3
    xbmc.LOGERROR = 4

    def _noop(*args, **kwargs):
        return None

    xbmc.log = _noop
    xbmc.executebuiltin = _noop
    xbmc.getSkinDir = lambda: 'skin.estuary'

    class _VideoStreamDetail:
        def __init__(self, **kwargs):
            self.details = kwargs

    xbmc.VideoStreamDetail = _VideoStreamDetail

    # xbmcaddon module -----------------------------------------------------
    xbmcaddon = types.ModuleType('kodi_six.xbmcaddon')

    class _Addon:
        def __init__(self, addon_id=None):
            self.addon_id = addon_id or 'plugin.video.cumination'
            self._settings = {
                'cache_time': '0',
                'custom_favorites': 'false',
                'favorites_path': '',
                'customview': 'false',
                'setview': '',
                'duration_in_name': 'false',
                'quality_in_name': 'false',
            }

        def getAddonInfo(self, key):
            if key == 'path':
                return str(PLUGIN_PATH)
            if key == 'profile':
                return str(ROOT / '.profile')
            if key == 'version':
                return '19.9'
            return ''

        def getSetting(self, key):
            return self._settings.get(key, '')

        def getLocalizedString(self, string_id):
            return string_id

        def setSetting(self, key, value):
            self._settings[key] = value

    xbmcaddon.Addon = _Addon

    # xbmcplugin module ----------------------------------------------------
    xbmcplugin = types.ModuleType('kodi_six.xbmcplugin')
    xbmcplugin.addDirectoryItem = lambda *args, **kwargs: True
    xbmcplugin.endOfDirectory = _noop
    xbmcplugin.setContent = _noop
    xbmcplugin.addSortMethod = _noop

    # xbmcgui module -------------------------------------------------------
    xbmcgui = types.ModuleType('kodi_six.xbmcgui')

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
        def __init__(self, label=''):
            self.label = label

        def setInfo(self, *args, **kwargs):
            pass

        def setArt(self, *args, **kwargs):
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

    xbmcgui.ListItem = _ListItem
    xbmcgui.Dialog = _Dialog
    xbmcgui.DialogProgress = _DialogProgress

    # xbmcvfs module -------------------------------------------------------
    xbmcvfs = types.ModuleType('kodi_six.xbmcvfs')

    def _translate_path(path):
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = ROOT / path
        return str(path_obj)

    xbmcvfs.translatePath = _translate_path
    xbmcvfs.exists = lambda path: Path(path).exists()
    xbmcvfs.mkdirs = lambda path: Path(path).mkdir(parents=True, exist_ok=True)

    # Assemble kodi_six package --------------------------------------------
    kodi_six = types.ModuleType('kodi_six')
    kodi_six.xbmc = xbmc
    kodi_six.xbmcaddon = xbmcaddon
    kodi_six.xbmcplugin = xbmcplugin
    kodi_six.xbmcgui = xbmcgui
    kodi_six.xbmcvfs = xbmcvfs

    sys.modules['kodi_six'] = kodi_six
    sys.modules['kodi_six.xbmc'] = xbmc
    sys.modules['kodi_six.xbmcaddon'] = xbmcaddon
    sys.modules['kodi_six.xbmcplugin'] = xbmcplugin
    sys.modules['kodi_six.xbmcgui'] = xbmcgui
    sys.modules['kodi_six.xbmcvfs'] = xbmcvfs

    # Provide top-level aliases that some modules may import directly.
    sys.modules.setdefault('xbmc', xbmc)
    sys.modules.setdefault('xbmcaddon', xbmcaddon)
    sys.modules.setdefault('xbmcplugin', xbmcplugin)
    sys.modules.setdefault('xbmcgui', xbmcgui)
    sys.modules.setdefault('xbmcvfs', xbmcvfs)

    # StorageServer stub ---------------------------------------------------
    storage_module = types.ModuleType('StorageServer')

    class _StorageServer:
        def __init__(self, *args, **kwargs):
            self.table_name = args[0] if args else 'default'

        def cacheDelete(self, *args, **kwargs):
            pass

    storage_module.StorageServer = _StorageServer
    sys.modules['StorageServer'] = storage_module


_ensure_kodi_stubs()


def read_fixture(filename):
    """Return the contents of a fixture file from tests/fixtures."""
    return (ROOT / 'tests' / 'fixtures' / filename).read_text(encoding='utf-8')

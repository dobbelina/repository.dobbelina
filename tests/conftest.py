import sys
import types
import urllib.parse
import urllib.error
import urllib.request
import html.parser
import http.cookiejar
from pathlib import Path


def pytest_configure(config):
    """Configure stub Kodi modules for unit tests."""

    # Avoid re-initializing when running multiple test sessions
    if 'xbmc' in sys.modules:
        return

    repo_root = Path(__file__).resolve().parents[1]
    addon_root = repo_root / 'plugin.video.cumination'
    profile_root = repo_root / '.kodi_profile'
    profile_root.mkdir(exist_ok=True)

    fake_xbmc = types.ModuleType('xbmc')
    fake_xbmc.LOGERROR = 0
    fake_xbmc.LOGWARNING = 1
    fake_xbmc.LOGINFO = 2
    fake_xbmc.LOGNOTICE = 2
    fake_xbmc.LOGDEBUG = 3
    fake_xbmc.LOGFATAL = 4
    fake_xbmc.LOGSEVERE = 5
    fake_xbmc.executebuiltin = lambda *args, **kwargs: None
    fake_xbmc.getSkinDir = lambda: 'estuary'
    fake_xbmc.log = lambda *args, **kwargs: None

    class _VideoStreamDetail:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_xbmc.VideoStreamDetail = _VideoStreamDetail

    fake_xbmcplugin = types.ModuleType('xbmcplugin')
    fake_xbmcplugin.addDirectoryItem = lambda *args, **kwargs: True
    fake_xbmcplugin.endOfDirectory = lambda *args, **kwargs: True
    fake_xbmcplugin.addSortMethod = lambda *args, **kwargs: None

    fake_xbmcaddon = types.ModuleType('xbmcaddon')

    class _FakeAddon:
        def __init__(self, addon_id=None):
            self.addon_id = addon_id or 'plugin.video.cumination'

        def getAddonInfo(self, key):
            if key == 'path':
                return str(addon_root)
            if key == 'profile':
                return str(profile_root)
            if key == 'version':
                return '20.0.0'
            return ''

        def getLocalizedString(self, _):
            return ''

        def getSetting(self, key):
            defaults = {
                'cache_time': '0',
                'custom_favorites': 'false',
                'favorites_path': '',
                'duration_in_name': 'false',
                'quality_in_name': 'false',
                'posterfanart': 'false',
                'customview': 'false',
                'setview': '',
                'favorder': 'date added',
                'filter_listing': '',
            }
            return defaults.get(key, '')

        def setSetting(self, key, value):
            pass

    fake_xbmcaddon.Addon = _FakeAddon

    fake_xbmcvfs = types.ModuleType('xbmcvfs')
    fake_xbmcvfs.translatePath = lambda path: str(Path(path))
    fake_xbmcvfs.exists = lambda path: Path(path).exists()

    fake_xbmcgui = types.ModuleType('xbmcgui')

    class _FakeDialogProgress:
        def create(self, *args, **kwargs):
            pass

        def update(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class _FakeDialog:
        def notification(self, *args, **kwargs):
            pass

    class _FakeListItem:
        def __init__(self, *args, **kwargs):
            self.props = {}

        def setInfo(self, *args, **kwargs):
            pass

        def addStreamInfo(self, *args, **kwargs):
            pass

        def setArt(self, *args, **kwargs):
            pass

        def setProperty(self, *args, **kwargs):
            pass

        def getVideoInfoTag(self):
            class _Tag:
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

            return _Tag()

    fake_xbmcgui.DialogProgress = _FakeDialogProgress
    fake_xbmcgui.Dialog = _FakeDialog
    fake_xbmcgui.ListItem = _FakeListItem

    fake_storage = types.ModuleType('StorageServer')

    class _StorageServer:
        def __init__(self, *args, **kwargs):
            self.table_name = ''

        def cacheDelete(self, *args, **kwargs):
            pass

    fake_storage.StorageServer = _StorageServer

    fake_kodi_six = types.ModuleType('kodi_six')
    fake_kodi_six.xbmc = fake_xbmc
    fake_kodi_six.xbmcaddon = fake_xbmcaddon
    fake_kodi_six.xbmcgui = fake_xbmcgui
    fake_kodi_six.xbmcplugin = fake_xbmcplugin
    fake_kodi_six.xbmcvfs = fake_xbmcvfs

    fake_six = types.ModuleType('six')
    fake_six.PY3 = True
    fake_six.PY2 = False
    fake_six.string_types = (str,)
    fake_six.text_type = str
    fake_six.binary_type = bytes
    fake_six_moves = types.ModuleType('six.moves')
    fake_six_moves.urllib_parse = urllib.parse
    fake_six_moves.urllib_error = urllib.error
    fake_six_moves.urllib_request = urllib.request
    fake_six_moves.html_parser = html.parser
    fake_six_moves.http_cookiejar = http.cookiejar
    fake_six.moves = fake_six_moves

    sys.modules['xbmc'] = fake_xbmc
    sys.modules['xbmcplugin'] = fake_xbmcplugin
    sys.modules['xbmcaddon'] = fake_xbmcaddon
    sys.modules['xbmcgui'] = fake_xbmcgui
    sys.modules['xbmcvfs'] = fake_xbmcvfs
    sys.modules['StorageServer'] = fake_storage
    sys.modules['kodi_six'] = fake_kodi_six
    sys.modules['six'] = fake_six
    sys.modules['six.moves'] = fake_six_moves

    sys.argv = ['plugin://plugin.video.cumination', '1', '', '']

import html.parser
import http.cookiejar
import io
import os
import sys
import types
import unittest
import urllib.error
import urllib.parse
import urllib.request

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - environment without BeautifulSoup
    BeautifulSoup = None


def _install_test_stubs():
    """Install lightweight Kodi and addon stubs so utils can import."""

    plugin_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'plugin.video.cumination'))
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)

    if 'kodi_six' not in sys.modules:
        kodi_six = types.ModuleType('kodi_six')

        class XBMCStub:
            LOGDEBUG = 0
            LOGINFO = 1
            LOGNOTICE = 2
            LOGWARNING = 3
            LOGERROR = 4

            def log(self, *args, **kwargs):
                return None

            def executebuiltin(self, *args, **kwargs):
                return None

            def getSkinDir(self):
                return 'estuary'

            def translatePath(self, path):
                return path

        xbmc_module = XBMCStub()

        xbmcgui_module = types.ModuleType('xbmcgui')

        class _DialogProgress:
            def __init__(self, *args, **kwargs):
                pass

            def create(self, *args, **kwargs):
                pass

            def update(self, *args, **kwargs):
                pass

            def close(self):
                pass

        class _Dialog:
            def notification(self, *args, **kwargs):
                pass

        class _ListItem:
            def __init__(self, *args, **kwargs):
                pass

            def setInfo(self, *args, **kwargs):
                pass

            def setArt(self, *args, **kwargs):
                pass

        xbmcgui_module.DialogProgress = _DialogProgress
        xbmcgui_module.Dialog = _Dialog
        xbmcgui_module.ListItem = _ListItem

        xbmcplugin_module = types.ModuleType('xbmcplugin')
        xbmcplugin_module.addDirectoryItem = lambda *args, **kwargs: None
        xbmcplugin_module.endOfDirectory = lambda *args, **kwargs: None

        xbmcvfs_module = types.ModuleType('xbmcvfs')
        xbmcvfs_module.translatePath = lambda path: path

        class _DummyAddon:
            _settings = {
                'cache_time': '0',
                'custom_favorites': 'false',
                'favorites_path': '',
                'duration_in_name': 'false',
                'filter_listing': '',
                'current_ua': '',
                'last_ua_create': '0'
            }

            def __init__(self, addon_id=None):
                self.addon_id = addon_id

            def getAddonInfo(self, key):
                info = {
                    'version': '20.0',
                    'profile': 'profile',
                    'path': '.'
                }
                return info.get(key, '')

            def getSetting(self, key):
                return self._settings.get(key, '')

            def setSetting(self, key, value):
                self._settings[key] = value

        xbmcaddon_module = types.ModuleType('xbmcaddon')
        _addon_instances = {}

        def _addon_factory(addon_id=None):
            key = addon_id or '__default__'
            if key not in _addon_instances:
                _addon_instances[key] = _DummyAddon(addon_id)
            return _addon_instances[key]

        xbmcaddon_module.Addon = _addon_factory

        kodi_six.xbmc = xbmc_module
        kodi_six.xbmcgui = xbmcgui_module
        kodi_six.xbmcplugin = xbmcplugin_module
        kodi_six.xbmcvfs = xbmcvfs_module
        kodi_six.xbmcaddon = xbmcaddon_module

        sys.modules['kodi_six'] = kodi_six
        sys.modules.setdefault('xbmc', xbmc_module)
        sys.modules.setdefault('xbmcgui', xbmcgui_module)
        sys.modules.setdefault('xbmcplugin', xbmcplugin_module)
        sys.modules.setdefault('xbmcvfs', xbmcvfs_module)
        sys.modules.setdefault('xbmcaddon', xbmcaddon_module)

    if 'StorageServer' not in sys.modules:
        storage_module = types.ModuleType('StorageServer')

        class _DummyStorage:
            def __init__(self, *args, **kwargs):
                self.table_name = ''

            def cacheDelete(self, *args, **kwargs):
                pass

            def cacheFunction(self, func, *args, **kwargs):
                return func(*args, **kwargs)

        storage_module.StorageServer = _DummyStorage
        sys.modules['StorageServer'] = storage_module

    if 'six' not in sys.modules:
        six_module = types.ModuleType('six')

        six_module.PY2 = False
        six_module.PY3 = True
        six_module.string_types = (str,)
        six_module.integer_types = (int,)
        six_module.class_types = (type,)
        six_module.binary_type = bytes
        six_module.text_type = str
        six_module.print_ = print
        six_module.unichr = chr
        six_module.BytesIO = io.BytesIO
        six_module.iteritems = lambda mapping: iter(mapping.items())
        six_module.viewitems = lambda mapping: mapping.items()

        def _ensure_str(value, encoding='utf-8', errors='strict'):
            if isinstance(value, str):
                return value
            if isinstance(value, bytes):
                return value.decode(encoding, errors)
            return str(value)

        def _ensure_binary(value, encoding='utf-8', errors='strict'):
            if isinstance(value, bytes):
                return value
            if isinstance(value, str):
                return value.encode(encoding, errors)
            return bytes(str(value), encoding)

        six_module.ensure_str = _ensure_str
        six_module.ensure_text = _ensure_str
        six_module.ensure_binary = _ensure_binary
        six_module.b = lambda s: s.encode('latin-1') if isinstance(s, str) else bytes(s)

        moves_module = types.ModuleType('six.moves')
        moves_module.html_parser = html.parser
        moves_module.http_cookiejar = http.cookiejar
        moves_module.urllib_error = urllib.error
        moves_module.urllib_parse = urllib.parse
        moves_module.urllib_request = urllib.request

        six_module.moves = moves_module

        sys.modules['six'] = six_module
        sys.modules['six.moves'] = moves_module

    if 'resources.lib.basics' not in sys.modules:
        basics_module = types.ModuleType('resources.lib.basics')
        addon_stub = sys.modules['kodi_six'].xbmcaddon.Addon()
        basics_module.addDir = lambda *args, **kwargs: None
        basics_module.addDownLink = lambda *args, **kwargs: None
        basics_module.addImgLink = lambda *args, **kwargs: None
        basics_module.addon = addon_stub
        basics_module.addon_handle = 0
        basics_module.addon_sys = ''
        basics_module.rootDir = plugin_root
        basics_module.resDir = os.path.join(plugin_root, 'resources')
        basics_module.cookiePath = 'cookies.lwp'
        basics_module.cum_image = lambda value, custom=False: value
        basics_module.cuminationicon = ''
        basics_module.eod = lambda *args, **kwargs: None
        basics_module.favoritesdb = ''
        basics_module.keys = {}
        basics_module.searchDir = lambda *args, **kwargs: None
        basics_module.profileDir = ''
        sys.modules['resources.lib.basics'] = basics_module


_install_test_stubs()

from resources.lib import utils  # noqa: E402


class DummySite:
    def __init__(self, base_url='https://example.com/'):
        self.url = base_url
        self.downloads = []
        self.dirs = []
        self.img_next = 'next.png'

    def add_download_link(self, name, url, mode, iconimage, desc='', stream=None,
                          fav='add', noDownload=False, contextm=None, fanart=None,
                          duration='', quality=''):
        self.downloads.append({
            'name': name,
            'url': url,
            'mode': mode,
            'thumbnail': iconimage,
            'desc': desc,
            'contextm': contextm,
            'fanart': fanart,
            'duration': duration,
            'quality': quality
        })

    def add_dir(self, label, url, mode, iconimage=None, *args, **kwargs):
        self.dirs.append({
            'label': label,
            'url': url,
            'mode': mode,
            'icon': iconimage
        })


@unittest.skipUnless(BeautifulSoup, "BeautifulSoup4 is required for these tests")
class SoupVideosListTests(unittest.TestCase):
    def test_basic_video_listing_with_pagination(self):
        html = """
        <div>
            <a class="video" href="/videos/1">
                <img src="/thumbs/1.jpg" alt=" First Video \n" />
                <span class="duration">10:00</span>
            </a>
            <a class="video" href="videos/2">
                <img data-src="/thumbs/2.jpg" />
                <span>Second Video Title</span>
            </a>
        </div>
        <nav>
            <a rel="next" href="/page/2">More results</a>
        </nav>
        """
        soup = BeautifulSoup(html, 'html.parser')

        selectors = {
            'items': 'a.video',
            'url': {'attr': 'href'},
            'title': {
                'selector': 'img',
                'attr': 'alt',
                'text': True,
                'clean': True,
                'fallback_selectors': [None]
            },
            'thumbnail': {'selector': 'img', 'attr': 'src', 'fallback_attrs': ['data-src']},
            'duration': {'selector': '.duration', 'text': True},
            'pagination': {
                'selector': {'query': 'a[rel="next"]', 'scope': 'soup'},
                'attr': 'href',
                'label': 'More results',
                'mode': 'List'
            }
        }

        site = DummySite()
        result = utils.soup_videos_list(site, soup, selectors, play_mode='play', contextm=['ctx'])

        self.assertEqual(result['items'], 2)
        self.assertEqual(len(site.downloads), 2)

        first = site.downloads[0]
        self.assertEqual(first['url'], 'https://example.com/videos/1')
        self.assertEqual(first['thumbnail'], 'https://example.com/thumbs/1.jpg')
        self.assertEqual(first['duration'], '10:00')
        self.assertEqual(first['contextm'], ['ctx'])

        second = site.downloads[1]
        self.assertEqual(second['name'], 'Second Video Title')
        self.assertEqual(second['thumbnail'], 'https://example.com/thumbs/2.jpg')
        self.assertEqual(second['duration'], '')

        self.assertEqual(result['next_url'], 'https://example.com/page/2')
        self.assertTrue(result['pagination_added'])
        self.assertEqual(site.dirs[0]['label'], 'More results')
        self.assertEqual(site.dirs[0]['url'], 'https://example.com/page/2')

    def test_handles_missing_thumbnail_and_duration(self):
        html = """
        <section>
            <article>
                <a href="/watch/3"><span class="title">Third Clip</span></a>
            </article>
        </section>
        <footer>
            <a class="pager" href="/page/3">Next page</a>
        </footer>
        """
        soup = BeautifulSoup(html, 'html.parser')

        selectors = {
            'items': lambda s: s.find_all('article'),
            'url': {'selector': 'a', 'attr': 'href'},
            'title': {
                'selector': '.title',
                'text': True,
                'clean': True,
                'fallback_selectors': ['a']
            },
            'thumbnail': {'selector': 'img', 'attr': 'src'},
            'duration': {'selector': '.duration', 'text': True},
            'pagination': {
                'text_matches': ['next'],
                'attr': 'href',
                'label': 'Continue',
                'mode': 'List',
                'add_dir': False
            }
        }

        site = DummySite()
        result = utils.soup_videos_list(site, soup, selectors, play_mode='play')

        self.assertEqual(result['items'], 1)
        self.assertEqual(len(site.downloads), 1)
        entry = site.downloads[0]
        self.assertEqual(entry['name'], 'Third Clip')
        self.assertEqual(entry['thumbnail'], '')
        self.assertEqual(entry['duration'], '')

        self.assertEqual(result['next_url'], 'https://example.com/page/3')
        self.assertFalse(result['pagination_added'])
        self.assertEqual(site.dirs, [])


if __name__ == '__main__':
    unittest.main()

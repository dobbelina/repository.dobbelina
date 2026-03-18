import sys
import os
from pathlib import Path
import types

# Root paths
CWD = Path.cwd()
PLUGIN_PATH = CWD / "plugin.video.cumination"
os.chdir(str(PLUGIN_PATH))
sys.path.insert(0, str(PLUGIN_PATH))

# Mock Kodi
def mock_kodi():
    for name in ["xbmc", "xbmcgui", "xbmcplugin", "xbmcvfs", "xbmcaddon", "StorageServer", "CommonFunctions", "websocket"]:
        mock = types.ModuleType(name)
        if name == "xbmcvfs": mock.translatePath = lambda p: p
        if name == "xbmc":
            mock.LOGDEBUG = 0
            mock.log = lambda *args, **kwargs: None
            mock.translatePath = lambda p: p
        if name == "xbmcgui":
            class Dialog:
                def ok(self, *args): return True
                def notification(self, *args): pass
            class DialogProgress:
                def create(self, *args): pass
                def update(self, *args): pass
                def close(self): pass
            mock.Dialog = Dialog
            mock.DialogProgress = DialogProgress
        if name == "xbmcaddon":
            class Addon:
                def __init__(self, id=None): pass
                def getSetting(self, id): return "0"
                def getLocalizedString(self, id): return str(id)
                def getAddonInfo(self, id): return "."
            mock.Addon = Addon
        if name == "StorageServer":
            class Storage:
                def __init__(self, id, time): pass
                def cacheFunction(self, f, *args, **kwargs): return f(*args, **kwargs)
            mock.StorageServer = Storage
        sys.modules[name] = mock
    kodi_six = types.ModuleType("kodi_six")
    for name in ["xbmc", "xbmcgui", "xbmcplugin", "xbmcvfs", "xbmcaddon"]:
        setattr(kodi_six, name, sys.modules[name])
    sys.modules["kodi_six"] = kodi_six

sys.argv = ["plugin.video.cumination", "1", ""]
mock_kodi()

from resources.lib.sites import pornkai
from resources.lib import utils

# Mock site.add_download_link to capture results
found_videos = []
def mock_add_download_link(title, url, mode, img, desc, **kwargs):
    found_videos.append({"title": title, "url": url, "img": img})

pornkai.site.add_download_link = mock_add_download_link

# Use the full path from the original root
with open(str(CWD / "pornkai_search.html"), "r") as f:
    html = f.read()

# Mock getHtml to return our saved file
utils.getHtml = lambda *args, **kwargs: html

pornkai.List("https://pornkai.com/videos?q=sex")

print(f"Found {len(found_videos)} videos")
for i, v in enumerate(found_videos[:5]):
    print(f"{i+1}. {v['title']} - {v['url']}")

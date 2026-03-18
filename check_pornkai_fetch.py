#!/usr/bin/env python3
import os
import sys
import types
import importlib
from pathlib import Path

# Enable Playwright for this script
os.environ["CUMINATION_ALLOW_PLAYWRIGHT"] = "1"

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
PLUGIN_PATH = ROOT / "plugin.video.cumination"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PLUGIN_PATH))

# Mock sys.argv for Kodi-style execution
sys.argv = ["plugin.video.cumination", "1", ""]

def mock_kodi():
    # Mock xbmc modules
    for name in [
        "xbmc",
        "xbmcgui",
        "xbmcplugin",
        "xbmcvfs",
        "xbmcaddon",
        "StorageServer",
        "CommonFunctions",
        "websocket",
    ]:
        mock = types.ModuleType(name)
        if name == "xbmc":
            mock.LOGDEBUG = 0
            mock.LOGINFO = 1
            mock.log = lambda *args, **kwargs: None
            mock.translatePath = lambda p: p
        if name == "xbmcvfs":
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
                def getSetting(self, id):
                    if id in ["cache_time", "qualityask", "sortxt", "content"]: return "0"
                    return "false"
                def setSetting(self, id, val): pass
                def getLocalizedString(self, id): return str(id)
                def getAddonInfo(self, id):
                    if id == "version": return "20.0.0"
                    if id == "path": return str(PLUGIN_PATH)
                    if id == "profile": return str(ROOT / "userdata")
                    return "."
            mock.Addon = Addon
        if name == "StorageServer":
            class Storage:
                def __init__(self, id, time): pass
                def set(self, key, val): pass
                def get(self, key): return None
                def cacheFunction(self, f, *args, **kwargs): return f(*args, **kwargs)
            mock.StorageServer = Storage
        sys.modules[name] = mock

    # Mock kodi_six
    kodi_six = types.ModuleType("kodi_six")
    for name in ["xbmc", "xbmcgui", "xbmcplugin", "xbmcvfs", "xbmcaddon"]:
        setattr(kodi_six, name, sys.modules[name])
    sys.modules["kodi_six"] = kodi_six

mock_kodi()

from resources.lib import utils
import re

url = "https://pornkai.com/view?key=xv29201765"
print(f"Fetching: {url}")
html = utils.getHtml(url)
if "iframe" in html:
    print("Iframe found!")
    match = re.compile(r'iframe.+?src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(html)
    if match:
        print(f"Found src: {match[0]}")
else:
    print("Iframe NOT found.")
    print(f"HTML Length: {len(html)}")
    # Print a snippet to see what we got
    print(html[:1000])

'''
    Cumination
    Copyright (C) 2023 Team Cumination

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

# -*- coding: utf-8 -*-

import re
import json
import sqlite3
import time
import urllib
import requests
import xbmc
import xbmcgui

from resources.lib import utils
from resources.lib.adultsite import AdultSite
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Py2 + Py3 compatibility
try:
    from urllib.parse import quote, quote_plus, unquote, parse_qs, urlparse, urljoin
except ImportError:
    from urllib import quote, quote_plus, unquote
    import urlparse 
    from urlparse import urljoin
    parse_qs = urlparse.parse_qs
    urlparse = urlparse.urlparse

site = AdultSite(
    'xlovecam',
    '[COLOR hotpink]xLoveCam[/COLOR]',
    'https://www.xlovecam.com/en/',
    'https://medianew.wlresources.com/wl/xlovecam/logo-1663.png',
    'xlovecam', True, extract_meta=True
)

PROXY_PORT = 8787
BASE_URL = None
FAVORITES = {}
_proxy_servers = {}
_proxy_threads = {}
addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', 'online', 'xlovecam.onlineFav', site.img_favorites)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url, 'xlovecam.List', site.img_models)
    utils.eod()


@site.register()
def List(url):
    global FAVORITES
    FAVORITES = getFavorites()
    fv = [item["name"] for item in FAVORITES]
    xlovecam_sort = utils.addon.getSetting("xlovecam_sort")
    if not xlovecam_sort:
        xlovecam_sort = '35|Most Popular'
        utils.addon.setSetting("xlovecam_sort", '35|Most Popular')

    xlovecam_filter_id= utils.addon.getSetting('xlovecam_filter_id')
    xlovecam_filter_value= utils.addon.getSetting('xlovecam_filter_value')    
    if not xlovecam_filter_id:
        xlovecam_filter_id = ''
        xlovecam_filter_value = ''
        utils.addon.setSetting("xlovecam_filter_id", xlovecam_filter_id)
        utils.addon.setSetting("xlovecam_filter_value", xlovecam_filter_value)
    sort_name = xlovecam_sort.split('|')[1]
    site.add_dir('[COLOR hotpink]Sort: [/COLOR]{}'.format(sort_name), 'filter', 'xlovecam.Sort', site.img_filters, Folder=False)
    site.add_dir('[COLOR hotpink]Filter: [/COLOR]{}'.format('ALL' if xlovecam_filter_id == '' else xlovecam_filter_id.split('|')[1]), 'filter', 'xlovecam.Filter', site.img_filters, Folder=False)

    filter_dict = None
    sort_id = None
    nextQuery = None

    if url.startswith("{") or url.startswith("%7B"):
        data = json.loads(unquote(url))
        if "from" in data and "time" in data:
            nextQuery = {
                "from": data["from"],
                "time": data["time"],
                "off": data.get("off")
            }

    fid = addon.getSetting('xlovecam_filter_id').split('|')[0]
    val = addon.getSetting('xlovecam_filter_value')
    sid = addon.getSetting('xlovecam_sort').split('|')[0]
    if val.startswith("{") or val.startswith("%7B"):
        val = json.loads(unquote(val))["value"]
        # fid = json.loads(unquote(val))["filter_id"]
    
    if sid:
        sort_id = int(sid)

    if fid and val:
        filter_dict = {
            "filter_id": int(fid),
            "value": int(val),
            "sort": sort_id
        }
    response = xlovecam_online_list(nextQuery=nextQuery, filter=filter_dict)

    items = response["content"]["performerList"]
    for item in items:
        showType = item.get("showType")
        if showType != 1:
            continue
        name = item["nickname"]
        img = "https:" + item.get("liveImg")
        videourl = item.get("hlsPlaylist")
        fav = 'add'
        if name in fv:
            fav = 'del'
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + quote_plus(name))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}'.format(name), 'RunPlugin(' + contextrecord + ')'))]

        try:
            site.add_download_link(name, videourl, "Playvid", img, contextm=contextmenu, fav=fav)
        except:
            utils.kodilog('Item: ' + json.dumps(item, indent=4))
            continue

    nq = response["content"]["nextQuery"]
    count = sum(1 for item in items if item.get("showType") == 1)
    if count > 34:

        payload = {
            "from": nq["from"],
            "time": nq["time"],
            "off": nq.get("off"),
        }
        if sort_id:
            payload["sort"] = sort_id
        if filter_dict:
            payload["filter_id"] = filter_dict["filter_id"]
            payload["value"] = filter_dict["value"]

        np = quote(json.dumps(payload))
        site.add_dir("Next Page... ({})".format(int(nq["from"]/35+1)), np, "xlovecam.List", site.img_next)

    utils.eod()
    return

@site.register()
def Sort(url):
    labels = [
        "Most Popular",
        "Loves",
        "Top Rated",
        "New Models",
        "Toy Connected",
        "VIP",
        "Recent/Latest logins",
        "Favorites/Number of fans",
    ]

    sort_ids = [35, 22, 34, 33, 32, 31, 30, 29]

    selection = xbmcgui.Dialog().select("Select filter", labels)
    if selection == -1:
        return

    chosen_sort = sort_ids[selection]

    filter_dict = {"sort": chosen_sort}
    np = quote(json.dumps(filter_dict))
    utils.addon.setSetting("xlovecam_sort", str(sort_ids[selection]) + '|' + labels[selection])
    utils.refresh()


@site.register()
def Filter(url):
    labels = [
        "ALL - reset filters",
        "Categories",
        "Ethnicity",
        "Body Type",
        "Hair Colour",
        "Bust",
        "Sex parts",
        "Language",
        "Age",
        "Hair Length",
        "Eye Colour",
        "Height"
    ]

    filter_ids = [0, 10, 109, 112, 106, 101, 111, 7, 202, 107, 108, 114]

    selection = xbmcgui.Dialog().select("Select filter category", labels)
    if selection == -1:
        return

    chosen_filter_id = filter_ids[selection]

    # valori posibile
    if chosen_filter_id == 10:
        values = ["Young women", "Ladies", "Mature female", "Couples", "Lesbians", "Fetish female", "Transsexual", "Male"]
        value_ids = [1, 13, 6, 2, 3, 4, 5, 7]
    elif chosen_filter_id == 109:
        values = ["Arabian", "Asian", "Black", "White", "Latin"]
        value_ids = [1, 2, 3, 4, 5]
    elif chosen_filter_id == 112:
        values = ["Athletic", "Average", "BBW", "Plumper", "Skinny"]
        value_ids = [1, 2, 3, 4, 5]
    elif chosen_filter_id == 106:
        values = ["Blonde", "Redhead", "Chestnut", "Brunette", "Black"]
        value_ids = [1, 2, 3, 4, 5]
    elif chosen_filter_id == 101:
        values = ["Small boobs", "Average boobs", "Big boobs"]
        value_ids = [1, 2, 3]
    elif chosen_filter_id == 111:
        values = ["Shave sex", "Hairy sex", "Trimmed sex"]
        value_ids = [1, 2, 3]
    elif chosen_filter_id == 7:
        values = ["English", "Portuguese", "Italian", "Spanish", "Dutch", "French", "German"]
        value_ids = [1, 2, 3, 4, 5, 6, 7]
    elif chosen_filter_id == 202:
        values = ["18-20 years old", "20 - 25 years old", "25 - 30 years old", "30 - 35 years old", "35 - 40 years", "40 - 45 years old", "45+ years old"]
        value_ids = [1, 2, 3, 4, 5, 6, 7]
    elif chosen_filter_id == 107:
        values = ["Short", "Medium", "Long"]
        value_ids = [1, 2, 3]
    elif chosen_filter_id == 108:
        values = ["Black", "Chestnut", "Hazel", "Blue", "Green"]
        value_ids = [1, 2, 3, 4, 5]
    elif chosen_filter_id == 114:
        values = ["Less than  4'9\"", "4'9\" - 5'2\"", "5'2\" - 5'6\"", "5'6\" - 5'9\"", "5'9\" - 6'2\"", "Taller than 6.20 ft"]
        value_ids = [1, 2, 3, 4, 5, 6]
    else:
        utils.addon.setSetting("xlovecam_filter_value", '')
        utils.addon.setSetting("xlovecam_filter_id", '')
        utils.refresh()
        return

    sel = xbmcgui.Dialog().select("Select value", values)
    if sel == -1:
        return

    chosen_value = value_ids[sel]

    filter_dict = {
        "filter_id": chosen_filter_id,
        "value": chosen_value
    }

    np = quote(json.dumps(filter_dict))
    utils.addon.setSetting("xlovecam_filter_value", np)
    utils.addon.setSetting("xlovecam_filter_id", str(chosen_filter_id) + '|' + labels[selection] + '=' + values[sel])
    utils.refresh()

def xlovecam_online_list(nextQuery=None, filter=None):
    init = requests.get("https://www.xlovecam.com/en/")
    cookies = init.cookies.get_dict()

    token = xlovecam_get_csrf()
    xwid = cookies.get("x-windowId", "mt9rzsd4.2tp4l")

    url = "https://www.xlovecam.com/en/performerAction/onlineList/"

    sort_id = filter.get("sort", 35) if filter else 35
    if nextQuery is None:
        offset_from = 0     # 75
        data_time = int(time.time())
        data_off = ""
    else:
        offset_from = nextQuery.get("from")
        data_time = nextQuery.get("time")
        data_off = nextQuery.get("off") if nextQuery.get("off") is not None else ""

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.xlovecam.com/en/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    nick = filter.get("nickname") if filter else ""
    data = {
        "config[nickname]": nick,
    }

    if filter is not None and "filter_id" in filter:
        fid = filter["filter_id"]
        val = filter["value"]
        data["config[filter][{}][]".format(fid)] = str(val)

    data.update({
        "config[favorite]": "0",
        "config[recent]": "0",
        "config[vip]": "0",
        "config[sort][id]": str(sort_id),
        "offset[from]": str(offset_from),
        "offset[length]": "35",
        "origin": "fetch-stat-on-load",
        "stat": "1",
        "data[from]": str(offset_from),
        "data[time]": str(data_time),
        "data[off]": data_off,
        "featureSupported[sessionStorageLarge]": "true",
        "featureSupported[localStorage]": "true",
        "csrfProtectionToken": token,
    })
    cookies["x-windowId"] = xwid

    r = requests.post(url, headers=headers, cookies=cookies, data=data)
    return r.json()


def xlovecam_get_csrf():
    html = utils._getHtml("https://www.xlovecam.com/en/")
    token = re.search(r'csrfProtectionToken\s*=\s*"([^"]+)"', html)
    return token.group(1) if token else ""

def getFavorites():
    favorites = {}
    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT name, url, image FROM favorites WHERE mode='{}.Playvid'".format(site.name))
    favorites = [{"name": row[0], "url": row[1], "image": row[2]} for row in c.fetchall()]
    c.close()
    return favorites

@site.register()
def online(url):
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()

@site.register()
def onlineFav():
    on_line = utils.addon.getSetting("online_only")
    site.add_download_link('[COLOR red][B]Show {} models[/B][/COLOR]'.format('ALL' if on_line == 'true' else 'ON LINE'), site.url, 'online', '', '', noDownload=True)

    favorites = getFavorites()
    names = [item["name"] for item in favorites]
    for name in names:
        filter = {"nickname": name}
        item = xlovecam_online_list(nextQuery=None, filter=filter)["content"]["performerList"][0]
        showType = item.get("showType")
        if showType == 1:

            name = item.get("nickname")
            img = "https:" + item.get("liveImg")
            videourl = item.get("hlsPlaylist")
        elif on_line == "false":
            name += ' [COLOR yellow][OFFLINE][/COLOR]'
            img = "https:" + item.get("liveImg")
            videourl = site.url
        else:
            continue
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + quote_plus(name))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}'.format(name), 'RunPlugin(' + contextrecord + ')'))]
        try:
            site.add_download_link(name, videourl, "Playvid", img, contextm=contextmenu, fav='del')
        except:
            utils.kodilog('Item: ' + json.dumps(item, indent=4))
            continue
    utils.eod()


class HLSProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        global BASE_URL

        path = self.path
        clean = path.lstrip("/")
        utils.kodilog(f"[Proxy] RAW PATH = [{self.path}]")

        # -------------------------
        # MANIFEST (.m3u8)
        # -------------------------
        if clean.startswith("proxy.m3u8"):
            qs = urllib.parse.urlparse(path).query
            params = urllib.parse.parse_qs(qs)
            real_url = params.get("u", [""])[0]

            parsed = urllib.parse.urlparse(real_url)
            BASE_URL = f"{parsed.scheme}://{parsed.netloc}/"

            utils.kodilog(f"[Proxy] GET manifest: {real_url}")

            r = requests.get(real_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*"
            })

            text = r.text

            # 1. Creștem toleranța ISA
            text = re.sub(
                r'#EXT-X-TARGETDURATION:\d+',
                '#EXT-X-TARGETDURATION:4',
                text
            )

            # 2. Rescriem EXT-X-MAP
            text = re.sub(
                r'EXT-X-MAP:URI="([^"]+)"',
                lambda m: f'EXT-X-MAP:URI="{BASE_URL}{m.group(1).lstrip("/")}"',
                text
            )

            # 3. Rescriem segmentele relative în absolute
            def fix_segment(match):
                seg = match.group(1)
                if seg.startswith("http"):
                    return match.group(0)
                return f'#EXTINF:{match.group(2)}\n{BASE_URL}{seg.lstrip("/")}'
            
            text = re.sub(
                r'#EXTINF:([0-9\.]+)\s*\n([^\n]+)',
                lambda m: f'#EXTINF:{m.group(1)}\n{BASE_URL}{m.group(2).lstrip("/")}',
                text
            )

            # 4. Trimitem manifestul rescris
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(text.encode("utf-8"))
            return

        # -------------------------
        # SEGMENTE (.ts)
        # -------------------------
        target = self.path.lstrip("/")

        # dacă segmentul este relativ → îl facem absolut
        if not target.startswith("http"):
            target = BASE_URL + target.lstrip("/")

        utils.kodilog(f"[Proxy] GET segment: {target}")

        r = requests.get(
            target,
            stream=True,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Range": "bytes=0-"
            }
        )

        self.send_response(r.status_code)
        for k, v in r.headers.items():
            if k.lower() in ["content-type", "content-length", "accept-ranges"]:
                self.send_header(k, v)
        self.end_headers()

        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                self.wfile.write(chunk)

    def do_GET_old(self):
        global BASE_URL
        path = self.path

        utils.kodilog(f"[Proxy] RAW PATH = [{self.path}]")

        # -------------------------
        # MANIFEST (.m3u8)
        # -------------------------
        if path.startswith("/proxy.m3u8"):
            qs = urllib.parse.urlparse(path).query
            params = urllib.parse.parse_qs(qs)
            real_url = params.get("u", [""])[0]

            parsed = urllib.parse.urlparse(real_url)
            BASE_URL = f"{parsed.scheme}://{parsed.netloc}/"

            utils.kodilog(f"[Proxy] GET manifest: {real_url}")

            r = requests.get(real_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*"
            })

            text = r.text

            # RESCRIERE SEGMENTE
            def repl(match):
                line = match.group(1).strip()

                # URL absolut
                if line.startswith("http"):
                    seg = line
                else:
                    # URL relativ → păstrăm exact calea
                    seg = BASE_URL + line.lstrip("/")

                # rescriem către proxy
                return f"http://127.0.0.1:{PROXY_PORT}/{seg}"

            rewritten = re.sub(
                r'^(?!#)(.+)$',
                repl,
                text,
                flags=re.MULTILINE
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(rewritten.encode("utf-8"))
            return

        # -------------------------
        # SEGMENTE (.ts / .m4s)
        # -------------------------
        target = path.lstrip("/")

        # dacă segmentul este relativ → îl convertim în absolut
        if not target.startswith("http"):
            target = BASE_URL + target

        utils.kodilog(f"[Proxy] GET segment: {target}")

        r = requests.get(
            target,
            stream=True,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Range": "bytes=0-"
            }
        )

        self.send_response(r.status_code)
        for k, v in r.headers.items():
            if k.lower() in ["content-type", "content-length", "accept-ranges"]:
                self.send_header(k, v)
        self.end_headers()

        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                self.wfile.write(chunk)

def start_generic_proxy(port):
    global _proxy_servers, _proxy_threads

    if port in _proxy_servers:
        # proxy deja pornit pe acest port
        return

    server = HTTPServer(('127.0.0.1', port), HLSProxy)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    _proxy_servers[port] = server
    _proxy_threads[port] = thread


def stop_generic_proxy(port):
    global _proxy_servers, _proxy_threads

    if port in _proxy_servers:
        try:
            _proxy_servers[port].shutdown()
            _proxy_servers[port].server_close()
        except Exception as e:
            xbmc.log(f"Proxy stop error on port {port}: {e}", xbmc.LOGERROR)

        del _proxy_servers[port]
        del _proxy_threads[port]

class ProxyMonitor(xbmc.Monitor):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def onPlayBackStopped(self):
        stop_generic_proxy(self.port)

    def onPlayBackEnded(self):
        stop_generic_proxy(self.port)

@site.register()
def Playvid(url, name):
    if '[OFFLINE]' in name:
        utils.notify(name)
        return
    PORT = PROXY_PORT

    start_generic_proxy(PORT)
    monitor = ProxyMonitor(PORT)

    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]{}[CR]".format(utils.i18n('Loading video page')))

    try:
        m3u = utils._getHtml(url)
    except:
        vp.progress.close()
        stop_generic_proxy(PORT)
        return

    if m3u.strip().startswith("{"):
        try:
            err = json.loads(m3u)
            msg = err.get("error", {}).get("msg", "Unknown error")
            utils.notify(name, msg)
        except:
            utils.notify(name, "Invalid response")
        vp.progress.close()
        stop_generic_proxy(PORT)
        return

    variants = re.findall(
        r'#EXT-X-STREAM-INF:.*?BANDWIDTH=(\d+).*?\n(https?://[^\s]+)',
        m3u
    )

    if not variants:
        utils.notify(name, "No HLS sources")
        vp.progress.close()
        stop_generic_proxy(PORT)
        return

    sources = {}
    for bw, stream_url in variants:
        label = "Low" if int(bw) < 300000 else "High"
        sources[label] = stream_url

    videourl = utils.selector(
        utils.i18n('Select quality'),
        sources,
        setting_valid='qualityask',
        sort_by=lambda x: x,
        reverse=False
    )


    if not videourl:
        vp.progress.close()
        stop_generic_proxy(PORT)
        return

    selected_url = videourl

    vp.progress.update(75, "[CR]Found Stream[CR]")

    encoded = quote_plus(selected_url)
    proxy_url = f"http://127.0.0.1:{PORT}/proxy.m3u8?u={encoded}"

    li = xbmcgui.ListItem(path=proxy_url)
    li.setProperty("IsPlayable", "true")
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")
    li.setMimeType("application/vnd.apple.mpegurl")
    li.setContentLookup(False)

    vp.play_from_direct_link(proxy_url)

    vp.progress.close()



def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    # vp.play_from_link_to_resolve(url)
    try:
        vp.play_from_direct_link(url)
    except:
        return

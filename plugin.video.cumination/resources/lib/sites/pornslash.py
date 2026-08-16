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

import xbmc
import xbmcgui
import re
import urllib.parse
import random
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from six.moves import urllib_parse
import requests

PROXY_PORT = 8787
site = AdultSite('pornslash', '[COLOR hotpink]PornSlash[/COLOR]', 'https://www.pornslash.com/', 'pornslash.png', 'pornslash')

addon = utils.addon
_proxy_servers = {}
_proxy_threads = {}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink](Porn)Stars[/COLOR]', site.url + 'pornstars', 'Stars', site.img_models)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'videos/new?p=1')

@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="video-item".+?href="([^"]+)".+?src="([^"]+)".+?quality">([^>]+)<.+?duration">([^>]+)<.+?data-title="([^"]+)".+?data-encid="([^"]+)"'
                       , re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, resolution, duration, name, encid in match:
        name = utils.cleantext(name) + ' [COLOR yellow]{}[/COLOR]'.format(resolution)
        videopage = site.url.rstrip("/") + videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = match = re.search(r"<a\s+href='([^']+)'>[^<]*<span[^>]*nav-btn[^>]*>Next</span>", listhtml)
    if np:
        np = site.url.rstrip("/") + np.group(1)
        nextpage = re.search(r'\?p=(\d+)', np).group(1)
        cm_page = (utils.addon_sys + "?mode=pornslash.GotoPage" + "&url=" + urllib_parse.quote_plus(np) + "&np=" + str(nextpage))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('[COLOR hotpink]Next Page...({0})[/COLOR]'.format(nextpage), np, 'List', site.img_next, contextm = cm)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(
        r'class="cat-item"\shref="([^"]+)".*?src="([^"]+)".*?"cat-name">([^>]+)<'
        , re.DOTALL | re.IGNORECASE).findall(cathtml)

    if match:
        for videourl, img, cat in match:
            site.add_dir(cat, site.url.rstrip("/") + videourl + "?p=1", 'List', img)
        utils.eod()

@site.register()
def Stars(url):
    starshtml = utils.getHtml(url)
    # ---------
    # slash_ethnicity = utils.addon.getSetting('slash_ethnicity')
    # if not slash_ethnicity:
    #     slash_ethnicity = 'ALL'
    # utils.addon.setSetting("slash_ethnicity", slash_ethnicity)

    site.add_download_link(
        'Filters',
        url,
        'filters',
        site.img_filters,
        '',
        noDownload=True
    )
    # slash_ethnicity = '' if slash_ethnicity == 'ALL' else slash_ethnicity
    # ---------    

    match = re.compile(
        r'<a[^>]+class="poster-wrapper"[^>]+href="([^"]+)".*?<img[^>]+src="([^"]+)"[^>]+alt="([^"]+)"'
        , re.DOTALL | re.IGNORECASE).findall(starshtml)
    if match:
        for videourl, img, name in match:
            site.add_dir(name, site.url.rstrip("/") + videourl, 'List', img)
        np = match = re.search(r"<a\s+href='([^']+)'>[^<]*<span[^>]*nav-btn[^>]*>Next</span>", starshtml)
        if np:
            np = site.url.rstrip("/") + np.group(1)
            nextpage = re.search(r'[\?\&]p=(\d+)', np).group(1)
            site.add_dir('Next Page... ({0})'.format(nextpage), np, 'Stars', site.img_next)
        utils.eod()

@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if lp and int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('p={}'.format(np), 'p={}'.format(pg))
        contexturl = (utils.addon_sys + "?mode=pornslash.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


class HLSProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        import urllib.parse
        import requests

        path = self.path

        # --- MANIFEST ---
        clean = self.path.lstrip("/")
        utils.kodilog(f"[Proxy] RAW PATH = [{self.path}]")
        if clean.startswith("proxy.m3u8"):
            qs = urllib.parse.urlparse(path).query
            params = urllib.parse.parse_qs(qs)
            real_url = params.get("u", [""])[0]

            utils.kodilog(f"[Proxy] GET manifest: {real_url}")

            r = requests.get(real_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*"
            })

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(r.content)
            return

        # --- SEGMENTE ---
        target = self.path[1:]
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


@site.register()
def Playvid(url, name):
    PORT = PROXY_PORT

    start_generic_proxy(PORT)
    monitor = ProxyMonitor(PORT)

    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]{}[CR]".format(utils.i18n('Loading video page')))
    try:
        embed = utils._getHtml(url)
    except:
        utils.notify(name, 'No page found!')
        vp.progress.close()
        return
    master = re.search(r'fetch\("(https?://[^"]+)"', embed).group(1)
    try:
        m3u = utils._getHtml(master)
    except:
        vp.progress.close()
        stop_generic_proxy(PORT)
        return
    
    variants = re.findall(
        r'#EXT-X-STREAM-INF:.*?RESOLUTION=(\d+x\d+).*?\n(https?://[^\s]+)',
        m3u
    )

    if not variants:
        utils.notify("Playvid", "No HLS sources")
        vp.progress.close()
        stop_generic_proxy(PORT)
        return

    sources = {res: url for res, url in variants}
    videourl = utils.selector(
        utils.i18n('Select quality'),
        sources,
        setting_valid='qualityask',
        sort_by=lambda x: int(x.split('x')[1]),
        reverse=True
    )

    if not videourl:
        vp.progress.close()
        stop_generic_proxy(PORT)
        return

    selected_url = videourl

    vp.progress.update(75, "[CR]Found Stream[CR]")

    encoded = urllib.parse.quote_plus(selected_url)
    proxy_url = f"http://127.0.0.1:{PORT}/proxy.m3u8?u={encoded}"

    li = xbmcgui.ListItem(path=proxy_url)
    li.setProperty("IsPlayable", "true")
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")
    li.setMimeType("application/vnd.apple.mpegurl")
    li.setContentLookup(False)

    vp.play_from_direct_link(proxy_url)

    vp.progress.close()


class ProxyMonitor(xbmc.Monitor):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def onPlayBackStopped(self):
        stop_generic_proxy(self.port)

    def onPlayBackEnded(self):
        stop_generic_proxy(self.port)

@site.register()
def filters(url):
    cathtml = utils.getHtml(url)
    filter_dict = [
        {'display': 'Tits Size', 'name': 'tits_size'},
        {'display': 'Tits Type', 'name': 'tits_type'},
        {'display': 'Ass Size', 'name': 'ass'},
        {'display': 'Age Group', 'name': 'age'},
        {'display': 'Ethnicity', 'name': 'ethnicity'},
        {'display': 'Country', 'name': 'country'}
        ]
    names = [s["display"] for s in filter_dict]
    # selected_filter = utils.selector(
    #     'Select filter',
    #     names,
    #     sort_by=None,
    #     reverse=False
    # )
    selected_filter = xbmcgui.Dialog().select('Select filter', names)
    utils.notify('Selected Filter', str(selected_filter))
    filter_name = filter_dict[selected_filter]['name']
    item_dict = extract_select_items(cathtml, filter_name)
    items = list(item_dict.keys())
    keys = names = list(item_dict.values())
    idx = xbmcgui.Dialog().select('Select {}'.format(filter_dict[selected_filter]['display']), items)
    key = keys[idx]

    new_url = site.url.rstrip('/') + str(key)
    contexturl = (utils.addon_sys + "?mode=pornslash.Stars&url=" + urllib_parse.quote_plus(new_url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    # xbmc.executebuiltin("Container.Update(plugin://plugin.video.cumination/?mode=Stars&url=%s)" % new_url)



def extract_select_items(html, name):
    block = re.search(
        rf'<div class="select-menu" data-name={name}>(.*?</a>)</div>',
        html,
        re.DOTALL | re.IGNORECASE
    )
    if not block:
        return {}

    content = block.group(1)

    pattern = re.compile(
        r"<a class='select-item[^']*' href='([^']+)'[^>]*>([^<]+)</a>",
        re.IGNORECASE
    )
    items = pattern.findall(content)
    return {title.strip(): url.strip() for url, title in items}    
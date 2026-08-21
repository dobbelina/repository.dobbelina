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
import xbmcplugin
import sys
import json
import re
import html
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from six.moves import urllib_parse
from resources.lib.jsunpack import unpack
from urllib.parse import urljoin, urlparse, parse_qs
import urllib


site = AdultSite('xtapes', '[COLOR hotpink]XTapes.la[/COLOR]', 'https://xtapes.la/', 'xtapes.png', 'xtapes')

addon = utils.addon
PROXY_PORT = '8787'
_proxy_servers = {}
_proxy_threads = {}
url = site.url + '?display=tube&filtre=date'


@site.register(default_mode=True)
def List(url=None):
    network_setting = utils.addon.getSetting('xtapes_network')
    networkname_setting = utils.addon.getSetting('xtapes_networkname')
    filter_setting = utils.addon.getSetting('xtapes_filter')
    if not network_setting:
        networkname_setting = 'ALL'
        network_setting = site.url # + '?display=tube&filtre=date'
        utils.addon.setSetting('xtapes_network', network_setting)
        utils.addon.setSetting('xtapes_networkname', 'ALL')
        filter_setting = '?display=tube&filtre=date'
        utils.addon.setSetting('xtapes_filter', filter_setting)
    if url == site.url: # or ('/search/' in url):
        url = network_setting + filter_setting

    # filter_setting = utils.addon.getSetting('xtapes_filter')
    # if not filter_setting:
    #     filter_setting = '?display=tube&filtre=date'
    #     utils.addon.setSetting('xtapes_filter', filter_setting)
    #     import html
    #     url = url + filter_setting
    # url = re.sub(r"#038;filtre=[^&]+", "", url) if '?' in url else url
    # url = parse_qs(urlparse(url).query)
    # if '/search/' in url:
    #     # url = url.replace('?display', '&display')
    #     networkname_setting = (parse_qs(urlparse(url).query)).get("s", [""])[0]
    #     networkname_setting = (url.split('/search/')[1]).split('/')[0]
    
    try:
        current_filter = filter_setting.split('filtre=')[1]
    except:
        current_filter = 'date'
    site.add_dir(
        f'[COLOR hotpink]Filters[/COLOR] Sort by: [COLOR yellow][{current_filter}][/COLOR] ' + ('Search:' if '/search/' in url else 'Network/Tag:') + ' [COLOR yellow][{}][/COLOR]'.format(networkname_setting),
        url,
        'filters',
        site.img_filters,
        Folder=False
    )

    # site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    url = url.replace('&#038;', '&')       # .replace('&&', '&')
    url = url.replace('#038;', '&')

    html = utils.getHtml(url)
    if 'Sorry, but nothing matched your search criteria.' in html:
        utils.notify(networkname_setting, 'Sorry, but nothing matched your search criteria.')

    delimiter = '<li class="border-radius'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+)"'
    re_duration = r'class="time-infos[^"]*"[^>]*>([^<]+)<'

    utils.videos_list(
        site, 'xtapes.Playvid', html, delimiter,
        re_videopage, re_name, re_img,
        re_duration=re_duration,
        contextm='xtapes.Related'
    )

    re_npurl = r'class="next page-numbers" href="([^"]+)">Next videos'
    # re_npurl = r'<link rel="next" href="([^"]+)" />'
    re_npnr  = r'class="next page-numbers" href="[^"]+/(\d+)'
    re_lpnr  = r"<a class='page-numbers' href='[^']*/(\d+)[^']*'>\s*[\d,]+\s*</a>(?!.*<a class='page-numbers')"

    utils.next_page(
        site, 'xtapes.List', html,
        re_npurl, re_npnr, re_lpnr=re_lpnr,
        contextm='xtapes.GotoPage'
    )

    utils.eod()

@site.register()
def filters(url):
    html = utils.getHtml(url + '?display=tube&filtre=date')
    container = re.compile(
        r'<li id="menu-item-.+?href="([^"]+)">([^>]+)</a>\s<ul class="sub-menu">'
        , re.DOTALL | re.IGNORECASE
    ).findall(html)
    container.append((site.url + "porn-movies-hd/", "Full Movies"))
    container.append(("", "Sort by"))
    if not container:
        return
    labels = [label for url, label in container]
    urls   = [url   for url, label in container]
    selection = xbmcgui.Dialog().select('Select', labels)
    if selection == 0:
        container = re.compile(
            r'<ul class="sub-menu">(.+?)\s</ul>'
            , re.DOTALL | re.IGNORECASE
        ).findall(html)
        if container:
            filters = re.compile(
                r'<li.+?href="([^"]+)">([^<]+)<',
                re.DOTALL | re.IGNORECASE
            ).findall(container[0])
            filters.insert(0, (site.url, "ALL"))
            labels = [label for url, label in filters]
            urls   = [url   for url, label in filters]
            selection = xbmcgui.Dialog().select('Select filter', labels)
            if selection != -1:
                filter_value = urls[selection].replace('&amp;', '&')
                utils.addon.setSetting('xtapes_network', filter_value)
                utils.addon.setSetting('xtapes_networkname', labels[selection])
                utils.refresh()

    elif selection == 1:
        container = re.compile(
            r'<ul class="sub-menu">(.+?)\s</ul>'
            , re.DOTALL | re.IGNORECASE
        ).findall(html)
        if container:
            filters = re.compile(
                r'<li.+?href="([^"]+)">([^<]+)<',
                re.DOTALL | re.IGNORECASE
            ).findall(container[1])
            filters.insert(0, (site.url, "ALL"))
            labels = [label for url, label in filters]
            urls   = [url   for url, label in filters]
            selection = xbmcgui.Dialog().select('Select filter', labels)
            if selection != -1:
                filter_value = urls[selection].replace('&amp;', '&')
                utils.addon.setSetting('xtapes_network', filter_value)
                utils.addon.setSetting('xtapes_networkname', labels[selection])
                utils.refresh()
    elif selection == 2:
        filter_value = urls[selection]
        utils.addon.setSetting('xtapes_network', filter_value)
        utils.addon.setSetting('xtapes_networkname', labels[selection])
        utils.refresh()
    elif selection == 3:
        container = re.compile(
            r'<ul class="filtre-list">(.+?)\s</ul>',
            re.DOTALL | re.IGNORECASE
        ).findall(html)

        if container:
            filters = re.compile(
                r'<li.+?href="([^"]+)">([^<]+)<',
                re.DOTALL | re.IGNORECASE
            ).findall(container[0])

            labels = [label for url, label in filters]
            urls   = [url   for url, label in filters]

            selection = xbmcgui.Dialog().select('Select filter', labels)

            if selection != -1:
                filter_value = urls[selection].replace('&amp;', '&')
                utils.addon.setSetting('xtapes_filter', filter_value)
                utils.refresh()

    return





@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('xtapes.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+') + '/page/1/'
        utils.addon.setSetting('xtapes_network', url)
        utils.addon.setSetting('xtapes_networkname', keyword)
        List(url + utils.addon.getSetting("xtapes_filter"))


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

class ProxyMonitor(xbmc.Monitor):
    def __init__(self, port):
        super().__init__()
        self.port = port

    def onPlayBackStopped(self):
        stop_generic_proxy(self.port)

    def onPlayBackEnded(self):
        stop_generic_proxy(self.port)


@site.register()
def Playvid(url, name, download=None):
    global PROXY_PORT

    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]{}[CR]".format(utils.i18n('load_vpage')))
    videohtml = utils.getHtml(url, site.url, ignoreCertificateErrors=True)
    match = re.compile(r'IFRAME SRC="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        iframe = match[0]
    else:
        utils.notify(name, utils.i18n('not_found'))
        return
    try:
        raw = utils._getHtml(iframe)
    except:
        try:
            raw = utils._getHtml(match[1])
        except:
            utils.notify('Oh oh', utils.i18n('not_found'))
            vp.progress.close()
            return
    match = re.compile(r'>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(raw)
    if not match:
        utils.notify('Oh oh', utils.i18n('not_found'))
        vp.progress.close()
        return

    videourl = unpack(match[0])
    m = re.search(r'var\s+links\s*=\s*(\{.*?\});', videourl, re.S)
    if not m:
        utils.notify("Playvid", "No links{} found")
        return

    try:
        links = json.loads(m.group(1))
    except:
        utils.notify("Playvid", "Error parsing links{}")
        return

    master = links.get("hls2")
    if not master:
        utils.notify("Playvid", "No HLS link")
        return
    master_data = utils._getHtml(master)
    master_data = master_data.replace('\r', '\n')
    master_data = re.sub(r'\s*#', '\n#', master_data)
    master_data = re.sub(r'\s*(index[^ \n]+\.m3u8)', r'\n\1', master_data)
    master_data = re.sub(r'\n+', '\n', master_data).strip()

    sources = {}
    base = master.rsplit("/", 1)[0] + "/"

    for block in re.findall(r'(#EXT-X-STREAM-INF[^\n]+)\n([^\n]+\.m3u8[^\n]*)', master_data):
        inf_line, url_line = block
        rez = re.search(r'RESOLUTION=\d+x(\d+)', inf_line)
        if rez:
            height = rez.group(1)
            variant_url = urljoin(base, url_line.strip())
            sources[height] = variant_url

    if not sources:
        utils.notify("Playvid", "No quality options")
        return

    videourl = utils.selector(
        utils.i18n('pick_qual'),
        sources,
        setting_valid='qualityask',
        sort_by=lambda x: int(x.split()[0].replace("x", "")),
        reverse=True
    )

    if not videourl:
        utils.notify("Playvid", "Nothing selected")
        return

    PROXY_PORT = 8787
    encoded = urllib.parse.quote_plus(videourl)
    proxy_url = f"http://127.0.0.1:{PROXY_PORT}/proxy.m3u8?u={encoded}"

    start_generic_proxy(PROXY_PORT)
    ProxyMonitor(PROXY_PORT)

    li = xbmcgui.ListItem(path=proxy_url)
    li.setProperty("IsPlayable", "true")
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")
    li.setMimeType("application/vnd.apple.mpegurl")
    li.setContentLookup(False)

    vp.play_from_direct_link(proxy_url)
    vp.progress.close()

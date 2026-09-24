'''
    Cumination
    Copyright (C) 2022 Team Cumination

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

import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
from six.moves import urllib_request
import json

site = AdultSite('familypornhd', '[COLOR hotpink]Familypornhd[/COLOR]', 'https://familypornhd.com/', 'https://familypornhd.com/wp-content/uploads/2020/06/Light-normal.png', 'familypornhd')


def _play_hls_proxy(url, name, referer):
    state = {'urls': {}, 'next_id': 0}
    request_headers = {
        'User-Agent': utils.USER_AGENT,
        'Accept': '*/*',
        'Referer': referer
    }

    def fetch(target):
        request = urllib_request.Request(target, headers=request_headers)
        response = urllib_request.urlopen(request, timeout=30)
        return response.read()

    def add_url(target):
        resource_id = str(state['next_id'])
        state['next_id'] += 1
        state['urls'][resource_id] = target
        return '/hls/' + resource_id

    def rewrite_playlist(content, base_url):
        text = content.decode('utf-8', 'ignore')
        rewritten = []
        uri_pattern = re.compile(r'URI="([^"]+)"', re.IGNORECASE)
        for line in text.splitlines():
            if not line.strip():
                continue
            if line.startswith('#'):
                line = uri_pattern.sub(
                    lambda match: 'URI="{}"'.format(
                        add_url(urllib_parse.urljoin(base_url, match.group(1)))
                    ),
                    line
                )
                rewritten.append(line)
            else:
                rewritten.append(add_url(urllib_parse.urljoin(base_url, line.strip())))
        return '\n'.join(rewritten).encode('utf-8')

    class ProxyHandler(BaseHTTPRequestHandler):
        def _resource_id(self):
            resource_id = self.path.split('?', 1)[0].rsplit('/', 1)[-1]
            if resource_id == 'master.m3u8':
                return 'master'
            return resource_id

        def do_HEAD(self):
            if self._resource_id() not in state['urls']:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()

        def do_GET(self):
            resource_id = self._resource_id()
            target = state['urls'].get(resource_id)
            if target is None:
                self.send_error(404)
                return

            try:
                content = fetch(target)
                is_playlist = content.lstrip().startswith(b'#EXTM3U')
                if is_playlist:
                    content = rewrite_playlist(content, target)
                    content_type = 'application/vnd.apple.mpegurl'
                else:
                    content_type = 'video/mp2t'
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as exc:
                utils.kodilog(f'Familypornhd HLS proxy failed for {target}: {exc}')
                self.send_error(502)

        def log_message(self, format_string, *args):
            return

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    stopped = {'value': False}

    def stop_proxy():
        if stopped['value']:
            return
        stopped['value'] = True
        try:
            server.shutdown()
            server.server_close()
            utils.kodilog('Familypornhd HLS proxy stopped')
        except Exception as exc:
            utils.kodilog(f'Familypornhd HLS proxy stop failed: {exc}')

    def monitor_proxy():
        monitor = xbmc.Monitor()
        playback_started = False
        while not monitor.abortRequested():
            if xbmc.Player().isPlaying():
                playback_started = True
            elif playback_started:
                break
            if monitor.waitForAbort(0.5):
                break
        stop_proxy()

    state['urls']['master'] = url
    server = ThreadedHTTPServer(('127.0.0.1', 0), ProxyHandler)
    port = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=monitor_proxy, daemon=True).start()
    proxy_url = f'http://127.0.0.1:{port}/hls/master.m3u8'
    return proxy_url


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    # site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url)
    if 'You have requested a page or file which doesn\'t exist' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    html = html.split('>Trending Porn<')[0]
    delimiter = 'article class="entry-tpl-grid'
    re_videopage = 'href="([^"]+)"><'
    re_name = 'title="([^"]+)"'
    re_img = ' src="([^"]+)"'
    utils.videos_list(site, 'familypornhd.Playvid', html, delimiter, re_videopage, re_name, re_img, contextm='familypornhd.Related')

    re_npurl = r'href="([^"]+)">Next'
    re_npnr = r'next" href="[^"]+/page/(\d+)'
    utils.next_page(site, 'familypornhd.List', html, re_npurl, re_npnr, contextm='familypornhd.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('familypornhd.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Channels(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<li>.+?href="([^"]+)"\s+style="background-image:url\(([^\)]+)\)">.+?<h4>([^<]+).+?<strong>(\d+).+?</li>', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({})[/COLOR]'.format(count.strip())
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Pornstars(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="wp-caption".+?href="([^"]+)".+? src="([^"]+)".+?wp-caption-text">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name in match:
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'href="([^"]+)">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml.split('page-title">Categories<')[-1].split('class="g1-row-background-media"')[0])
    for caturl, name in match:
        site.add_dir(name.title(), caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex='<a href="([^"]+)" target="_blank"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)

    match = re.compile('class="embed-container"><iframe.*?src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        iframeurl = match[0]
        hash = iframeurl.split('/')[-1]
        if 'bestwish.lol' in iframeurl:
            url1 = 'https://bestwish.lol/ajax/stream?filecode={}'.format(hash)
            html = utils.getHtml(url1, 'https://bestwish.lol/')
            jsondata = json.loads(html)
            videourl = jsondata["streaming_url"]
            videourl += '|Referer=https://bestwish.lol/&Origin=https://bestwish.lol'
            vp.play_from_direct_link(videourl)
        elif 'video-mart.com' in iframeurl or 'videostreamingworld.com' in iframeurl or 'watchstreamhd.com' in iframeurl:
            host = iframeurl.rsplit('/', 2)[0]
            url1 = '{}/player/index.php?data={}&do=getVideo'.format(host, hash)
            hdr = dict(utils.base_hdrs).copy()
            hdr['Accept'] = '*/*'
            hdr['X-Requested-With'] = 'XMLHttpRequest'
            data = {'hash': hash, 'r': ''}
            html = utils.getHtml(url1, iframeurl, headers=hdr, data=data)
            jsondata = json.loads(html)
            videourl = jsondata["videoSource"]
            if 'watchstreamhd.com' in videourl and videourl.lower().split('|', 1)[0].endswith('.txt'):
                videourl = _play_hls_proxy(videourl.split('|', 1)[0], name, iframeurl)
            vp.IA_check = 'IA'
            vp.play_from_direct_link(videourl)
        else:
            iframehtml = utils.getHtml(iframeurl, url)
            if 'kt_player.swf' in iframehtml:
                vp.play_from_kt_player(iframehtml)
            else:
                host = iframeurl.rsplit('/', 1)[0]
                url1 = host + '/data.php?filecode=' + hash
                html = utils.getHtml(url1, iframeurl)
                jsondata = json.loads(html)
                videourl = jsondata["streaming_url"]
                vp.play_from_direct_link(videourl)

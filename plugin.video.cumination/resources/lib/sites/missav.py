'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
import urllib.request as urllib_request
from http.cookiejar import CookieJar
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import xbmc
from resources.lib import utils, jsunpack
from resources.lib.adultsite import AdultSite

site = AdultSite('missav', '[COLOR hotpink]Miss AV[/COLOR]', 'https://missav123.com/', 'missav.png', 'missav')

# Session globale
cookie_jar = CookieJar()
opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(cookie_jar))
session_established = False


def get_headers(url):
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': url,
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def establish_session():
    global session_established
    if session_established:
        return True
    try:
        headers = get_headers(site.url)
        request = urllib_request.Request(site.url, headers=headers)
        opener.open(request, timeout=20)
        session_established = True
        return True
    except Exception:
        session_established = False
        return False


def make_request(url, data=None, max_retries=3):
    global session_established
    if not session_established:
        if not establish_session():
            return ""

    headers = get_headers(url)
    for attempt in range(max_retries):
        try:
            request = urllib_request.Request(url, data=data, headers=headers)
            with opener.open(request, timeout=20) as response:
                return response.read().decode('utf-8', errors='ignore')
        except urllib_request.HTTPError as e:
            if e.code == 403:
                session_established = False
                if not establish_session():
                    break
        except Exception:
            pass
        if attempt < max_retries - 1:
            xbmc.sleep(3000)
    return ""


class HlsProxy(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, state):
        super().__init__(server_address, RequestHandlerClass)
        self.state = state


class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            state = self.server.state
            proxy_opener = state.get('opener')
            playlist_url = state.get('real_playlist_url')

            if not proxy_opener or not playlist_url:
                return self.send_error(500, 'Proxy not configured')

            base_stream_url = playlist_url.rsplit('/', 1)[0]
            headers = state.get('headers')
            request_file = self.path.rsplit('/', 1)[-1]

            if request_file.endswith('.m3u8'):
                req = urllib_request.Request(playlist_url, headers=headers)
                with proxy_opener.open(req, timeout=15) as response:
                    content = response.read().decode('utf-8', errors='ignore')

                modified_lines, segment_map, segment_index = [], {}, 0
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxy_segment_name = f"{segment_index}.ts"
                        segment_map[proxy_segment_name] = f"{base_stream_url}/{line}"
                        modified_lines.append(proxy_segment_name)
                        segment_index += 1
                    else:
                        modified_lines.append(line)

                state['segment_map'] = segment_map
                self.send_response(200)
                self.send_header('Content-type', 'application/vnd.apple.mpegurl')
                self.end_headers()
                self.wfile.write('\n'.join(modified_lines).encode('utf-8'))

            elif request_file.endswith('.ts'):
                segment_map = state.get('segment_map', {})
                real_segment_url = segment_map.get(request_file)
                if not real_segment_url:
                    return self.send_error(404, 'Segment not found')

                req = urllib_request.Request(real_segment_url, headers=headers)
                with proxy_opener.open(req, timeout=15) as response:
                    segment_data = response.read()
                    content_type = response.getheader('Content-Type', 'video/mp2t')

                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(segment_data)
            else:
                self.send_error(404, 'Not Found')

        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        pass


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Actress List[/COLOR]', site.url + 'en/actresses', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Amateur[/COLOR]', 'Amateur', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', 'Uncensored', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Chinese AV[/COLOR]', 'Madou', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'en/search/', 'Search', site.img_search)
    List(site.url + 'en/new?page=1')
    utils.eod()


@site.register()
def List(url):
    html = make_request(url)
    if not html:
        utils.notify('Oh Oh', 'Failed to load page')
        return

    match = re.compile(r'<div\s*@mouseenter.+?img.+?data-src="([^"]+).+?alt="([^"]+).+?href="([^"]+)"\s*alt="([^""]+).+?<span.+?>\s*([\d:]+)', re.DOTALL | re.IGNORECASE).findall(html)
    for img, info, videopage, name, duration in match:
        info = utils.cleantext(info)
        duration = utils.cleantext(duration)
        site.add_download_link(name, videopage, 'Playvid', img, info, duration=duration, noDownload=True, fanart=img)

    match = re.compile(r'aria-label="Go to page \d+">\s*(\d+)\s*</a>\s*<a href="([^"]+page=(\d+))"\s+rel="next"', re.DOTALL | re.IGNORECASE).findall(html)
    if match:
        lp, npurl, np = match[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}/{1}'.format(np, lp), npurl, 'List', site.img_next)
    utils.eod()


@site.register()
def Models(url):
    cathtml = make_request(url)
    if not cathtml:
        return

    match = re.compile(r'<li>\s*<div.+?img\s*src="([^"]+).+?href="([^"]+).+?truncate">([^<]+).+?nord10">([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for img, caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]({0})[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', img)

    match = re.compile(r'aria-label="Go to page \d+">\s*(\d+)\s*</a>\s*<a href="([^"]+page=(\d+))"\s+rel="next"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if match:
        lp, npurl, np = match[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}/{1}'.format(np, lp), npurl, 'Models', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    html = make_request(site.url + 'en/')
    if not html:
        return

    try:
        section = re.compile(r'''(<span\s+x-cloak[="\s]+x-show="showCollapse === '{0}'.+?</span>)'''.format(url.lower()), re.IGNORECASE | re.DOTALL).findall(html)[0]
        match = re.compile(r'href="([^"]+)[^>]+>([^<]+)', re.IGNORECASE | re.DOTALL).findall(section)
        for caturl, name in match:
            name = utils.cleantext(name)
            site.add_dir(name, caturl, 'List', '')
    except:
        pass
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url + keyword.replace(' ', '%2B')
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    video_page = make_request(url)
    if not video_page:
        vp.progress.close()
        utils.notify('Oh Oh', 'Failed to load video page')
        return

    packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\)[^\n]+)', re.DOTALL | re.IGNORECASE).search(video_page)

    if not packed:
        vp.progress.close()
        utils.notify('Oh Oh', 'No packed data found')
        return

    try:
        unpacked = jsunpack.unpack(packed.group(1)).replace('\\', '')
    except Exception:
        vp.progress.close()
        utils.notify('Oh Oh', 'Failed to unpack video data')
        return

    # Cherche les différentes qualités
    stream_url = None
    quality_patterns = [
        r"source1280\s*=\s*['\"]([^'\"]+)['\"]",
        r"source842\s*=\s*['\"]([^'\"]+)['\"]",
        r"source\s*=\s*['\"]([^'\"]+)['\"]",
        r"file\s*:\s*['\"]([^'\"]+\.m3u8[^'\"]*)['\"]",
        r"src\s*:\s*['\"]([^'\"]+\.m3u8[^'\"]*)['\"]"
    ]

    for pattern in quality_patterns:
        match = re.search(pattern, unpacked)
        if match:
            stream_url = match.group(1)
            break

    if not stream_url:
        vp.progress.close()
        utils.notify('Oh Oh', 'No stream URL found')
        return

    vp.progress.update(50, "[CR]Setting up proxy...[CR]")

    headers = get_headers(url)

    httpd = None
    try:
        # Port unique
        import random
        port = random.randint(49000, 49100)

        server_address = ('127.0.0.1', port)
        current_video_state = {
            'real_playlist_url': stream_url,
            'base_url': stream_url.rsplit('/', 1)[0],
            'headers': headers,
            'opener': opener
        }

        httpd = HlsProxy(server_address, ProxyHandler, current_video_state)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        local_playlist_url = f"http://127.0.0.1:{port}/playlist.m3u8"

        vp.progress.update(75, "[CR]Starting playback...[CR]")
        vp.play_from_direct_link(local_playlist_url)

        monitor = xbmc.Monitor()
        timeout = 0
        while timeout < 30 and not xbmc.Player().isPlaying():
            if monitor.waitForAbort(0.5):
                break
            timeout += 0.5

        if xbmc.Player().isPlaying():
            while xbmc.Player().isPlaying():
                if monitor.waitForAbort(1):
                    break
    except Exception:
        utils.notify('Error', 'Playback failed')
    finally:
        if httpd:
            try:
                httpd.shutdown()
                httpd.server_close()
            except:
                pass

# -*- coding: utf-8 -*-
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
import html
import urllib.parse
import xbmc
import threading
import socket
import select
import time
import ssl
import xbmcgui
import sys
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('8kporner', '[COLOR hotpink]8k Porner[/COLOR]', 'https://8kporner.com', '8kporner.png', '8kporner')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'identity',
}


# ============================================================================
# PROXY CONTROLLER - Pour contourner les restrictions SSL sur les IPs CDN
# ============================================================================

class ProxyController:
    """Proxy local pour contourner les restrictions SSL de Kodi sur les IPs CDN"""
    
    def __init__(self, upstream_url, upstream_headers=None):
        self.upstream_url = upstream_url
        self.upstream_headers = upstream_headers or {}
        self.port = self._find_free_port()
        self.server_socket = None
        self.running = False
        self.thread = None
        
    def _find_free_port(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
        
    def start(self):
        """Demarre le proxy et retourne l'URL locale"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self.thread = threading.Thread(target=self._serve)
            self.thread.daemon = True
            self.thread.start()
            
            time.sleep(0.1)
            return "http://127.0.0.1:{0}/stream".format(self.port)
        except Exception as e:
            xbmc.log('[8kporner] Proxy error: ' + str(e), xbmc.LOGERROR)
            return None
            
    def _serve(self):
        """Boucle principale du serveur proxy"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                ready, _, _ = select.select([self.server_socket], [], [], 1.0)
                if not ready:
                    continue
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except:
                continue
                
    def _handle_client(self, client_socket):
        """Gere une connexion client (Kodi)"""
        try:
            request_data = b''
            client_socket.settimeout(5.0)
            
            while True:
                try:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    request_data += chunk
                    if b'\r\n\r\n' in request_data:
                        break
                except:
                    break
            
            if not request_data:
                return
                
            request_text = request_data.decode('utf-8', errors='ignore')
            
            range_header = None
            for line in request_text.split('\r\n'):
                if line.startswith('Range:'):
                    range_header = line.split(':', 1)[1].strip()
                    break
            
            headers = dict(self.upstream_headers)
            if range_header:
                headers['Range'] = range_header
            
            headers.pop('Origin', None)
            headers.pop('Referer', None)
            
            import urllib.request
            req = urllib.request.Request(self.upstream_url, headers=headers, method='GET')
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            response = urllib.request.urlopen(req, context=ctx, timeout=30)
            
            status_line = "HTTP/1.1 {0} {1}\r\n".format(response.getcode(), response.msg)
            client_socket.send(status_line.encode())
            
            for key, value in response.headers.items():
                if key.lower() not in ('transfer-encoding', 'connection'):
                    try:
                        header_line = "{0}: {1}\r\n".format(key, value)
                        client_socket.send(header_line.encode())
                    except:
                        pass
            
            client_socket.send(b"\r\n")
            
            while self.running:
                try:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    client_socket.send(chunk)
                except:
                    break
                    
        except Exception as e:
            xbmc.log('[8kporner] Proxy client error: ' + str(e), xbmc.LOGERROR)
        finally:
            try:
                client_socket.close()
            except:
                pass
            
    def stop(self):
        """Arrete le proxy"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


class PlaybackGuard:
    """Surveille la lecture et arrete le proxy quand c'est fini"""
    
    def __init__(self, player, monitor, play_url, controller):
        self.player = player
        self.monitor = monitor
        self.play_url = play_url
        self.controller = controller
        
    def start(self):
        thread = threading.Thread(target=self._watch)
        thread.daemon = True
        thread.start()
        
    def _watch(self):
        max_wait = 300
        waited = 0
        
        while not self.monitor.abortRequested() and waited < max_wait:
            if self.player.isPlaying() and self.player.getPlayingFile() == self.play_url:
                break
            xbmc.sleep(100)
            waited += 1
        
        while not self.monitor.abortRequested():
            if not self.player.isPlaying():
                break
            if self.player.getPlayingFile() != self.play_url:
                break
            xbmc.sleep(1000)
            
        xbmc.sleep(2000)
        self.controller.stop()


def _is_ipv4(value):
    """Verifie si une chaine est une IPv4"""
    parts = (value or "").split(".")
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


# ============================================================================
# FIN PROXY CONTROLLER
# ============================================================================


def transform_url(url):
    """Transforme les URLs en URLs internes du site"""
    parsed = urllib.parse.urlsplit(url or "")
    if parsed.netloc.lower() not in ("8kporner.com", "www.8kporner.com"):
        return url

    query = urllib.parse.parse_qs(parsed.query)
    if query.get("link1"):
        return url

    path = urllib.parse.unquote(parsed.path).rstrip("/")
    page_id = query.get("page_id", [""])[0]
    params = []

    if path in ("/videos/latest", "/videos/trending", "/videos/top"):
        params = [("link1", "videos"), ("page", path.rsplit("/", 1)[-1])]
    elif path == "/search":
        params = [("link1", "search"), ("keyword", query.get("keyword", [""])[0])]
    elif path == "/categories":
        params = [("link1", "categories")]
    elif path == "/pornstars":
        params = [("link1", "pornstars")]
    elif path.startswith("/videos/category/"):
        params = [("link1", "videos"), ("page", "category"), ("id", path[len("/videos/category/"):])]
    elif path.startswith("/videos/pornstar/"):
        params = [("link1", "videos"), ("page", "pornstar"), ("id", path[len("/videos/pornstar/"):])]
    elif path.startswith("/watch/"):
        params = [("link1", "watch"), ("id", path[len("/watch/"):])]

    if not params:
        return url
    if page_id:
        params.append(("page_id", page_id))
    return urllib.parse.urljoin(site.url, "?" + urllib.parse.urlencode(params))


def fetch_html(url, referer=None):
    """Recupere le HTML d'une URL"""
    try:
        import requests
        url = transform_url(url)
        headers = HEADERS.copy()
        if referer:
            headers['Referer'] = referer
        response = requests.get(url, headers=headers, timeout=20)
        return response.text if response.status_code == 200 else ""
    except Exception as e:
        xbmc.log('[8kporner] Error: ' + str(e), xbmc.LOGERROR)
        return ""


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + '/categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + '/pornstars', 'Pornstars', site.img_models)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '/search?keyword=', 'Search', site.img_search)
    List(site.url + '/videos/latest')


@site.register()
def List(url):
    page_html = fetch_html(url, site.url)
    if not page_html:
        utils.notify('8k Porner', 'Failed to load page')
        utils.eod()
        return

    items = []
    seen = set()
    
    blocks = re.split(r'(?=<div\b[^>]+class=["\'][^"\']*video-latest-list\s+video-wrapper[^"\']*["\'])', page_html, flags=re.I)
    
    for block in blocks[1:]:
        href_match = re.search(r'<a\b[^>]+href=["\']([^"\']*/watch/[^"\']+)["\']', block, re.I)
        if not href_match:
            continue
            
        vid_url = urllib.parse.urljoin(site.url, html.unescape(href_match.group(1)))
        if vid_url in seen:
            continue
        seen.add(vid_url)

        img_match = re.search(r'<img\b[^>]*>', block, re.I)
        img_tag = img_match.group(0) if img_match else ""
        
        title_match = re.search(r'\s(?:alt|title)=["\']([^"\']+)', img_tag, re.I)
        if not title_match:
            title_match = re.search(r'<h4\b[^>]*title=["\']([^"\']+)', block, re.I)
        
        title = html.unescape(title_match.group(1) if title_match else "").strip()
        if not title:
            continue

        thumb_match = re.search(r'\s(?:data-src|data-original|src)=["\']([^"\']+)', img_tag, re.I)
        thumb = urllib.parse.urljoin(site.url, thumb_match.group(1)) if thumb_match else site.image
        
        duration_match = re.search(r'class=["\'][^"\']*video-duration[^"\']*["\'][^>]*>([^<]+)', block, re.I)
        duration = html.unescape(duration_match.group(1) if duration_match else "").strip()
        
        site.add_download_link(title, vid_url, 'Playvid', thumb, title, duration=duration, stream=True)
        items.append(vid_url)
    
    if items:
        current_page = 1
        page_match = re.search(r'[?&]page_id=(\d+)', url)
        if page_match:
            current_page = int(page_match.group(1))
        
        if re.search(r'[?&]page_id={}\b'.format(current_page + 1), page_html):
            if '?' in url:
                next_url = re.sub(r'([?&])page_id=\d+', r'\1page_id=' + str(current_page + 1), url)
                if 'page_id=' not in next_url:
                    next_url += '&page_id=' + str(current_page + 1)
            else:
                next_url = url + '?page_id=' + str(current_page + 1)
                
            site.add_dir('[COLOR orange]Next Page[/COLOR]', next_url, 'List', site.img_next)
    
    utils.eod()


@site.register()
def Categories(url):
    """Page des categories"""
    process_directory(url, "/videos/category/", "category", "Categories")


@site.register()
def Pornstars(url):
    """Page des pornstars"""
    process_directory(url, "/videos/pornstar/", "pornstar", "Pornstars")


def process_directory(url, marker, dir_type, list_mode):
    """Affiche les categories ou pornstars avec pagination"""
    parsed = urllib.parse.urlparse(url)
    try:
        current_page = max(1, int(urllib.parse.parse_qs(parsed.query).get("page_id", [1])[0]))
    except (TypeError, ValueError):
        current_page = 1
    
    page_html = fetch_html(url)
    if not page_html:
        utils.notify('8k Porner', 'Failed to load ' + dir_type)
        utils.eod()
        return
    
    seen = set()
    count = 0
    
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', page_html, re.I | re.DOTALL):
        href = match.group(1)
        body = match.group(2)
        
        if marker not in href:
            continue
            
        target = urllib.parse.urljoin(site.url, html.unescape(href))
        if target in seen:
            continue
        seen.add(target)
        
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.I)
        thumb = urllib.parse.urljoin(site.url, img_match.group(1)) if img_match else site.image
        
        title = ""
        for pattern in [r'alt=["\']([^"\']+)["\']', r'title=["\']([^"\']+)["\']', r'>([^<]+)<']:
            title_match = re.search(pattern, body, re.I)
            if title_match:
                title = title_match.group(1).strip()
                break
        
        title = html.unescape(title).strip()
        
        if title:
            site.add_dir(title, target, 'List', thumb)
            count += 1
    
    if count > 0 and re.search(r'[?&]page_id={}\b'.format(current_page + 1), page_html):
        if '?' in url:
            next_url = re.sub(r'([?&])page_id=\d+', r'\1page_id=' + str(current_page + 1), url)
            if 'page_id=' not in next_url:
                next_url += '&page_id=' + str(current_page + 1)
        else:
            next_url = url + '?page_id=' + str(current_page + 1)
            
        site.add_dir('[COLOR orange]Next Page ({})[/COLOR]'.format(current_page + 1), 
                     next_url, list_mode, site.img_next)
    
    if count == 0:
        utils.notify('8k Porner', 'No ' + dir_type + ' found')
    
    utils.eod()


@site.register()
def Search(url=None, keyword=None):
    if not keyword:
        site.search_dir(site.url + '/search?keyword=', 'Search')
    else:
        search_url = site.url + '/search?keyword=' + urllib.parse.quote_plus(keyword.strip())
        List(search_url)


@site.register()
def Playvid(url, name, download=None):
    """Lecture avec ProxyController pour contourner les restrictions SSL sur les IPs CDN"""
    
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    page_html = fetch_html(url, site.url)
    if not page_html:
        utils.notify('Error', 'Failed to load video')
        vp.progress.close()
        return
    
    variants = []
    for source, label in re.findall(r'\{\s*["\']file["\']\s*:\s*["\']([^"\']+)["\']\s*,\s*["\']label["\']\s*:\s*["\']([^"\']+)["\']', page_html, re.I):
        source = html.unescape(source).replace("\\/", "/")
        quality = 2160 if label.upper() == "4K" else 1440 if label.upper() == "2K" else 0
        if not quality:
            q_match = re.search(r'(\d+)', label)
            quality = int(q_match.group(1)) if q_match else 0
        variants.append((quality, source))
    
    if not variants:
        utils.notify('Error', 'No video streams found')
        vp.progress.close()
        return
    
    variants.sort(key=lambda x: x[0], reverse=True)
    stream_url = variants[0][1]
    
    # Parse l'URL pour extraire les IPs CDN
    parsed = urllib.parse.urlsplit(stream_url)
    query_params = urllib.parse.parse_qs(parsed.query)
    cdn_ips = query_params.get('urls', [''])[0].split(';')
    
    # Prepare les headers
    stream_headers = {
        'User-Agent': HEADERS['User-Agent'],
        'Accept': '*/*',
    }
    
    # Si on a des IPs CDN, on utilise le ProxyController
    if cdn_ips and _is_ipv4(cdn_ips[0]):
        vp.progress.update(50, "[CR]Starting proxy for CDN...[CR]")
        
        # Remplace le hostname par l'IP CDN
        stream_headers['Host'] = parsed.netloc
        direct_url = urllib.parse.urlunsplit((
            parsed.scheme,
            cdn_ips[0],
            parsed.path,
            parsed.query,
            parsed.fragment
        ))
        
        # Demarre le proxy
        controller = ProxyController(direct_url, stream_headers)
        play_url = controller.start()
        
        if not play_url:
            vp.progress.close()
            utils.notify('Error', 'Failed to start proxy')
            return
        
        # Demarre le guard
        monitor = xbmc.Monitor()
        player = xbmc.Player()
        guard = PlaybackGuard(player, monitor, play_url, controller)
        guard.start()
        
        vp.progress.update(75, "[CR]Playing via proxy...[CR]")
        vp.progress.close()
        
        # Joue via le proxy local
        import xbmcplugin
        item = xbmcgui.ListItem(name, path=play_url)
        item.setProperty('IsPlayable', 'true')
        item.setMimeType('video/mp4')
        item.setContentLookup(False)
        
        if utils.KODIVER > 19.8:
            vtag = item.getVideoInfoTag()
            vtag.setTitle(name)
            vtag.setGenres(['Porn'])
        else:
            item.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        
    else:
        # Pas d'IP CDN, lecture normale
        play_url = stream_url + "|" + urllib.parse.urlencode(HEADERS)
        
        vp.progress.update(75, "[CR]Playing video[CR]")
        vp.play_from_direct_link(play_url)
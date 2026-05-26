
# -*- coding: utf-8 -*-
'''
    Cumination
    Copyright (C) 2017 Whitecream, hdgdl, Team Cumination
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

import os
import sqlite3
import json
import re
from six.moves import urllib_parse, urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse

site = AdultSite('bongacams', '[COLOR hotpink]BongaCams[/COLOR]', 'https://bongacams.com/', 'bongacams.png', 'bongacams', True)

@site.register(default_mode=True)
def Main():
    player = utils.addon.getSetting('bongaPlayer')

    if not player:
        utils.addon.setSetting('bongaPlayer', 'Playvid_Adaptive')
        player = 'Playvid_Adaptive'

    pretty_name = {
        'Playvid_Adaptive': 'Adaptive',
        'Playvid_proxy': 'Proxy',
        'Playvid_classic': 'Classic'
    }.get(player)
    site.add_download_link(
        u'Current player: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format(pretty_name),
        site.url,
        'Playvid_change',
        '',
        '',
        noDownload=True
    )

    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    site.add_dir('[COLOR red]Refresh bongacams.com images[/COLOR]', '', 'clean_database', '', Folder=False)
    site.add_dir('Hour\'s TOP chat rooms', 'https://bongacams.com/contest/top-room?cp=1', 'List2', '', '')
    bu = "http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]="
    if female:
        site.add_dir('[COLOR hotpink]Female[/COLOR]', '{0}female'.format(bu), 'List', '', '')
        site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', "http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json", 'onlineFav', '', '')
        site.add_dir('  International - Queen of Queens', site.url + 'contest/queen-of-queens-international', 'List3', '', '')
        site.add_dir('  North America & Western Europe\'s - Queen of Queens', site.url + 'contest/queen-of-queens', 'List3', '', '')
        site.add_dir('  Latin American - Queen of Queens', site.url + 'contest/queen-of-queens-latin-america', 'List3', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '{0}couples'.format(bu), 'List', '', '')
        site.add_dir('  Couples\' Top 50', site.url + 'contest/top-couple-models', 'List3', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male[/COLOR]', '{0}male'.format(bu), 'List', '', '')
        site.add_dir('  Guys and Trans\' Top 10', site.url + 'contest/top-male-models', 'List3', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '{0}transsexual'.format(bu), 'List', '', '')
        site.add_dir('  Guys and Trans\' Top 10', site.url + 'contest/top-male-models', 'List3', '', '')

    utils.eod()


@site.register()
def List(url):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    
    favorite = {}
    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT url FROM favorites WHERE mode='bongacams.Playvid'")
    favorite = [row[0] for row in c.fetchall()]
    c.close()

    data = utils._getHtml(url)
    model_list = json.loads(data)
    for model in model_list:
        if any(model['username'] in username for username in favorite):
            name = '[COLOR yellow]★ [/COLOR]'
            fav = 'del'
        else:
            name = ''
            fav = 'add'
        img = 'https:' + model['profile_images']['thumbnail_image_big_live']
        username = model['username']
        name += model['display_name']
        age = model['display_age']
        name += ' [COLOR hotpink][{}][/COLOR]'.format(age)
        if model['hd_cam']:
            name += ' [COLOR gold]HD[/COLOR]'
        subject = ''
        if model.get('is_geo'):
            subject += u'[B][COLOR hotpink]GeoLocked[/COLOR][/B]\n'
        if model.get('hometown'):
            subject += u'Location: {}'.format(model.get('hometown'))
        if model.get('homecountry'):
            subject += u', {}\n'.format(model.get('homecountry')) if subject else u'Location: {}\n'.format(model.get('homecountry'))
        if model['ethnicity']:
            subject += u'\n- {}\n'.format(model['ethnicity'])
        if model['primary_language']:
            subject += u'- Speaks {}\n'.format(model['primary_language'])
        if model['secondary_language']:
            subject = subject[:-1] + u', {}\n'.format(model['secondary_language'])
        if model['eye_color']:
            subject += u'- {} Eyed\n'.format(model['eye_color'])
        if model['hair_color']:
            subject = subject[:-1] + u' {}\n'.format(model['hair_color'])
        if model['height']:
            subject += u'- {} tall\n'.format(model['height'])
        if model['weight']:
            subject += u'- {} weight\n'.format(model['weight'])
        if model['bust_penis_size']:
            subject += u'- {} Boobs\n'.format(model['bust_penis_size']) if 'Female' in model['gender'] else u'- {} Cock\n'.format(model['bust_penis_size'])
        if model['pubic_hair']:
            subject = subject[:-1] + u' and {} Pubes\n'.format(model['pubic_hair'])
        if model['vibratoy']:
            subject += u'- Lovense Toy\n\n'
        if model['turns_on']:
            subject += u'- Likes: {}\n'.format(model['turns_on'])
        if model['turns_off']:
            subject += u'- Dislikes: {}\n\n'.format(model['turns_off'])
        if model.get('tags'):
            subject += u', '.join(model.get('tags'))
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(model['display_name']))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(model['display_name']), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, username, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, contextm=contextmenu, fav=fav, noDownload=True)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % "bongacams.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % "bongacams.com")
            if showdialog:
                utils.notify('Finished', 'bongacams.com images cleared')
    except:
        pass

@site.register()
def Playvid_change(url, name):
    import xbmc
    current = utils.addon.getSetting('bongaPlayer')

    if current == 'Playvid_Adaptive':
        utils.addon.setSetting('bongaPlayer', 'Playvid_proxy')
        utils.notify('Player switched', 'Now using Proxy mode')
    elif current == 'Playvid_proxy':
        utils.addon.setSetting('bongaPlayer', 'Playvid_classic')
        utils.notify('Player switched', 'Now using Classic mode')
    elif current == 'Playvid_classic':
        utils.addon.setSetting('bongaPlayer', 'Playvid_Adaptive')
        utils.notify('Player switched', 'Now using Adaptive mode')

    xbmc.executebuiltin('Container.Refresh')

@site.register()
def Playvid(url, name):
    if url == '':
        return
    player = utils.addon.getSetting('bongaPlayer')

    if player == 'Playvid_proxy':
        return Playvid_proxy(url, name)
    elif player == 'Playvid_Adaptive':
        return Playvid_Adaptive(url, name)
    elif player == 'Playvid_classic':
        return Playvid_classic(url, name)


#@site.register()
def Playvid_proxy(url, name):
    import json
    import time
    import threading
    import requests
    import xbmc
    import xbmcgui
    from http.server import BaseHTTPRequestHandler, HTTPServer

    try:
        postRequest = [
            ('method', 'getRoomData'),
            ('args[]', str(url)),
            ('args[]', ''),
            ('args[]', '')
        ]
        hdr = utils.base_hdrs
        hdr.update({'X-Requested-With': 'XMLHttpRequest'})
        response = utils._postHtml(
            f"{site.url}tools/amf.php",
            form_data=postRequest,
            headers=hdr,
            compression=False
        )
    except:
        utils.notify(name, "Nu pot obține datele camerei")
        return

    amf = json.loads(response)
    performer = amf.get("performerData", {})
    localdata = amf.get("localData", {})

    if not performer.get("isOnline"):
        utils.notify(name, "Model Offline")
        return

    username = performer.get("username")
    server = (
        localdata.get("videoServerUrl")
        or performer.get("videoServerUrl")
        or localdata.get("videoServerUrlHls")
        or localdata.get("videoServerUrlMobile")
    )

    if not server:
        utils.notify(name, "Nu pot obține serverul video")
        return

    server = server.replace("\\/", "/")
    if server.startswith("//"):
        server = "https:" + server

    # VIDEO
    base_video = f"{server}/hls/stream_{username}"

    # AUDIO
    base_audio = f"{server}/public-aac/stream_{username}"

    headers = {
        "User-Agent": utils.USER_AGENT,
        "Referer": site.url,
        "Origin": site.url[:-1]
    }

    def raw_get(url):
        try:
            r = requests.get(url, headers=headers, timeout=3, verify=False)
            if r.status_code == 200:
                return r.content
            return None
        except:
            return None

    # CACHE
    cache_ts = {}
    cache_m3u8 = {}

    TS_TTL = 45      # ★ crescut pentru stabilitate
    M3U8_TTL = 8     # ★ crescut pentru stabilitate
    MAX_TS = 40      # ★ păstrăm max 40 segmente în cache

    # ★ prefetch pentru următorul segment
    def prefetch_next(segment_name):
        try:
            base = f"{base_video}/{segment_name}"
            data = raw_get(base)
            if data:
                cache_ts[segment_name] = (time.time(), data)
        except:
            pass

    class BongaProxy(BaseHTTPRequestHandler):

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()

        def do_GET(self):
            now = time.time()

            if self.path.endswith("playlist.m3u8"):
                return self.serve_master(now)

            if "chunklist" in self.path and self.path.endswith(".m3u8"):
                return self.serve_child(now)

            if "chunks.m3u8" in self.path:
                return self.serve_audio_playlist(now)

            if self.path.endswith(".ts"):
                return self.serve_ts(now)

            self.send_error(404)

        def serve_master(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                    self.end_headers()
                    self.wfile.write(data)
                    return

            url = f"{base_video}/playlist.m3u8"
            raw = raw_get(url)
            if not raw:
                self.send_error(404)
                return

            text = raw.decode("utf-8")
            new_lines = []
            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            data = "\n".join(new_lines).encode("utf-8")
            cache_m3u8[self.path] = (now, data)

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(data)

        def serve_child(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                    self.end_headers()
                    self.wfile.write(data)
                    return

            url = f"{base_video}/{self.path.lstrip('/')}"
            raw = raw_get(url)
            if not raw:
                self.send_error(404)
                return

            text = raw.decode("utf-8")
            new_lines = []
            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            data = "\n".join(new_lines).encode("utf-8")
            cache_m3u8[self.path] = (now, data)

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(data)

        def serve_audio_playlist(self, now):
            url = f"{base_audio}/{self.path.split('/')[-1]}"
            raw = raw_get(url)
            if not raw:
                self.send_error(404)
                return

            text = raw.decode("utf-8")
            new_lines = []
            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            data = "\n".join(new_lines).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(data)

        def serve_ts(self, now):
            clean = self.path.split("?")[0]

            # CACHE HIT
            if clean in cache_ts:
                ts, data = cache_ts[clean]
                if now - ts < TS_TTL:
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp2t")
                    self.end_headers()
                    self.wfile.write(data)

                    # ★ prefetch următorul segment
                    next_seg = self._guess_next_segment(clean)
                    if next_seg:
                        threading.Thread(target=prefetch_next, args=(next_seg,), daemon=True).start()

                    return

            # FETCH VIDEO
            url = f"{base_video}/{clean.lstrip('/')}"
            data = raw_get(url)

            # AUDIO fallback
            if not data:
                url = f"{base_audio}/{clean.lstrip('/')}"
                data = raw_get(url)

            if not data:
                self.send_error(404)
                return

            cache_ts[clean] = (now, data)

            # ★ limităm cache-ul
            if len(cache_ts) > MAX_TS:
                cache_ts.pop(next(iter(cache_ts)))

            self.send_response(200)
            self.send_header("Content-Type", "video/mp2t")
            self.end_headers()
            self.wfile.write(data)

            # ★ prefetch următorul segment
            next_seg = self._guess_next_segment(clean)
            if next_seg:
                threading.Thread(target=prefetch_next, args=(next_seg,), daemon=True).start()

        # ★ funcție inteligentă pentru a ghici următorul segment
        def _guess_next_segment(self, seg):
            try:
                base, num = seg.rsplit("-", 1)
                num = num.replace(".ts", "")
                next_num = str(int(num) + 1)
                return f"{base}-{next_num}.ts"
            except:
                return None

    server = HTTPServer(("127.0.0.1", 0), BongaProxy)
    port = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()

    proxy_url = f"http://127.0.0.1:{port}/playlist.m3u8"

    li = xbmcgui.ListItem(name, path=proxy_url)
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")

    xbmc.Player().play(proxy_url, li)



def Playvid_proxy_(url, name):
    import json
    import time
    import threading
    import requests
    import xbmc
    import xbmcgui
    from http.server import BaseHTTPRequestHandler, HTTPServer

    try:
        postRequest = [
            ('method', 'getRoomData'),
            ('args[]', str(url)),
            ('args[]', ''),
            ('args[]', '')
        ]
        hdr = utils.base_hdrs
        hdr.update({'X-Requested-With': 'XMLHttpRequest'})
        response = utils._postHtml(
            f"{site.url}tools/amf.php",
            form_data=postRequest,
            headers=hdr,
            compression=False
        )
    except:
        utils.notify(name, "Nu pot obține datele camerei")
        return

    amf = json.loads(response)
    performer = amf.get("performerData", {})
    localdata = amf.get("localData", {})

    if not performer.get("isOnline"):
        utils.notify(name, "Model Offline")
        return

    username = performer.get("username")
    server = (
        localdata.get("videoServerUrl")
        or performer.get("videoServerUrl")
        or localdata.get("videoServerUrlHls")
        or localdata.get("videoServerUrlMobile")
    )

    if not server:
        utils.notify(name, "Nu pot obține serverul video")
        return

    server = server.replace("\\/", "/")
    if server.startswith("//"):
        server = "https:" + server

    # VIDEO
    base_video = f"{server}/hls/stream_{username}"

    # AUDIO
    base_audio = f"{server}/public-aac/stream_{username}"

    headers = {
        "User-Agent": utils.USER_AGENT,
        "Referer": site.url,
        "Origin": site.url[:-1]
    }

    def raw_get(url):
        try:
            r = requests.get(url, headers=headers, timeout=3, verify=False)
            if r.status_code == 200:
                return r.content
            return None
        except:
            return None

    # CACHE
    cache_ts = {}
    cache_m3u8 = {}
    TS_TTL = 30 # 45
    M3U8_TTL = 5    # 8

    class BongaProxy(BaseHTTPRequestHandler):

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()

        def do_GET(self):
            now = time.time()

            # MASTER VIDEO
            if self.path.endswith("playlist.m3u8"):
                return self.serve_master(now)

            # CHILD VIDEO
            if "chunklist" in self.path and self.path.endswith(".m3u8"):
                return self.serve_child(now)

            # AUDIO PLAYLIST
            if "chunks.m3u8" in self.path:
                return self.serve_audio_playlist(now)

            # SEGMENTE VIDEO/AUDIO
            if self.path.endswith(".ts"):
                return self.serve_ts(now)

            self.send_error(404)

        def serve_master(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                    self.end_headers()
                    self.wfile.write(data)
                    return

            url = f"{base_video}/playlist.m3u8"
            raw = raw_get(url)
            if not raw:
                self.send_error(404)
                return

            text = raw.decode("utf-8")
            new_lines = []
            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            data = "\n".join(new_lines).encode("utf-8")
            cache_m3u8[self.path] = (now, data)

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(data)

        def serve_child(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                    self.end_headers()
                    self.wfile.write(data)
                    return

            url = f"{base_video}/{self.path.lstrip('/')}"
            raw = raw_get(url)
            if not raw:
                self.send_error(404)
                return

            text = raw.decode("utf-8")
            new_lines = []
            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            data = "\n".join(new_lines).encode("utf-8")
            cache_m3u8[self.path] = (now, data)

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(data)

        def serve_audio_playlist(self, now):
            url = f"{base_audio}/{self.path.split('/')[-1]}"
            raw = raw_get(url)
            if not raw:
                self.send_error(404)
                return

            text = raw.decode("utf-8")
            new_lines = []
            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            data = "\n".join(new_lines).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(data)

        def serve_ts(self, now):
            clean = self.path.split("?")[0]

            if clean in cache_ts:
                ts, data = cache_ts[clean]
                if now - ts < TS_TTL:
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp2t")
                    self.end_headers()
                    self.wfile.write(data)
                    return

            # VIDEO
            url = f"{base_video}/{clean.lstrip('/')}"
            data = raw_get(url)

            # AUDIO fallback
            if not data:
                url = f"{base_audio}/{clean.lstrip('/')}"
                data = raw_get(url)

            if not data:
                self.send_error(404)
                return

            cache_ts[clean] = (now, data)

            self.send_response(200)
            self.send_header("Content-Type", "video/mp2t")
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("127.0.0.1", 0), BongaProxy)
    port = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()

    proxy_url = f"http://127.0.0.1:{port}/playlist.m3u8"

    li = xbmcgui.ListItem(name, path=proxy_url)
    li.setProperty("inputstream", "inputstream.adaptive")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")

    xbmc.Player().play(proxy_url, li)

def Playvid_Adaptive(url, name):
    if not url:
        utils.notify(name, 'Model Offline', icon='thumb')
        return

    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        postRequest = [
            ('method', 'getRoomData'),
            ('args[]', str(url)),
            ('args[]', ''),
            ('args[]', '')
        ]
        hdr = utils.base_hdrs
        hdr.update({'X-Requested-With': 'XMLHttpRequest'})
        response = utils._postHtml(
            '{0}tools/amf.php'.format(site.url),
            form_data=postRequest,
            headers=hdr,
            compression=False
        )
    except:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link', icon='thumb')
        return

    amf_json = json.loads(response)
    if amf_json.get('status') == 'error':
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link', icon='thumb')
        return

    if 'private' in amf_json.get('performerData', {}).get('showType'):
        utils.notify(name, 'Model in private chat', icon='thumb')
        vp.progress.close()
        return

    amf = amf_json.get('localData', {}).get('videoServerUrl')
    if amf is None:
        utils.notify(name, 'Model Offline', icon='thumb')
        vp.progress.close()
        return

    username = amf_json.get('performerData', {}).get('username')

    if amf.startswith("//mobile"):
        base = 'https:' + amf + '/hls/stream_' + username + '.m3u8'
    else:
        base = 'https:' + amf + '/hls/stream_' + username + '/playlist.m3u8'

    try:
        m3u8 = utils._getHtml(base, referer=site.url)
    except:
        utils.notify(name, 'Model Offline or GeoLocked', icon='thumb')
        vp.progress.close()
        return

    quals = re.findall(r'\d+x(\d+).+\n(.+)', m3u8)
    if quals:
        sources = {qual: urllib_parse.urljoin(base, vurl) for qual, vurl in quals}
        videourl = utils.selector(
            'Select quality',
            sources,
            setting_valid='qualityask',
            sort_by=lambda x: int(x.split('x')[-1]),
            reverse=True
        )
    else:
        videourl = base

    videourl += '|User-Agent={0}&Referer={1}&Origin={2}'.format(
        utils.USER_AGENT,
        site.url,
        site.url[:-1]
    )

    vp.progress.update(75, "[CR]Found Stream[CR]")

    import xbmcgui, xbmc
    import xbmcplugin

    li = xbmcgui.ListItem(name)
    li.setPath(videourl)

    li.setProperty('inputstream', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', 'hls')
    li.setProperty('inputstream.adaptive.stream_headers',
                'User-Agent={0}&Referer={1}&Origin={2}'.format(
                    utils.USER_AGENT, site.url, site.url[:-1]
                ))

    li.setMimeType('application/vnd.apple.mpegurl')
    li.setContentLookup(False)

    xbmc.Player().play(videourl, li)


#@site.register()
def Playvid_classic(url, name):
    if url is None or url == '':
        utils.notify(name, 'Model Offline', icon='thumb')
        return

    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        postRequest = [
            ('method', 'getRoomData'),
            ('args[]', str(url)),
            ('args[]', ''),
            ('args[]', '')
        ]
        hdr = utils.base_hdrs
        hdr.update({'X-Requested-With': 'XMLHttpRequest'})
        response = utils._postHtml('{0}tools/amf.php'.format(site.url), form_data=postRequest, headers=hdr, compression=False)
    except:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link', icon='thumb')
        return None

    amf_json = json.loads(response)
    if amf_json['status'] == 'error':
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link', icon='thumb')
        return
    # if amf_json.get('performerData', {}).get('is_Online') is None: 
    #     utils.notify(name, 'Model Offline', icon='thumb')
    #     return       

    if 'private' in amf_json.get('performerData', {}).get('showType'):
        utils.notify(name, 'Model in private chat', icon='thumb')
        vp.progress.close()
        return

    amf = amf_json.get('localData', {}).get('videoServerUrl')

    if amf is None:
        utils.notify(name, 'Model Offline', icon='thumb')
        vp.progress.close()
        return
    elif amf.startswith("//mobile"):
        videourl = 'https:' + amf + '/hls/stream_' + amf_json.get('performerData', {}).get('username') + '.m3u8'
    else:
        videourl = 'https:' + amf + '/hls/stream_' + amf_json.get('performerData', {}).get('username') + '/playlist.m3u8'
        try:
            m3u8 = utils._getHtml(videourl, referer=site.url)
        except:     # urllib_error.HTTPError:
            utils.notify(name, 'Model Offline or GeoLocked', icon='thumb')
            vp.progress.close()
            return
        quals = re.findall(r'\d+x(\d+).+\n(.+)', m3u8)
        if quals:
            sources = {qual: urllib_parse.urljoin(videourl, vurl) for qual, vurl in quals}
            videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x.split('x')[-1]), reverse=True)

    videourl += '|User-Agent={0}&Referer={1}&Origin={2}'.format(utils.USER_AGENT, site.url, site.url[:-1])
    vp.progress.update(75, "[CR]Found Stream[CR]")
    vp.play_from_direct_link(videourl)


@site.register()
def List2(url):
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    timePeriod = json.loads(data).get("data").get("topRooms").get("content").get("winners").get("timePeriod")

    site.add_download_link('Current contest standings: {} - [COLOR red][B]Refresh[/B][/COLOR]'.format(timePeriod), url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        online_only = True
        url = url + '?isOnlineOnly=on'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        online_only = False
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    items = (
        json.loads(data)
        .get("data", {})
        .get("topRooms", {})
        .get("content", {})
        .get("winners", {})
        .get("thumbs", [])
    )

    for item in items:
        is_live = item.get("liveBadge") is not None
        status = "Online" if is_live else "Offline"

        if online_only and status == "Offline":
            continue

        name = item.get("footer", {}).get("displayName", "")
        if utils.PY2 and name:
            name = name.encode("utf8")

        link_path = item.get("link", {}).get("url", {}).get("url", "")
        if status == "Online":
            username = link_path.strip("/") if link_path else ""
        else:
            username = " "

        img_src = item.get("avatar", {}).get("src", "")
        if img_src.startswith("//"):
            img = "https:" + img_src
        else:
            img = "https://" + img_src if img_src else ""

        place = item.get("stripe", {}).get("place", "")

        content_list = item.get("content", [])
        viewers = ""
        prize_formatted = ""

        for c in content_list:
            text_val = c.get("text", "")
            if "members" in text_val.lower():
                viewers = "".join(filter(str.isdigit, text_val))
            elif "prize" in text_val.lower():
                prize_formatted = text_val

        subject = "Status: {0}[CR]".format(status)
        subject += "Place: {0}[CR]".format(place)
        subject += "Viewers: {0}[CR]".format(viewers)
        subject += "Prize: {0}[CR]".format(prize_formatted)

        site.add_download_link(
            name, username, "Playvid", img, subject, noDownload=True
        )
    utils.eod()
  


@site.register()
def List3(url):
    site.add_download_link('[COLOR red][B]Refresh[/B][/COLOR]', url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        url = url + '?online_only=1'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    #timePeriod = json.loads(data).get("data").get("topModels").get("content").get("winners").get("thumbs", [])   #.get("content").get("winners").get("timePeriod")
    json_data = json.loads(data).get("data", {})

    top_winners_list = (
        json_data.get("topModels", {})
        .get("content", {})
        .get("topWinners", {})
        .get("thumbs", [])
    )

    winners_list = (
        json_data.get("topModels", {})
        .get("content", {})
        .get("winners", {})
        .get("thumbs", [])
    )

    items = top_winners_list + winners_list

    for item in items:
        is_live = item.get("liveBadge") is not None
        status = "Online" if is_live else "Offline"

        # if online_only and status == "Offline":
        #     continue

        name = item.get("footer", {}).get("displayName", "")
        if utils.PY2 and name:
            name = name.encode("utf8")

        link_path = item.get("link", {}).get("url", {}).get("url", "")
        if status == "Online":
            username = link_path.strip("/") if link_path else ""
        else:
            username = " "

        img_src = item.get("avatar", {}).get("src", "")
        if img_src.startswith("//"):
            img = "https:" + img_src
        else:
            img = "https://" + img_src if img_src else ""

        place = item.get("stripe", {}).get("place", "")

        content_list = item.get("content", [])
        viewers = ""
        prize_formatted = ""

        for c in content_list:
            text_val = c.get("text", "")
            if "members" in text_val.lower():
                viewers = "".join(filter(str.isdigit, text_val))
            elif "prize" in text_val.lower():
                prize_formatted = text_val

        subject = "Status: {0}[CR]".format(status)
        subject += "Place: {0}[CR]".format(place)
        subject += "Viewers: {0}[CR]".format(viewers)
        subject += "Prize: {0}[CR]".format(prize_formatted)

        site.add_download_link(
            name, username, "Playvid", img, subject, noDownload=True
        )
    utils.eod()



@site.register()
def online(url):
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()


@site.register()
def onlineFav(url):
    data = utils._getHtml(url)
    model_list = json.loads(data)

    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='bongacams.Playvid'")

    favorite_data = {}

    for row in c.fetchall():
        name_raw = row[0]
        name_clean = name_raw.split('[COLOR')[0].strip()

        favorite_data[name_clean] = {
            'name_clean': name_clean,
            'name_raw': name_raw,
            'db_url': row[1],
            'db_image': row[2]
        }

    c.close()

    model_lookup = {
        item['display_name']: item | favorite_data[item['display_name']]
        for item in model_list
        if item['display_name'] in favorite_data
    }

    for model_name, info in model_lookup.items():
        username = info['username']
        name = info['display_name']
        img = info['db_image']
        age = info['display_age']
        name += ' [COLOR hotpink][{}][/COLOR]'.format(age)
        if info['hd_cam']:
            name += ' [COLOR gold]HD[/COLOR]'
        subject = ''
        if info['is_geo']:
            subject += u'[B][COLOR hotpink]GeoLocked[/COLOR][/B]\n'
        if info['hometown']:
            subject += u'Location: {}'.format(info['hometown'])
        if info['homecountry']:
            subject += u', {}\n'.format(info['homecountry']) if subject else u'Location: {}\n'.format(info['homecountry'])
        if info['ethnicity']:
            subject += u'\n- {}\n'.format(info['ethnicity'])
        if info['primary_language']:
            subject += u'- Speaks {}\n'.format(info['primary_language'])
        if info['secondary_language']:
            subject = subject[:-1] + u', {}\n'.format(info['secondary_language'])
        if info['eye_color']:
            subject += u'- {} Eyed\n'.format(info['eye_color'])
        if info['hair_color']:
            subject = subject[:-1] + u' {}\n'.format(info['hair_color'])
        if info['height']:
            subject += u'- {} tall\n'.format(info['height'])
        if info['weight']:
            subject += u'- {} weight\n'.format(info['weight'])
        if info['bust_penis_size']:
            subject += u'- {} Boobs\n'.format(info['bust_penis_size']) if 'Female' in info['gender'] else u'- {} Cock\n'.format(info['bust_penis_size'])
        if info['pubic_hair']:
            subject = subject[:-1] + u' and {} Pubes\n'.format(info['pubic_hair'])
        if info['vibratoy']:
            subject += u'- Lovense Toy\n\n'
        if info['turns_on']:
            subject += u'- Likes: {}\n'.format(info['turns_on'])
        if info['turns_off']:
            subject += u'- Dislikes: {}\n\n'.format(info['turns_off'])
        chat_status = ''
        if info['chat_status']:
            if info['chat_status'] != 'public':
                current_show = '[COLOR blue] {}[/COLOR]'.format(info['chat_status'])

        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(username))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(name), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, username, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, contextm=contextmenu, fav='del', noDownload=True)
    model_off = {}

    for fav_name, fav_info in favorite_data.items():
        if fav_name not in model_lookup:
            model_off[fav_name] = {
                'display_name': fav_info['name_clean'],
                'display_name_raw': fav_info['name_raw'],
                'online': False,
                'db_url': fav_info['db_url'],
                'db_image': fav_info['db_image']
            }

    # Bucla pentru favoritele offline
    for model_name, info in model_off.items():
        name = info['display_name']
        name_raw = info['display_name_raw']
        img = info['db_image']
        url = info['db_url']
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(name))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(name), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name_raw + ' [COLOR yellow]Offline[/COLOR]', url, 'Playvid', img, "Offline", contextm=contextmenu, fav='del', noDownload=True)
    utils.eod()


'''
class BongaProxyHandler(BaseHTTPRequestHandler):
    upstream = None
    headers_map = None

    def do_GET(self):
        try:
            target = self.upstream + self.path
            data = utils._getHtml(target, headers=self.headers_map, referer=self.headers_map.get("Referer"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(data.encode('utf-8'))
        except Exception as e:
            utils.log(f"BONGA PROXY ERROR: {e}")
            self.send_response(404)
            self.end_headers()

def start_bonga_proxy(upstream, headers):
    # găsim un port liber
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    BongaProxyHandler.upstream = upstream
    BongaProxyHandler.headers_map = headers

    server = HTTPServer(('127.0.0.1', port), BongaProxyHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    return port
'''
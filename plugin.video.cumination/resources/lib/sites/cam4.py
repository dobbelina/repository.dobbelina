# -*- coding: utf-8 -*-
'''
    Cumination
    Copyright (C) 2016 Whitecream

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
from six.moves import urllib_parse, urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite

cj = utils.cj
site = AdultSite('cam4', '[COLOR hotpink]Cam4[/COLOR]', 'https://www.cam4.com/', 'cam4.png', 'cam4', True)
IOS_UA = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) '
                  'AppleWebKit/605.1.15 (KHTML%2C like Gecko) Mobile/15E148'
}
STREAM_INFO  = "{0}rest/v1.0/profile/{1}/streamInfo".format(site.url, 0)
INFO_URL     = "{0}rest/v1.0/search/performer/{1}".format(site.url, 0)
PROFILE_URL  = "{0}rest/v1.0/profile/{1}/info".format(site.url, 0)

addon = utils.addon
cam4logged = utils.addon.getSetting('cam4logged').lower() == 'true'


@site.register(default_mode=True)
def Main():
    global cam4logged

    player = utils.addon.getSetting('cam4player')
    if not player:
        utils.addon.setSetting('cam4player', 'Playvid_Adaptive')
        player = 'Playvid_Adaptive'
    pretty_name = {
        'Playvid_Adaptive': 'Adaptive',
        'Playvid_proxy': 'Proxy',
        'Playvid_classic': 'Classic'
    }.get(player)

    site.add_download_link(
        u'Current player: [COLOR fuchsia][B]{}[/B][/COLOR] - '
        u'[COLOR red][B]Change[/B][/COLOR]'.format(pretty_name),
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

    site.add_dir('[COLOR red]Refresh Cam4 images[/COLOR]', '', 'clean_database', '', Folder=False)

    if cam4logged:
        site.add_dir('[COLOR fuchsia]Followed Cams[/COLOR]', '', 'list_followed', '', 1)
        site.add_dir('[COLOR fuchsia]Logout[/COLOR]', '', 'logout', '', Folder=False)
    else:
        site.add_dir('[COLOR red]Login[/COLOR]', '', 'login', '', Folder=False)

    site.add_dir(
        '[COLOR yellow]Online Favorites[/COLOR]',
        '&gender=female&broadcastType=female_group&broadcastType=solo&broadcastType=male_female_group',
        'onlineFav',
        '',
        1
    )

    if female:
        site.add_dir(
            '[COLOR hotpink]Females[/COLOR]',
            '&gender=female&broadcastType=female_group&broadcastType=solo&broadcastType=male_female_group',
            'List',
            '',
            1
        )
    if couple:
        site.add_dir(
            '[COLOR hotpink]Couples[/COLOR]',
            '&broadcastType=male_group&broadcastType=female_group&broadcastType=male_female_group',
            'List',
            '',
            1
        )
    if male:
        site.add_dir(
            '[COLOR hotpink]Males[/COLOR]',
            '&gender=male&broadcastType=male_group&broadcastType=solo&broadcastType=male_female_group',
            'List',
            '',
            1
        )
    if trans:
        site.add_dir(
            '[COLOR hotpink]Transsexual[/COLOR]',
            '&gender=shemale',
            'List',
            '',
            1
        )

    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            rows = conn.execute(
                "SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".cam4s.com"
            )
            for row in rows:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".cam4.com")
            if showdialog:
                utils.notify('Finished', 'Cam4 images cleared')
    except:
        pass


@site.register()
def PerPage(url=None, name=None):
    vq = utils._get_keyboard(heading=utils.i18n('srch_for'))
    if not vq or not vq.isdigit():
        return False

    utils.addon.setSetting("cam4per_page", str(vq))
    import xbmc
    xbmc.executebuiltin('Container.Refresh')
    return True


@site.register()
def Playvid_change(url, name):
    import xbmc
    current = utils.addon.getSetting('cam4player')

    if current == 'Playvid_Adaptive':
        utils.addon.setSetting('cam4player', 'Playvid_proxy')
        utils.notify('Player switched', 'Now using Proxy mode')
    elif current == 'Playvid_proxy':
        utils.addon.setSetting('cam4player', 'Playvid_classic')
        utils.notify('Player switched', 'Now using Classic mode')
    elif current == 'Playvid_classic':
        utils.addon.setSetting('cam4player', 'Playvid_Adaptive')
        utils.notify('Player switched', 'Now using Adaptive mode')

    xbmc.executebuiltin('Container.Refresh')


@site.register()
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT url FROM favorites WHERE mode='cam4.Playvid'")
    favorite = [row[0] for row in c.fetchall()]
    c.close()

    perPage_setting = utils.addon.getSetting('cam4per_page')
    if perPage_setting and perPage_setting.strip() != "":
        perPage = int(perPage_setting)
    else:
        perPage = 60
        utils.addon.setSetting("cam4per_page", str(perPage))

    site.add_download_link(
        'Current models per page: [COLOR fuchsia][B]{}[/B][/COLOR] - '
        '[COLOR red][B]Change[/B][/COLOR]'.format(perPage),
        url,
        'PerPage',
        '',
        '',
        noDownload=True
    )

    cams_followed = followedCams() or []
    followed_set = {cam["username"] for cam in cams_followed}

    listurl = (
        '{0}/api/directoryCams?directoryJson=true&online=true&url=true&'
        'orderBy=VIDEO_QUALITY{1}&page={2}&resultsPerPage={3}'
    ).format(site.url, url, page, perPage)

    listhtml = utils._getHtml(listurl, headers=IOS_UA)
    cams = json.loads(listhtml).get('users', {})

    for cam in cams:
        name = ''
        username = cam.get('username')

        if cam4logged and username in followed_set:
            name += '[COLOR yellow]♥[/COLOR]'
            fav = 'del'
        elif any(username in fav_url for fav_url in favorite):
            name += u'[COLOR yellow]★ [/COLOR]'
            fav = 'del'
        else:
            fav = 'add'

        name += username

        age = cam.get('age')
        if age:
            name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)

        hd = ''
        if cam.get('hdStream'):
            hd = 'HD'

        img = cam.get('snapshotImageLink') or cam.get('defaultImageLink')

        subject = ''

        if cam.get('viewers'):
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(cam.get('viewers'))
        if cam.get('countryCode'):
            country = utils.get_country(cam.get('countryCode'))
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(country)
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, country)
        if cam.get('languages'):
            langs = [utils.get_language(lang) for lang in cam.get('languages')]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if cam.get('resolution'):
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(cam.get('resolution'))
        if cam.get('sexPreference'):
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(cam.get('sexPreference'))
        if cam.get('statusMessage'):
            msg = cam.get('statusMessage')
            subject += '[CR]{}[CR][CR]'.format(msg.encode('utf8') if utils.PY2 else msg)
        if cam.get('showTags'):
            tags = ', '.join(cam.get('showTags'))
            subject += tags.encode('utf8') if utils.PY2 else tags

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, username)

        context = []
        if username in followed_set:
            context.append((
                "Unfollow {}".format(username),
                "RunPlugin({}?mode=cam4.unfollow&model={})".format(
                    utils.addon_sys,
                    urllib_parse.quote_plus(username)
                )
            ))
        else:
            context.append((
                "Follow {}".format(username),
                "RunPlugin({}?mode=cam4.follow&model={})".format(
                    utils.addon_sys,
                    urllib_parse.quote_plus(username)
                )
            ))

        contextrecord = (
            utils.addon_sys +
            "?mode=chaturbate.Record&id=" +
            urllib_parse.quote_plus(username)
        )
        context.append((
            '[COLOR violet]Find recordings featuring [/COLOR]{}'.format(username),
            'RunPlugin(' + contextrecord + ')'
        ))

        site.add_download_link(
            name,
            video,
            'Playvid',
            img,
            subject,
            contextm=context,
            noDownload=True,
            fav=fav,
            quality=hd
        )

    if len(cams) == perPage:
        page += 1
        site.add_dir('Next Page ({})'.format(page), url, 'List', site.img_next, page)

    utils.eod()

@site.register()
def Playvid(url, name):
    player = utils.addon.getSetting('cam4player')

    if player == 'Playvid_proxy':
        return Playvid_proxy(url, name)
    elif player == 'Playvid_Adaptive':
        return Playvid_Adaptive(url, name)
    elif player == 'Playvid_classic':
        return Playvid_classic(url, name)


def Playvid_Adaptive(url, name):
    import json
    import xbmcgui
    import xbmc
    import sys

    PY2 = sys.version_info[0] == 2
    if PY2:
        from urllib import urlencode
    else:
        from urllib.parse import urlencode

    html = utils._getHtml(url)
    try:
        cdn_list = json.loads(html).get('cdnURL')
    except:
        utils.notify('Cam4', 'Cannot fetch CDN URL')
        return

    if not cdn_list:
        utils.notify('Cam4', 'The model is not broadcasting at this moment.')
        return

    if isinstance(cdn_list, list):
        cdn_urls = cdn_list
    else:
        cdn_urls = [cdn_list]

    headers = {
        'User-Agent': utils.USER_AGENT,
        'Referer': site.url,
        'Origin': site.url
    }

    header_str = urlencode(headers)
    final_url = None

    for cdn in cdn_urls:
        test_url = cdn + "|" + header_str
        if utils._getHtml(cdn, error='return'):
            final_url = test_url
            break

    if not final_url:
        utils.notify('Cam4', 'All CDNs failed')
        return

    li = xbmcgui.ListItem(name, path=final_url)
    li.setProperty('inputstream', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', 'hls')

    manifest_headers = (
        "User-Agent=%s&Referer=%s&Origin=%s" %
        (headers['User-Agent'], headers['Referer'], headers['Origin'])
    )

    li.setProperty('inputstream.adaptive.manifest_headers', manifest_headers)
    li.setProperty('inputstream.adaptive.stream_headers', manifest_headers)

    li.setProperty('http-user-agent', headers['User-Agent'])
    li.setProperty('http-referrer', headers['Referer'])

    xbmc.Player().play(final_url, li)


def Playvid_proxy(url, name):
    import json
    import xbmc
    import xbmcgui
    import threading
    import time
    import requests
    import sys

    PY2 = sys.version_info[0] == 2

    if PY2:
        import BaseHTTPServer as httpserver
        import SocketServer as socketserver
    else:
        from http.server import BaseHTTPRequestHandler as HTTPHandler
        from http.server import HTTPServer as HTTPServerBase
        import socketserver

    html = utils._getHtml(url)
    try:
        playlist_url = json.loads(html).get('cdnURL')
    except:
        utils.notify('Cam4', 'Cannot fetch CDN URL')
        return

    if not playlist_url:
        utils.notify('Cam4', 'The model is not broadcasting at this moment.')
        return

    if isinstance(playlist_url, list):
        playlist_url = playlist_url[0]

    base_url = playlist_url.rsplit('/', 1)[0]

    headers = {
        'User-Agent': utils.USER_AGENT,
        'Referer': site.url,
        'Origin': site.url
    }

    def raw_get(u):
        try:
            r = requests.get(u, headers=headers, timeout=3, verify=False)
            if r.status_code == 200:
                return r.content
            return None
        except:
            return None

    cache_ts = {}
    cache_m3u8 = {}

    TS_TTL = 40
    M3U8_TTL = 6
    MAX_TS = 30

    def prefetch_next(segment_url):
        try:
            raw_get(segment_url)
        except:
            pass

    class ProxyHandler(httpserver.BaseHTTPRequestHandler if PY2 else HTTPHandler):

        def log_message(self, *args):
            return

        def do_HEAD(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()

        def do_GET(self):
            try:
                now = time.time()
                p = self.path

                if p.endswith("playlist.m3u8"):
                    return self.serve_master(now)
                if "chunklist" in p and p.endswith(".m3u8"):
                    return self.serve_child(now)
                if "index.m3u8" in p:
                    return self.serve_subfolder(now)
                if p.endswith(".ts"):
                    return self.serve_ts(now)

                self.send_error(404)
            except:
                self.send_error(500)

        def serve_master(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    return self._send_m3u8(data)

            data_raw = raw_get(playlist_url)
            if not data_raw:
                return self.send_error(404)

            text = data_raw.decode('utf-8')
            new_lines = []

            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append("http://127.0.0.1:%d/%s" % (port, line))

            new_playlist = "\n".join(new_lines)
            data = new_playlist.encode('utf-8')

            cache_m3u8[self.path] = (now, data)
            return self._send_m3u8(data)

        def serve_child(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    return self._send_m3u8(data)

            child_url = "%s/%s" % (base_url, self.path.lstrip("/"))
            data_raw = raw_get(child_url)
            if not data_raw:
                return self.send_error(404)

            text = data_raw.decode('utf-8')
            new_lines = []

            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append("http://127.0.0.1:%d/%s" % (port, line))

            new_playlist = "\n".join(new_lines)
            data = new_playlist.encode('utf-8')

            cache_m3u8[self.path] = (now, data)
            return self._send_m3u8(data)

        def serve_subfolder(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    return self._send_m3u8(data)

            clean_path = self.path.split("?")[0].lstrip("/")
            subfolder = clean_path.split("/")[0]

            sub_url = "%s/%s" % (base_url, clean_path)
            data_raw = raw_get(sub_url)
            if not data_raw:
                return self.send_error(404)

            text = data_raw.decode('utf-8')
            new_lines = []

            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append("http://127.0.0.1:%d/%s/%s" % (port, subfolder, line))

            new_playlist = "\n".join(new_lines)
            data = new_playlist.encode('utf-8')

            cache_m3u8[self.path] = (now, data)
            return self._send_m3u8(data)

        def serve_ts(self, now):
            clean_path = self.path.split("?")[0]

            if clean_path in cache_ts:
                ts, data = cache_ts[clean_path]
                if now - ts < TS_TTL:
                    self._send_ts(data)
                    return

            segment_url = "%s/%s" % (base_url, clean_path.lstrip("/"))
            data = raw_get(segment_url)

            folder = clean_path.split("/")[1] if "/" in clean_path else ""
            base_name = clean_path.split("/")[-1].replace(".ts", "")

            if not data and folder:
                candidates = [
                    "%s/%s/%s.ts" % (base_url, folder, base_name),
                    "%s/%s/seg-1-v1-a1.ts" % (base_url, folder),
                    "%s/%s/video_00001.ts" % (base_url, folder),
                ]
                for cand in candidates:
                    data = raw_get(cand)
                    if data:
                        break

            if not data:
                return self.send_error(404)

            cache_ts[clean_path] = (now, data)

            if len(cache_ts) > MAX_TS:
                oldest = sorted(cache_ts.items(), key=lambda x: x[1][0])[0][0]
                del cache_ts[oldest]

            try:
                num = int(base_name.split("-")[-1])
                next_name = base_name.replace(str(num), str(num + 1))
                next_url = "%s/%s/%s.ts" % (base_url, folder, next_name)
                threading.Thread(target=prefetch_next, args=(next_url,)).start()
            except:
                pass

            return self._send_ts(data)

        def _send_m3u8(self, data):
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()
            self.wfile.write(data)

        def _send_ts(self, data):
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp2t')
            self.end_headers()
            self.wfile.write(data)

    class ThreadedHTTPServer(socketserver.ThreadingMixIn,
                             httpserver.HTTPServer if PY2 else HTTPServerBase):
        daemon_threads = True

    server = ThreadedHTTPServer(('127.0.0.1', 0), ProxyHandler)
    port = server.server_port

    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True)
    t.start()

    proxy_url = "http://127.0.0.1:%d/playlist.m3u8" % port

    li = xbmcgui.ListItem(name, path=proxy_url)
    li.setProperty('inputstream', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', 'hls')

    xbmc.Player().play(proxy_url, li)


def Playvid_classic(url, name):
    vp = utils.VideoPlayer(name)
    html = utils._getHtml(url)
    video = json.loads(html).get('cdnURL')
    vp.play_from_direct_link(video)

@site.register()
def onlineFav(url):
    listurl = (
        '{0}/api/directoryCams?directoryJson=true&online=true&url=true&'
        'orderBy=VIDEO_QUALITY{1}'.format(site.url, url)
    )
    data = utils._getHtml(listurl)
    model_list = json.loads(data).get('users', {})

    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='cam4.Playvid'")
    favorite_data = {
        row[0].split('[COLOR')[0].strip(): {'db_url': row[1], 'db_image': row[2]}
        for row in c.fetchall()
    }
    c.close()

    model_lookup = {
        item['username']: dict(item, **favorite_data[item['username']])
        for item in model_list
        if item['username'] in favorite_data
    }

    for model_name, info in model_lookup.items():
        username = info['username']
        name = info['username']
        age = info.get('age')
        if age:
            name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)

        hd = ''
        if info.get('hdStream'):
            hd = 'HD'

        img = info.get('snapshotImageLink') or info.get('defaultImageLink')

        subject = ''

        if info.get('viewers'):
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(info['viewers'])
        if info.get('countryCode'):
            country = utils.get_country(info['countryCode'])
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(country)
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, country)
        if info.get('languages'):
            langs = [utils.get_language(lang) for lang in info['languages']]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if info.get('resolution'):
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(info['resolution'])
        if info.get('sexPreference'):
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(info['sexPreference'])
        if info.get('statusMessage'):
            msg = info['statusMessage']
            subject += '[CR]{}[CR][CR]'.format(msg.encode('utf8') if utils.PY2 else msg)
        if info.get('showTags'):
            tags = ', '.join(info['showTags'])
            subject += tags.encode('utf8') if utils.PY2 else tags

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, username)
        contextrecord = (
            utils.addon_sys +
            "?mode=chaturbate.Record&id=" +
            urllib_parse.quote_plus(username)
        )
        contextmenu = [(
            '[COLOR violet]Find recordings featuring [/COLOR]{}'
            '[COLOR violet] on Cloudbate[/COLOR]'.format(username),
            'RunPlugin(' + contextrecord + ')'
        )]

        site.add_download_link(
            name,
            video,
            'Playvid',
            img,
            subject.encode('utf-8') if utils.PY2 else subject,
            contextm=contextmenu,
            noDownload=True,
            quality=hd,
            fav='del'
        )

    utils.eod()


def get_cookie():
    domain = ".cam4.com"
    cookiestr = ""
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'cam4_SESSION_ID':
            cookiestr = cookie.value
            break
    return cookiestr


@site.register()
def login():
    import json
    global cam4logged

    sessionid = utils.addon.getSetting('cam4_sessionid')
    if sessionid:
        session_cookie = get_cookie()
        if sessionid == session_cookie:
            utils.addon.setSetting('cam4logged', 'true')
            cam4logged = True
            return True

        if sessionid not in session_cookie:
            cookie_structure = {
                'solution': {
                    "cookies": [{
                        'name': "cam4_SESSION_ID",
                        'domain': ".cam4.com",
                        'value': sessionid,
                        'path': '/',
                        'secure': True,
                        'expiry': None,
                        'httpOnly': True
                    }],
                    "userAgent": utils.USER_AGENT
                }
            }
            utils.savecookies(cookie_structure)
            utils.addon.setSetting('cam4logged', 'true')
            cam4logged = True
            utils.refresh()
            return True

    cam4user = utils.addon.getSetting('cam4user') or ''
    cam4pass = utils.addon.getSetting('cam4pass') or ''

    if not cam4user:
        cam4user = utils._get_keyboard(default=cam4user, heading='Input your Cam4 email')
        if not cam4user:
            return False

        cam4pass = utils._get_keyboard(default=cam4pass, heading='Input your Cam4 password', hidden=True)
        if not cam4pass:
            return False

    login_url = '{}rest/v2.0/login/email'.format(site.url)

    payload_dict = {
        "password": cam4pass,
        "email": cam4user
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": site.url,
        "Referer": site.url,
        "User-Agent": utils.USER_AGENT
    }

    try:
        response_html = utils._postHtml(login_url, json_data=payload_dict, headers=headers)
        response_json = json.loads(response_html)

        cam4_display_name = response_json.get('username')
        if not cam4_display_name and 'user' in response_json:
            cam4_display_name = response_json['user'].get('username')
        if not cam4_display_name:
            cam4_display_name = "Utilizator"
        utils.addon.setSetting('cam4_display_name', cam4_display_name)

        if 'accessHash' in response_json:
            utils.addon.setSetting('cam4_accesshash', response_json['accessHash'])
        elif 'user' in response_json and 'accessHash' in response_json['user']:
            utils.addon.setSetting('cam4_accesshash', response_json['user']['accessHash'])

        if 'user' in response_json and 'id' in response_json['user']:
            utils.addon.setSetting('cam4_userid', str(response_json['user']['id']))

        if 'username' in response_json:
            utils.addon.setSetting('cam4_username', response_json['username'])
        elif 'user' in response_json and 'username' in response_json['user']:
            utils.addon.setSetting('cam4_username', response_json['user']['username'])

        new_session_id = get_cookie()

        cam4_ah = get_cam4_AH()
        if cam4_ah:
            utils.addon.setSetting('cam4_ah', cam4_ah)

        if new_session_id:
            utils.notify('Cam4', u'Autentificare reușită pentru {}'.format(cam4_display_name))
            utils.addon.setSetting('cam4_sessionid', new_session_id)
            utils.addon.setSetting('cam4logged', 'true')
            utils.addon.setSetting('cam4user', cam4user)
            utils.addon.setSetting('cam4pass', cam4pass)

            cam4logged = True

            cookie_structure = {
                'solution': {
                    "cookies": [{
                        'name': "cam4_SESSION_ID",
                        'domain': ".cam4.com",
                        'value': new_session_id,
                        'path': '/',
                        'secure': True,
                        'expiry': None,
                        'httpOnly': True
                    }],
                    "userAgent": utils.USER_AGENT
                }
            }
            utils.savecookies(cookie_structure)
            utils.refresh()
            return True

    except Exception as e:
        print("Error on utils._postHtml for Login Cam4: {e}".format(e=e))
        utils.notify('Cam4', 'Eroare la autentificare')

    utils.addon.setSetting('cam4logged', 'false')
    cam4logged = False
    return False


@site.register()
def logout():
    logout_url = '{}rest/v2.0/login/logout'.format(site.url)

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": site.url,
        "Referer": site.url,
        "User-Agent": utils.USER_AGENT
    }

    try:
        utils._postHtml(logout_url, headers=headers)
        utils.notify('Cam4', u'It looks like your session ended successfully.')
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear == 'Yes':
            utils.addon.setSetting('cam4user', '')
            utils.addon.setSetting('cam4pass', '')
        utils.addon.setSetting('cam4_sessionid', '')
        utils.addon.setSetting('cam4logged', 'false')
        global cam4logged
        cam4logged = False

        utils.refresh()
        return True

    except Exception as e:
        print("Error on utils._postHtml for Logout Cam4: {e}".format(e=e))
        return False

@site.register()
def followedCams():
    import json
    import xbmc

    username = utils.addon.getSetting('cam4_display_name')
    accessHash = utils.addon.getSetting('cam4_accesshash')

    if not username or not accessHash:
        if not login():
            utils.notify("Cam4", "Authentication failed!")
            return []
        username = utils.addon.getSetting('cam4_display_name')
        accessHash = utils.addon.getSetting('cam4_accesshash')

    url = (
        "https://api.cam4.com/webchat/requestChatlessPresenceInformation"
        "?username={username}"
        "&accessHash={accessHash}"
        "&online=true"
        "&agent=flash"
        "&type=favorites"
    ).format(username=username, accessHash=accessHash)

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": site.url,
        "Referer": site.url,
        "User-Agent": utils.USER_AGENT
    }

    response = utils._getHtml(url, headers=headers)
    low = response.lower()
    if "unauthorized" in low or "login" in low:
        if login():
            response = utils._getHtml(url, headers=headers)
        else:
            utils.notify("Cam4", "Authentication needed")
            return []

    try:
        data = json.loads(response)
    except Exception as e:
        xbmc.log("followedCams JSON error: %s" % e, xbmc.LOGERROR)
        return []

    return data.get("users", [])


@site.register()
def list_followed():
    import json

    cams = followedCams()
    if not cams:
        utils.notify("Cam4", "No followed cams are online")
        utils.eod()
        return

    listurl = (
        '{0}/api/directoryCams?directoryJson=true&online=true&url=true&'
        'orderBy=VIDEO_QUALITY'.format(site.url)
    )
    listhtml = utils._getHtml(listurl, headers=IOS_UA)
    all_cams = json.loads(listhtml).get('users', {})

    favorite_set = {cam["username"] for cam in cams}
    filtered_cams = [cam for cam in all_cams if cam.get("username") in favorite_set]

    for cam in filtered_cams:
        username = cam.get('username')
        name = "[COLOR yellow]♥[/COLOR] {0}".format(username)

        age = cam.get('age')
        if age:
            name += ' [COLOR deeppink][{}][/COLOR]'.format(age)

        hd = ''
        if cam.get('hdStream'):
            hd = 'HD'

        img = cam.get('snapshotImageLink') or cam.get('defaultImageLink')

        subject = ''

        if cam.get('viewers'):
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(cam.get('viewers'))
        if cam.get('countryCode'):
            country = utils.get_country(cam.get('countryCode'))
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(country)
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, country)
        if cam.get('languages'):
            langs = [utils.get_language(lang) for lang in cam.get('languages')]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if cam.get('resolution'):
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(cam.get('resolution'))
        if cam.get('sexPreference'):
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(cam.get('sexPreference'))
        if cam.get('statusMessage'):
            msg = cam.get('statusMessage')
            subject += '[CR]{}[CR][CR]'.format(msg.encode('utf8') if utils.PY2 else msg)
        if cam.get('showTags'):
            tags = ', '.join(cam.get('showTags'))
            subject += tags.encode('utf8') if utils.PY2 else tags

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, username)
        contextrecord = (
            utils.addon_sys +
            "?mode=chaturbate.Record&id=" +
            urllib_parse.quote_plus(username)
        )
        contextmenu = [(
            '[COLOR violet]Find recordings featuring [/COLOR]{}'
            '[COLOR violet] on Cloudbate[/COLOR]'.format(username),
            'RunPlugin(' + contextrecord + ')'
        )]

        site.add_download_link(
            name,
            video,
            'Playvid',
            img,
            subject,
            contextm=contextmenu,
            noDownload=True,
            quality=hd,
            fav='del'
        )

    utils.eod()


@site.register()
def list_offline():
    import json

    username = utils.addon.getSetting("cam4_username")
    base = site.url.rstrip('/')
    url = "{base}/rest/v1.0/favorites/{username}?offset=0&limit=1000".format(
        base=base,
        username=username
    )

    favs_json = utils._getHtml(url, headers={"User-Agent": utils.USER_AGENT})
    data = json.loads(favs_json)

    favs = data.get("usersList", [])
    all_fav_names = {f["username"] for f in favs}

    online = followedCams()
    online_names = {cam["username"] for cam in online}

    offline_names = sorted(all_fav_names - online_names)
    offline_cams = [f for f in favs if f["username"] in offline_names]

    for cam in offline_cams:
        name = cam.get("username")
        display = "[COLOR gray]★ {name}[/COLOR]".format(name=name)
        img = cam.get("profileThumbnailUrl") or "{base}/images/placeholder_offline.png".format(base=base)
        subject = "[COLOR gray]Offline[/COLOR]"

        site.add_download_link(display, "", "", img, subject, noDownload=True)

    utils.eod()


@site.register()
def follow(model):
    import requests

    username = utils.addon.getSetting("cam4_username")
    if not username:
        utils.notify("Cam4", "You don't have a Cam4 username")
        return

    base = site.url.rstrip('/')
    url = "{base}/rest/v1.0/favorites/{username}/{model}".format(
        base=base,
        username=username,
        model=model
    )

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=utf-8",
        "Origin": base,
        "Referer": "{base}/{model}".format(base=base, model=model),
        "User-Agent": utils.USER_AGENT,
        "DNT": "1"
    }

    session_id = get_cam4_SESSION_ID()
    ah_token = get_cam4_AH()

    if not session_id or not ah_token:
        utils.notify("Cam4", "Missing cookies (login required)")
        return

    cookies = {
        "cam4_SESSION_ID": session_id,
        "cam4-AH": ah_token
    }

    try:
        r = requests.post(url, headers=headers, cookies=cookies, data="")
        if r.status_code == 200:
            utils.notify("Cam4", "{model} followed".format(model=model))
        else:
            utils.notify("Cam4", "Error {code} on follow".format(code=r.status_code))
    except Exception as e:
        utils.notify("Cam4", "Error: {e}".format(e=e))


@site.register()
def unfollow(model):
    import requests

    username = utils.addon.getSetting("cam4_username")
    if not username:
        utils.notify("Cam4", "You don't have a Cam4 username")
        return

    base = site.url.rstrip('/')
    url = "{base}/rest/v1.0/favorites/{username}/{model}".format(
        base=base,
        username=username,
        model=model
    )

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=utf-8",
        "Origin": base,
        "Referer": "{base}/{model}".format(base=base, model=model),
        "User-Agent": utils.USER_AGENT,
        "DNT": "1"
    }

    session_id = get_cam4_SESSION_ID()
    ah_token = get_cam4_AH()

    if not session_id or not ah_token:
        utils.notify("Cam4", "Missing cookies (login required)")
        return

    cookies = {
        "cam4_SESSION_ID": session_id,
        "cam4-AH": ah_token
    }

    try:
        r = requests.delete(url, headers=headers, cookies=cookies)
        if r.status_code == 200:
            utils.notify("Cam4", "{model} unfollowed".format(model=model))
        else:
            utils.notify("Cam4", "Error {code} on unfollow".format(code=r.status_code))
    except Exception as e:
        utils.notify("Cam4", "Error: {e}".format(e=e))


def get_cam4_SESSION_ID():
    for c in cj:
        if c.name == "cam4_SESSION_ID":
            return c.value
    return ""


def get_cam4_AH():
    for c in cj:
        if c.name == "cam4-AH":
            return c.value
    return ""

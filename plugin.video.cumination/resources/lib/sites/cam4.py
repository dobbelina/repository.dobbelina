
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
from resources.lib import utils

cj = utils.cj
site = AdultSite('cam4', '[COLOR hotpink]Cam4[/COLOR]', 'https://www.cam4.com/', 'cam4.png', 'cam4', True)
IOS_UA = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML%2C like Gecko) Mobile/15E148'}
STREAM_INFO =   f"{site.url}rest/v1.0/profile/{0}/streamInfo"
INFO_URL =      f"{site.url}rest/v1.0/search/performer/{0}"
PROFILE_URL =   f"{site.url}rest/v1.0/profile/{0}/info"

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
        u'Current player: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format(pretty_name),
        site.url,
        'Playvid_change',
        '',
        '',
        noDownload=True
    )    
    female = True if utils.addon.getSetting("chatfemale") == "true" else False
    male = True if utils.addon.getSetting("chatmale") == "true" else False
    couple = True if utils.addon.getSetting("chatcouple") == "true" else False
    trans = True if utils.addon.getSetting("chattrans") == "true" else False
    site.add_dir('[COLOR red]Refresh Cam4 images[/COLOR]', '', 'clean_database', '', Folder=False)
    if cam4logged:
        site.add_dir('[COLOR fuchsia]Followed Cams[/COLOR]', '', 'list_followed', '', 1)
        site.add_dir('[COLOR fuchsia]Logout[/COLOR]', '', 'logout', '', Folder=False)
    else:
        site.add_dir('[COLOR red]Login[/COLOR]', '', 'login', '', Folder=False)


    site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', '&gender=female&broadcastType=female_group&broadcastType=solo&broadcastType=male_female_group', 'onlineFav', '', 1)
    if female:
        site.add_dir('[COLOR hotpink]Females[/COLOR]', '&gender=female&broadcastType=female_group&broadcastType=solo&broadcastType=male_female_group', 'List', '', 1)
    if couple:
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '&broadcastType=male_group&broadcastType=female_group&broadcastType=male_female_group', 'List', '', 1)
    if male:
        site.add_dir('[COLOR hotpink]Males[/COLOR]', '&gender=male&broadcastType=male_group&broadcastType=solo&broadcastType=male_female_group', 'List', '', 1)
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '&gender=shemale', 'List', '', 1)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".cam4s.com")
            for row in list:
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
    favorite = {}
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
        'Current models per page: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Refresh[/B][/COLOR]'.format(perPage), 
        url, 
        'PerPage', 
        '', 
        '', 
        noDownload=True
    )

    cams = followedCams() or []
    followed_set = {cam["username"] for cam in cams}

    listurl = '{0}/api/directoryCams?directoryJson=true&online=true&url=true&orderBy=VIDEO_QUALITY{1}&page={2}&resultsPerPage={3}'.format(site.url, url, page, perPage)
    listhtml = utils._getHtml(listurl, headers=IOS_UA)
    cams = json.loads(listhtml).get('users', {})
    for cam in cams:
        name = ''
        if cam4logged and cam.get('username') in followed_set:
            name += '[COLOR yellow]♥[/COLOR]'
            fav = 'del'
        if any(cam['username'] in username for username in favorite):
            name += u'[COLOR yellow]★ [/COLOR]'
            fav = 'del'
        else:
            name = ''
            fav = 'add'
        username = cam.get('username')
        name += cam.get('username')
        age = cam.get('age')
        if age:
            name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)
        hd = ''
        if cam.get('hdStream'):
            # name = '{0} [COLOR limegreen][HD][/COLOR]'.format(name)
            hd = 'HD'
        img = cam.get('snapshotImageLink')
        if not img:
            img = cam.get('defaultImageLink')

        subject = ''

        if cam.get('viewers'):
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(cam.get('viewers'))
        if cam.get('countryCode'):
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(utils.get_country(cam.get('countryCode')))
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, utils.get_country(cam.get('countryCode')))
        if cam.get('languages'):
            langs = [utils.get_language(lang) for lang in cam.get('languages')]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if cam.get('resolution'):
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(cam.get('resolution'))
        if cam.get('sexPreference'):
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(cam.get('sexPreference'))
        if cam.get('statusMessage'):
            subject += '[CR]{}[CR][CR]'.format(cam.get('statusMessage').encode('utf8') if utils.PY2 else cam.get('statusMessage'))
        if cam.get('showTags'):
            subject += ', '.join(cam.get('showTags')).encode('utf8') if utils.PY2 else ', '.join(cam.get('showTags'))

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, cam.get('username'))
        context = []
        if username in followed_set:
            context.append((
                "Unfollow {}".format(username),
                f"RunPlugin({utils.addon_sys}?mode=cam4.unfollow&model={urllib_parse.quote_plus(username)})"
            ))
        else:
            context.append((
                "Follow {}".format(username),
                f"RunPlugin({utils.addon_sys}?mode=cam4.follow&model={urllib_parse.quote_plus(username)})"
            ))
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(cam.get('username')))
        context.append((('[COLOR violet]Find recordings featuring [/COLOR]{}'.format(cam.get('username')), 'RunPlugin(' + contextrecord + ')')))
        site.add_download_link(name, video, 'Playvid', img, subject, contextm=context, noDownload=True, fav=fav,quality=hd)

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
    import urllib.parse
    import xbmcgui
    import xbmc

    html = utils._getHtml(url)
    try:
        cdn_list = json.loads(html).get('cdnURL')
    except:
        utils.notify('Cam4', 'Cannot fetch CDN Url')
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

    final_url = None
    for cdn in cdn_urls:
        test_url = cdn + '|' + urllib.parse.urlencode(headers)
        if utils._getHtml(cdn, error='return'):  # test rapid
            final_url = test_url
            break

    if not final_url:
        utils.notify('Cam4', 'All CDNs failed')
        return

    li = xbmcgui.ListItem(name, path=final_url)

    li.setProperty('inputstream', 'inputstream.adaptive')
    li.setProperty('inputstream.adaptive.manifest_type', 'hls')

    manifest_headers = (
        f"User-Agent={headers['User-Agent']}&"
        f"Referer={headers['Referer']}&"
        f"Origin={headers['Origin']}"
    )

    li.setProperty('inputstream.adaptive.manifest_headers', manifest_headers)
    li.setProperty('inputstream.adaptive.stream_headers', manifest_headers)

    li.setProperty('http-user-agent', headers['User-Agent'])
    li.setProperty('http-referrer', headers['Referer'])

    xbmc.Player().play(final_url, li)


#@site.register()
def Playvid_proxy(url, name):
    import json
    import urllib.parse
    import xbmc
    import xbmcgui
    import threading
    import time
    import requests
    from http.server import BaseHTTPRequestHandler, HTTPServer
    html = utils._getHtml(url)
    try:
        playlist_url = json.loads(html).get('cdnURL')
    except:
        utils.notify('Cam4', 'Nu pot obține CDN URL')
        return

    if not playlist_url:
        utils.notify('Cam4', 'Modelul nu transmite în acest moment')
        return

    if isinstance(playlist_url, list):
        playlist_url = playlist_url[0]

    base_url = playlist_url.rsplit('/', 1)[0]

    headers = {
        'User-Agent': utils.USER_AGENT,
        'Referer': site.url,
        'Origin': site.url
    }

    def raw_get(url):
        try:
            r = requests.get(url, headers=headers, timeout=3, verify=False)
            if r.status_code == 200:
                return r.content
            return None
        except:
            return None

    cache_ts = {}
    cache_m3u8 = {}

    TS_TTL = 10       # segmente .ts sunt valabile ~10 secunde
    M3U8_TTL = 2      # playlist-urile se schimbă rapid

    class Cam4Proxy(BaseHTTPRequestHandler):

        def do_HEAD(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()

        def do_GET(self):
            try:
                now = time.time()

                if self.path.endswith("playlist.m3u8"):
                    return self.serve_master_playlist(now)

                if "chunklist" in self.path and self.path.endswith(".m3u8"):
                    return self.serve_child_playlist(now)

                if "index.m3u8" in self.path:
                    return self.serve_subfolder_playlist(now)

                if self.path.endswith(".ts"):
                    return self.serve_ts(now)

                self.send_error(404)

            except:
                self.send_error(500)

        def serve_master_playlist(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                    self.end_headers()
                    self.wfile.write(data)
                    return

            data_raw = raw_get(playlist_url)
            if not data_raw:
                self.send_error(404)
                return

            text = data_raw.decode('utf-8')
            new_lines = []

            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            new_playlist = "\n".join(new_lines).encode('utf-8')
            cache_m3u8[self.path] = (now, new_playlist)

            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()
            self.wfile.write(new_playlist)

        def serve_child_playlist(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                    self.end_headers()
                    self.wfile.write(data)
                    return

            child_url = f"{base_url}/{self.path.lstrip('/')}"
            data_raw = raw_get(child_url)
            if not data_raw:
                self.send_error(404)
                return

            text = data_raw.decode('utf-8')
            new_lines = []

            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    new_lines.append(f"http://127.0.0.1:{port}/{line}")

            new_playlist = "\n".join(new_lines).encode('utf-8')
            cache_m3u8[self.path] = (now, new_playlist)

            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()
            self.wfile.write(new_playlist)

        def serve_subfolder_playlist(self, now):
            if self.path in cache_m3u8:
                ts, data = cache_m3u8[self.path]
                if now - ts < M3U8_TTL:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                    self.end_headers()
                    self.wfile.write(data)
                    return

            # ex: /0_2/index.m3u8?tkn=0
            subfolder = self.path.split("/")[1].split("/")[0]
            clean_path = self.path.split("?")[0].lstrip("/")
            sub_url = f"{base_url}/{clean_path}"

            data_raw = raw_get(sub_url)
            if not data_raw:
                self.send_error(404)
                return

            text = data_raw.decode('utf-8')
            new_lines = []

            for line in text.splitlines():
                if line.startswith("#"):
                    new_lines.append(line)
                else:
                    # ex: seg-1-v1-a1.ts
                    new_lines.append(f"http://127.0.0.1:{port}/{subfolder}/{line}")

            new_playlist = "\n".join(new_lines).encode('utf-8')
            cache_m3u8[self.path] = (now, new_playlist)

            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
            self.end_headers()
            self.wfile.write(new_playlist)

        def serve_ts(self, now):
            clean_path = self.path.split("?")[0]

            if clean_path in cache_ts:
                ts, data = cache_ts[clean_path]
                if now - ts < TS_TTL:
                    self.send_response(200)
                    self.send_header('Content-Type', 'video/mp2t')
                    self.end_headers()
                    self.wfile.write(data)
                    return

            segment_url = f"{base_url}/{clean_path.lstrip('/')}"
            data = raw_get(segment_url)

            if not data:
                folder = clean_path.split("/")[1]  # ex: 0_2
                base_name = clean_path.split("/")[-1].replace(".ts", "")

                candidates = [
                    f"{base_url}/{folder}/seg-1-v1-a1.ts",
                    f"{base_url}/{folder}/video_00001.ts",
                    f"{base_url}/{folder}/{base_name}.ts",
                ]

                for cand in candidates:
                    data = raw_get(cand)
                    if data:
                        break

            if not data:
                self.send_error(404)
                return

            cache_ts[clean_path] = (now, data)

            self.send_response(200)
            self.send_header('Content-Type', 'video/mp2t')
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(('127.0.0.1', 0), Cam4Proxy)
    port = server.server_port

    threading.Thread(target=server.serve_forever, daemon=True).start()

    proxy_url = f"http://127.0.0.1:{port}/playlist.m3u8"

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
    import xbmcgui
    listurl = '{0}/api/directoryCams?directoryJson=true&online=true&url=true&orderBy=VIDEO_QUALITY{1}'.format(site.url, url)    
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
        item['username']: item | favorite_data[item['username']]
        for item in model_list
        if item['username'] in favorite_data
    }

    for model_name, info in model_lookup.items():
        username = info['username']
        name = info['username']
        age = info['age']
        if age:
            name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)
        hd = ''
        if info.get('hdStream'):
            # name = '{0} [COLOR limegreen][HD][/COLOR]'.format(name)
            hd = 'HD'
        img = info['snapshotImageLink']
        if not img:
            img = info['defaultImageLink']

        subject = ''

        if info['viewers']:
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(info['viewers'])
        if info['countryCode']:
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(utils.get_country(info['countryCode']))
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, utils.get_country(info['countryCode']))
        if info['languages']:
            langs = [utils.get_language(lang) for lang in info['languages']]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if info['resolution']:
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(info['resolution'])
        if info['sexPreference']:
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(info['sexPreference'])
        if info['statusMessage']:
            subject += '[CR]{}[CR][CR]'.format(info['statusMessage'].encode('utf8') if utils.PY2 else info['statusMessage'])
        if info['showTags']:
            subject += ', '.join(info['showTags']).encode('utf8') if utils.PY2 else ', '.join(info['showTags'])

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, info['username'])
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(info['username']))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(info['username']), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, video, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, contextm=contextmenu, noDownload=True, quality=hd, fav='del')

    utils.eod()

def get_cookie():
    domain = ".cam4.com"
    cookiestr = ""
    # Căutăm în cookiejar-ul global al addon-ului tău (utils.cj)
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
        print(f"Eroare la executarea utils._postHtml pentru Login Cam4: {e}")
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
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('cam4user', '')
                utils.addon.setSetting('cam4pass', '')
        utils.addon.setSetting('cam4_sessionid', '')
        utils.addon.setSetting('cam4logged', 'false')
        cam4logged = False
        
        utils.refresh()
        return True
        
    except Exception as e:
        print(f"Eroare la executarea utils._postHtml pentru Logout Cam4: {e}")
        return False


@site.register()
def followedCams():
    import json

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

    try:
        data = json.loads(response)
        return data.get("users", [])
    except:
        return []


def followedCams():
    import json

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

    try:
        data = json.loads(response)
        return data.get("users", [])
    except:
        return []




def followedCams_():
    import json
    import xbmc

    sessionid = utils.addon.getSetting('cam4_sessionid')
    if not sessionid:
        if not login():
            utils.notify("Cam4", "Authentication needed")
            return []

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

    if data.get("count") == 0:
        utils.notify('Cam4', 'No followed cams are online')
        return
    
    results = data.get("users", [])
    cams = []

    for item in results:
        cams.append({
            "username": item.get("username"),
            "isBroadcasting": item.get("isBroadcasting", False),
            "access_level": item.get("access_level"),
        })
    return cams


@site.register()
def list_followed():
    cams = followedCams()  # favorite online din API Flash
    if not cams:
        utils.notify("Cam4", "Nu există modele favorite online")
        utils.eod()
        return
    else:
        list_followed_online(cams)

def list_followed_online(cams):
    import json
    base = site.url.rstrip('/')
    followed_set = {cam["username"] for cam in cams}

    listurl = '{0}/api/directoryCams?directoryJson=true&online=true&url=true&orderBy=VIDEO_QUALITY'.format(site.url)
    listhtml = utils._getHtml(listurl, headers=IOS_UA)
    cams_info = json.loads(listhtml).get('users', {})
    followed_online = [
        cam for cam in cams_info
        if cam.get("username") in followed_set
    ]

    for cam in followed_online:
        #name = cam.get('username')
        name = f"[COLOR yellow]♥[/COLOR] {cam.get('username')}"
        fav='del'
        username = cam.get('username')
        age = cam.get('age')
        if age:
            name += ' [COLOR deeppink][{}][/COLOR]'.format(age)
        hd = ''
        if cam.get('hdStream'):
            # name = '{0} [COLOR limegreen][HD][/COLOR]'.format(name)
            hd = 'HD'
        img = cam.get('snapshotImageLink')
        if not img:
            img = cam.get('defaultImageLink')

        subject = ''

        if cam.get('viewers'):
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(cam.get('viewers'))
        if cam.get('countryCode'):
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(utils.get_country(cam.get('countryCode')))
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, utils.get_country(cam.get('countryCode')))
        if cam.get('languages'):
            langs = [utils.get_language(lang) for lang in cam.get('languages')]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if cam.get('resolution'):
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(cam.get('resolution'))
        if cam.get('sexPreference'):
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(cam.get('sexPreference'))
        if cam.get('statusMessage'):
            subject += '[CR]{}[CR][CR]'.format(cam.get('statusMessage').encode('utf8') if utils.PY2 else cam.get('statusMessage'))
        if cam.get('showTags'):
            subject += ', '.join(cam.get('showTags')).encode('utf8') if utils.PY2 else ', '.join(cam.get('showTags'))

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, cam.get('username'))
        context = []
        if username in followed_set:
            context.append((
                "Unfollow {}".format(username),
                f"RunPlugin({utils.addon_sys}?mode=cam4.unfollow&model={urllib_parse.quote_plus(username)})"
            ))
        else:
            context.append((
                "Follow {}".format(username),
                f"RunPlugin({utils.addon_sys}?mode=cam4.follow&model={urllib_parse.quote_plus(username)})"
            ))
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(cam.get('username')))
        context.append((('[COLOR violet]Find recordings featuring [/COLOR]{}'.format(cam.get('username')), 'RunPlugin(' + contextrecord + ')')))
        site.add_download_link(name, video, 'Playvid', img, subject, contextm=context, noDownload=True, fav=fav,quality=hd)
    # site.add_dir('[COLOR yellow]Offline Favorites[/COLOR]', "", 'list_offline', '', 1)

    utils.eod()




#@site.register()
def list_followed():
    import json

    cams = followedCams()  # lista completă din pasul B

    if not cams:
        utils.notify("Cam4", "Nu există modele favorite online")
        utils.eod()
        return

    listurl = '{0}/api/directoryCams?directoryJson=true&online=true&url=true&orderBy=VIDEO_QUALITY'.format(site.url)
    listhtml = utils._getHtml(listurl, headers=IOS_UA)
    all_cams = json.loads(listhtml).get('users', {})

    # --- FILTRARE FAVORITE ---
    favorite_set = {cam["username"] for cam in cams}
    filtered_cams = [cam for cam in all_cams if cam.get("username") in favorite_set]


    for cam in filtered_cams:
        name = cam.get('username')
        age = cam.get('age')
        if age:
            name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)
        hd = ''
        if cam.get('hdStream'):
            # name = '{0} [COLOR limegreen][HD][/COLOR]'.format(name)
            hd = 'HD'
        img = cam.get('snapshotImageLink')
        if not img:
            img = cam.get('defaultImageLink')

        subject = ''

        if cam.get('viewers'):
            subject += '[COLOR deeppink]Viewers:[/COLOR] {}[CR]'.format(cam.get('viewers'))
        if cam.get('countryCode'):
            subject += '[CR][COLOR deeppink]Country:[/COLOR] {}[CR]'.format(utils.get_country(cam.get('countryCode')))
            name = '{0} [COLOR blue][{1}][/COLOR]'.format(name, utils.get_country(cam.get('countryCode')))
        if cam.get('languages'):
            langs = [utils.get_language(lang) for lang in cam.get('languages')]
            subject += '[COLOR deeppink]Languages:[/COLOR] {}[CR]'.format(', '.join(langs))
        if cam.get('resolution'):
            subject += '[COLOR deeppink]Resolution:[/COLOR] {}[CR]'.format(cam.get('resolution'))
        if cam.get('sexPreference'):
            subject += '[CR][COLOR deeppink]Sexual Preference:[/COLOR] {}[CR]'.format(cam.get('sexPreference'))
        if cam.get('statusMessage'):
            subject += '[CR]{}[CR][CR]'.format(cam.get('statusMessage').encode('utf8') if utils.PY2 else cam.get('statusMessage'))
        if cam.get('showTags'):
            subject += ', '.join(cam.get('showTags')).encode('utf8') if utils.PY2 else ', '.join(cam.get('showTags'))

        video = '{}rest/v1.0/profile/{}/streamInfo'.format(site.url, cam.get('username'))
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(cam.get('username')))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(cam.get('username')), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, video, 'Playvid', img, subject, contextm=contextmenu, noDownload=True, quality=hd)

    utils.eod()


@site.register()
def list_offline():
    import json

    username = utils.addon.getSetting("cam4_username")
    base = site.url.rstrip('/')
    url = f"{base}/rest/v1.0/favorites/{username}?offset=0&limit=1000"

    favs_json = utils._getHtml(url, headers={"User-Agent": utils.USER_AGENT})
    data = json.loads(favs_json)

    # lista reală de favorite
    favs = data.get("usersList", [])
    all_fav_names = {f["username"] for f in favs}
    import xbmcgui
    xbmcgui.Dialog().ok("Debug", f"Total favorites: {str(all_fav_names)}")

def list_offline():
    import json

    username = utils.addon.getSetting("cam4_username")
    base = site.url.rstrip('/')
    url = f"{base}/rest/v1.0/favorites/{username}?offset=0&limit=1000"

    favs_json = utils._getHtml(url, headers={"User-Agent": utils.USER_AGENT})
    data = json.loads(favs_json)

    # lista reală de favorite
    favs = data.get("usersList", [])
    all_fav_names = {f["username"] for f in favs}

    # camere online (din API Flash)
    online = followedCams()
    online_names = {cam["username"] for cam in online}

    # camere offline = toate favoritele - cele online
    offline_names = sorted(all_fav_names - online_names)

    # filtrăm detaliile pentru camerele offline
    offline_cams = [f for f in favs if f["username"] in offline_names]

    for cam in offline_cams:
        name = cam.get("username")
        display = f"[COLOR gray]★ {name}[/COLOR]"
        img = cam.get("profileThumbnailUrl") or f"{base}/images/placeholder_offline.png"
        subject = "[COLOR gray]Offline[/COLOR]"

        site.add_download_link(display, "", "", img, subject, noDownload=True)

    utils.eod()




@site.register()
def follow(model):
    import requests
    import xbmcgui

    username = utils.addon.getSetting("cam4_username")
    if not username:
        utils.notify("Cam4", "You don't have a Cam4 username")
        return

    base = site.url.rstrip('/')
    url = f"{base}/rest/v1.0/favorites/{username}/{model}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=utf-8",
        "Origin": base,
        "Referer": f"{base}/{model}",
        "User-Agent": utils.USER_AGENT,
        "DNT": "1"
    }

    session_id = get_cam4_SESSION_ID()
    ah_token   = get_cam4_AH()

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
            utils.notify("Cam4", f"{model} followed")
        else:
            utils.notify("Cam4", f"Error {r.status_code} on follow")

    except Exception as e:
        utils.notify("Cam4", f"Error: {e}")


@site.register()
def unfollow(model):
    import requests
    import xbmcgui

    # username-ul real folosit de API
    username = utils.addon.getSetting("cam4_username")
    if not username:
        utils.notify("Cam4", "You don't have a Cam4 username")
        return

    # URL corect (fără dublu slash)
    base = site.url.rstrip('/')
    url = f"{base}/rest/v1.0/favorites/{username}/{model}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=utf-8",
        "Origin": base,
        "Referer": f"{base}/{model}",
        "User-Agent": utils.USER_AGENT,
        "DNT": "1"
    }

    # Cookie-uri reale din cookie jar
    session_id = get_cam4_SESSION_ID()
    ah_token   = get_cam4_AH()

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
            utils.notify("Cam4", f"{model} unfollowed")
        else:
            utils.notify("Cam4", f"Error {r.status_code} on unfollow")

    except Exception as e:
        utils.notify("Cam4", f"Error: {e}")


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

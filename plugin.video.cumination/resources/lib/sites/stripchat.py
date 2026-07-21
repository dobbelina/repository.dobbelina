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
import threading
import time
import random
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import sys

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse, urllib_error


try:
    # Python 2
    import BaseHTTPServer as httpserver
    import SocketServer as socketserver
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer
    import urllib2 as urlreq
    from urlparse import urlparse, parse_qs
except ImportError:
    # Python 3
    import http.server as httpserver
    import socketserver
    from http.server import BaseHTTPRequestHandler
    from http.server import HTTPServer
    import urllib.request as urlreq
    from urllib.parse import urlparse, parse_qs



UA = "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

site = AdultSite('stripchat', '[COLOR hotpink]stripchat.com[/COLOR]', 'http://stripchat.com/', 'stripchat.jpg', 'stripchat', True)
# bu = "https://stripchat.com/api/front/models?limit=80&parentTag=autoTagNew&sortBy=stripRanking&offset=0&primaryTag="
bu = "https://stripchat.com/api/front/models?removeShows=false&recInFeatured=false&limit=80&offset=0&filterGroupTags=&sortBy=stripRanking&parentTag=&nic=true&byw=false&rcmGrp=A&rbCnGr=true&iem=true&decMb=true&ctryTop=true&primaryTag="
top = "https://stripchat.com/api/front/v5/models/top?gender={0}&period=current&offset=0&limit=100&continent={1}"

@site.register(default_mode=True)
def Main():
    player = utils.addon.getSetting('stripchatplayer')
    if not player:
        utils.addon.setSetting('stripchatplayer', 'Playvid_Adaptive')
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
    site.add_dir('[COLOR red]Refresh Stripchat images[/COLOR]', '', 'clean_database', '', Folder=False)
    site.add_dir('[COLOR red]Top Models[/COLOR]', 'girls', 'topModels', '', '')
    site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', '{}girls'.format(bu), 'onlineFav', '', 1)
    # https://stripchat.com/api/front/v5/models/top?gender=female&period=current&offset=0&limit=100&continent=na&uniq=kcbwpy0hugjlieom
    if female:
        site.add_dir('[COLOR hotpink]Female[/COLOR]', '{0}girls'.format(bu), 'List', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '{0}couples'.format(bu), 'List', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male[/COLOR]', '{0}men'.format(bu), 'List', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '{0}trans'.format(bu), 'List', '', '')

    utils.eod()


@site.register()
def List(url, page=1):
    online_only = utils.addon.getSetting("online_only").lower() == 'true'
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    perPage_setting = utils.addon.getSetting('stripchatper_page')
    if perPage_setting and perPage_setting.strip() != "":
        perPage = int(perPage_setting)
    else:
        perPage = 80
        utils.addon.setSetting("stripchatper_page", str(perPage))

    if '/models/top' not in url:
        tag_setting = utils.addon.getSetting('stripchattag')
        if not tag_setting:
            tag_setting = 'ALL'
        utils.addon.setSetting("stripchattag", tag_setting)

        site.add_download_link(
            'Filter - currently: [COLOR fuchsia][B]' + tag_setting + '[/B][/COLOR] - '
            '[COLOR red][B]Change[/B][/COLOR]',
            url,
            'filters',
            '',
            '',
            noDownload=True
        )
        tag_setting = '' if tag_setting == 'ALL' else tag_setting
        url = url.replace('filterGroupTags=&', 'filterGroupTags=%5B%5B%22{0}%22%5D%5D&'.format(tag_setting)).replace('&parentTag=&', '&parentTag={0}&'.format(tag_setting))
    else:
        if utils.addon.getSetting("online_only") == "true":
            online_only = True
            site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
        else:
            online_only = False
            site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)


    favorite = {}
    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT name FROM favorites WHERE mode='stripchat.Playvid'")
    favorite = [row[0] for row in c.fetchall()]
    c.close()

    try:
        response = utils._getHtml(url)
    except:
        xbmcgui.Dialog().textviewer(url, "URL: " + url + "\n" + str(response))
        return None
    data = json.loads(response)
    if "models" in data:
        model_list = data["models"]
    elif 'tops' in data:
        model_list = []
        for top in data.get("tops", []):
            for winner in top.get("winners", []):
                model = winner.get("model")
                if model:
                    model_list.append(model)
    else:
        model_list = [item["model"] for item in data["items"]]

        # model_list = data["items"]
        # xbmcgui.Dialog().textviewer(url, str(model_list[1]["model"]))

    for model in model_list:
        if online_only is True and model.get("isLive") is False:
            continue
        # xbmcgui.Dialog().textviewer(url, str(model))
        name = utils.cleanhtml(model['username'])
        if any(name in fav_url for fav_url in favorite):
            # name = u'[COLOR yellow]★ [/COLOR]' + name
            fav = 'del'
        else:
            fav = 'add'

        try:
            videourl = model['hlsPlaylist']
        except KeyError:
            try:
                videourl = model['stream']['url']
            except KeyError:
                videourl = site.url

        # try:
        #     img = 'https://img.doppiocdn.media/snapshot/{0}/{1}_webp'.format(
        #         model.get('id'), model.get('popularSnapshotTimestamp')
        #     )
        # except KeyError:
        #     try:
        #         img = model['popularSnapshotUrl']
        #     except KeyError:
        #         img = 'https://img.doppiocdn.media/snapshot/{0}/{1}_webp'.format(
        #             model.get('id'), model.get('snapshotTimestamp')
        #         )
        try:
            if model.get("isLive") is False:
                img = model.get("previewUrlThumbBig")
            else:
                snap = (
                    model.get("popularSnapshotTimestamp")
                    or model.get("snapshotTimestamp")
                    or 0
                )
                img = f"https://img.doppiocdn.media/snapshot/{model['id']}/{snap}_webp"

        except Exception:
            img = model.get("previewUrlThumbBig") or ""

        fanart = model.get('previewUrlThumbSmall')
        subject = model.get('groupShowTopic') or ''
        if subject:
            subject += '[CR]'
        if model.get('country'):
            subject += '[COLOR deeppink]Location: [/COLOR]{0}[CR]'.format(
                utils.get_country(model.get('country'))
            )
        if model.get('languages'):
            langs = [utils.get_language(x) for x in model.get('languages')]
            subject += '[COLOR deeppink]Languages: [/COLOR]{0}[CR]'.format(', '.join(langs))
        if model.get('broadcastGender'):
            subject += '[COLOR deeppink]Gender: [/COLOR]{0}[CR]'.format(model.get('broadcastGender'))
        if model.get('viewersCount'):
            subject += '[COLOR deeppink]Watching: [/COLOR]{0}[CR][CR]'.format(model.get('viewersCount'))
        if model.get('tags'):
            subject += '[COLOR deeppink]#[/COLOR]'
            tags = [t for t in model.get('tags') if 'tag' not in t.lower()]
            subject += '[COLOR deeppink] #[/COLOR]'.join(tags)

        context = []
        contextrecord = (
            utils.addon_sys +
            "?mode=chaturbate.Record&id=" +
            urllib_parse.quote_plus(name)
        )
        context.append((
            '[COLOR violet]Find recordings featuring [/COLOR]{}'.format(name),
            'RunPlugin(' + contextrecord + ')'
        ))


        site.add_download_link(
            name if model.get("isLive") is True else name + ' [COLOR yellow][Offline][/COLOR]',
            videourl,
            'Playvid',
            img,
            subject,
            contextm=context,
            noDownload=True,
            fav=fav,
            quality='HD', 
            fanart=fanart
        )


    total_items = data.get('filteredCount', 0)
    nextp = (page * 80) < total_items
    if nextp:
        next = (page * 80) + 1
        lastpg = -1 * (-total_items // 80)
        page += 1
        nurl = re.sub(r'offset=\d+', 'offset={0}'.format(next), url)
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page - 1, lastpg),
                     nurl, 'List', site.img_next, page)

    utils.eod()


@site.register()
def PerPage(url=None, name=None):
    vq = utils._get_keyboard(heading=utils.i18n('Items per page'), default=utils.addon.getSetting("stripchatper_page"))
    if not vq or not vq.isdigit():
        return False
        
    utils.addon.setSetting("stripchatper_page", str(vq))
    import xbmc
    xbmc.executebuiltin('Container.Refresh')
    return True


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            rows = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".stripst.com")
            for row in rows:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".stripst.com")
            if showdialog:
                utils.notify('Finished', 'Stripchat images cleared')
    except:
        pass


@site.register()
def Playvid_change(url, name):
    current = utils.addon.getSetting('stripchatplayer')

    if current == 'Playvid_Adaptive':
        utils.addon.setSetting('stripchatplayer', 'Playvid_proxy')
        utils.notify('Player switched', 'Now using Proxy mode')
    elif current == 'Playvid_proxy':
        utils.addon.setSetting('stripchatplayer', 'Playvid_classic')
        utils.notify('Player switched', 'Now using Classic mode')
    elif current == 'Playvid_classic':
        utils.addon.setSetting('stripchatplayer', 'Playvid_Adaptive')
        utils.notify('Player switched', 'Now using Adaptive mode')

    xbmc.executebuiltin('Container.Refresh')


class GenericProxy(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        base_url = qs.get('u', [None])[0]

        if not base_url:
            self.send_error(500, "Missing ?u= URL")
            return

        path = parsed.path.lstrip("/")
        if path.endswith("proxy.m3u8"):
            final_url = base_url
        else:
            base = base_url.rsplit("/", 1)[0]
            final_url = base + "/" + path

        try:
            req = urlreq.Request(final_url, headers={
                'User-Agent': UA,
                'Origin': 'https://stripchat.com',
                'Referer': 'https://stripchat.com/'
            })
            data = urlreq.urlopen(req, timeout=10).read()
        except Exception as e:
            xbmc.log("@@@@Cumination: GenericProxy ERROR for %s: %s" % (final_url, repr(e)), xbmc.LOGERROR)
            self.send_error(500, "Eroare: %s" % e)
            return

        if final_url.endswith(".m3u8"):
            text = data.decode('utf-8')
            base = base_url.rsplit("/", 1)[0]
            text = re.sub(r'^(?!#)(.*\.ts)', base + r'/\1', text, flags=re.MULTILINE)

            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(text.encode('utf-8'))
            return

        self.send_response(200)
        self.send_header("Content-Type", "video/mp2t")
        self.end_headers()
        self.wfile.write(data)


_proxy_servers = {}
_proxy_threads = {}


def start_generic_proxy(port):
    global _proxy_servers, _proxy_threads

    if port in _proxy_servers:
        return

    server = HTTPServer(('127.0.0.1', port), GenericProxy)
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
        except:
            pass

        del _proxy_servers[port]
        del _proxy_threads[port]


@site.register()
def Playvid_Classic(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    altUrl = 'https://go.stripchat.com/api/models?limit=1&modelsList='
    data = json.loads(utils._getHtml(altUrl + name))
    data = data['models'][0]
    if data["username"] == name:
        url = data['stream']['url']
    else:
        utils.notify(name, 'Couldn\'t find a playable webcam link', icon='thumb')
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Found Stream[CR]")
    vp.play_from_direct_link(url)
    vp.progress.close()


@site.register()
def Playvid_ISA(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    api = "https://go.stripchat.com/api/models?limit=1&modelsList="
    try:
        raw = utils._getHtml(api + name)
        data = json.loads(raw)
        data = data['models'][0]
    except Exception as e:
        utils.notify(name, "Error at API interogation", icon='thumb')
        vp.progress.close()
        return

    if data.get("username") != name:
        utils.notify(name, "Couldn't find a playable webcam link", icon='thumb')
        vp.progress.close()
        return

    stream_url = data['stream'].get('url')
    if not stream_url:
        utils.notify(name, "Stream URL missing in response", icon='thumb')
        vp.progress.close()
        return

    vp.progress.update(75, "[CR]Found Stream[CR]InputStream Adaptive should handle the rest...[CR]")

    try:
        utils.kodilog("Playvid_ISA stream_url = %s" % stream_url)
    except:
        pass

    vp.play_from_direct_link(stream_url)
    vp.progress.close()


@site.register()
def Playvid_Proxy(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    api = "https://go.stripchat.com/api/models?limit=1&modelsList="
    data = json.loads(utils._getHtml(api + name))
    data = data['models'][0]

    if data["username"] != name:
        utils.notify(name, "Couldn't find a playable webcam link", icon='thumb')
        vp.progress.close()
        return

    stream_url = data['stream']['url']
    vp.progress.update(75, "[CR]Found Stream[CR]")

    port = random.randint(30000, 60000)

    stop_generic_proxy(port)
    start_generic_proxy(port)

    encoded = urllib.parse.quote_plus(stream_url)
    proxy_url = "http://127.0.0.1:%d/proxy.m3u8?u=%s" % (port, encoded)

    xbmc.log("@@@@Cumination: Playvid_Proxy stream_url = %s" % stream_url, xbmc.LOGINFO)
    xbmc.log("@@@@Cumination: Playvid_Proxy proxy_url  = %s" % proxy_url, xbmc.LOGINFO)

    vp.play_from_direct_link(proxy_url)
    vp.progress.close()


@site.register()
def Playvid(url, name):
    if "[Offline]" in name:
        utils.notify(name.split("[")[0] + " is OFFLINE")
        return
    player = utils.addon.getSetting('stripchatplayer')

    if player == 'Playvid_proxy':
        return Playvid_Proxy(url, name)
    elif player == 'Playvid_Adaptive':
        return Playvid_ISA(url, name)
    elif player == 'Playvid_classic':
        return Playvid_Classic(url, name)


@site.register()
def List2(url):
    site.add_download_link('[COLOR red][B]Refresh[/B][/COLOR]', url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        url = url + '/?online_only=1'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    match = re.compile('class="top_ranks(.+?)class="title_h3', re.I | re.M | re.S).findall(data)
    if not match:
        match = re.compile('class="top_others(.+?)class="title_h3', re.I | re.M | re.S).findall(data)
    match = re.compile('class="top_thumb".+?href="([^"]+)".+?src="([^"]+)".+?class="mn_lc">(.+?)</span>',
                       re.I | re.M | re.S).findall(match[0])
    for url2, img, name in match:
        if 'profile' in url2:
            name = '[COLOR hotpink][Offline][/COLOR] ' + name
            url2 = "  "
        site.add_download_link(name, url2[1:], 'Playvid', 'https:' + img, '')
    utils.eod()


@site.register()
def List3(url):
    site.add_download_link('[COLOR red][B]Refresh[/B][/COLOR]', url, 'utils.refresh', '', '', noDownload=True)
    if utils.addon.getSetting("online_only") == "true":
        url = url + '/?online_only=1'
        site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
    else:
        site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    data = utils._getHtml(url, site.url, headers=headers)
    match = re.compile('class="top_ranks(.+?)trs_actions', re.I | re.M | re.S).findall(data)
    match = re.compile('class="top_thumb".+?href="([^"]+)".+?src="([^"]+)".+?class="mn_lc">(.+?)</span>',
                       re.I | re.M | re.S).findall(match[0])
    for url2, img, name in match:
        if 'profile' in url2:
            name = '[COLOR hotpink][Offline][/COLOR] ' + name
            url2 = "  "
        site.add_download_link(name, url2[1:], 'Playvid', 'https:' + img, '')
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
    import xbmcgui

    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='stripchat.Playvid'")
    favorite_data = {
        row[0]: {'db_url': row[1], 'db_image': row[2]} 
        for row in c.fetchall()
    }
    c.close()
    # xbmcgui.Dialog().textviewer("Debug", json.dumps(favorite_data, indent=4))

    for model in favorite_data:
        # xbmcgui.Dialog().textviewer("Debug", "Favorite: %s, URL: %s, Image: %s" % (model, favorite_data[model]['db_url'], favorite_data[model]['db_image']))
        altUrl = 'https://stripchat.com/api/front/v4/models/search/suggestion?limit=24&primaryTag=girls&query=' + model
        # altUrl = 'https://stripchat.com/api/front/v5/models/search/group/all?limit=24&primaryTag=girls&query=' + model
        try:
            raw = utils._getHtml(altUrl)
            data = json.loads(raw)
            models = data.get('models', [])
            found = next((m for m in models if m.get("username") == model), None)
            if not found:
                continue  # not found
            if not found.get("isOnline"):
                continue
            img = found.get("previewUrl")
            model = u'[COLOR yellow]★ [/COLOR]' + model
            fav = 'del'
 
            # altUrl = 'https://stripchat.com/api/front/v5/models/search/group/all?limit=24&primaryTag=girls&query=' + model
            # try:
            #     raw = utils._getHtml(altUrl)
            #     data = json.loads(raw)
            #     data = data['models'][0]
            #     if data["username"] == model:
            #         isOnline = data['isOnline']
            #         if not isOnline:
            #             continue
            #         img = data['previewUrl']
            # https://stripchat3.com/api/front/v2/models/username/ChrystalCade/cam?triggerRequest=loadCam&primaryTag=girls
            # data_model = json.loads(utils._getHtml('https://stripchat3.com/api/front/v2/models/username/{}/cam?triggerRequest=loadCam&primaryTag=girls'.format(model)))
        except Exception as e:
            utils.notify(model, "Error at API interrogation: %s" % e, icon='thumb')
            continue
        
        contextrecord = (
            utils.addon_sys +
            "?mode=chaturbate.Record&id=" +
            urllib_parse.quote_plus(found["username"])
        )
        contextmenu = [(
            '[COLOR violet]Find recordings featuring [/COLOR]{}'.format(found["username"]),
            'RunPlugin(' + contextrecord + ')'
        )]

        site.add_download_link(
            found["username"],
            url,
            'Playvid',
            img,
            quality='HD',
            fav=fav
        )
    utils.eod()
    # https://stripchat.com/api/front/v4/models/search/suggestion?limit=1&primaryTag=girls&query=ChrystalCade
    return

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


@site.register()
def filters(url):
    import xbmcgui
    groupTags = [
        {"name": "Age", "prefix": "age"},
        {"name": "Body Type", "prefix": "bodyType"},
        {"name": "Activities on Request", "prefix": "do"},
        {"name": "Ethnicity", "prefix": "ethnicity"},
        {"name": "Hair", "prefix": "hairColor"},
        {"name": "Specifics", "prefix": "specific"}, 
        {"name": "Subcultures", "prefix": "subculture"}, 
        {"name": "Countries & Languages", "prefix": "tagLanguage"},
        {"name": "AutoTag", "prefix": "autoTag"}
    ]
    names = [site["name"] for site in groupTags]

    selection = xbmcgui.Dialog().select('Select filter', names)
    if selection == -1:
        return
    tag = groupTags[selection]["prefix"]

    count_all = json.loads(utils._getHtml("https://stripchat.com/api/front/models/count"))["count"]
    # url = 'https://stripchat.com/api/front/models/liveTags?primaryTag=girls&withMixedTags=true&currentMixedTag=tagLanguageJapanese&parentTag=tagLanguageJapanese&specialEventTagIds=%5B%22worldTournament%22%5D'
    url = 'https://stripchat.com/api/front/models/liveTags'
    listhtml = utils._getHtml(url)
    cjson = json.loads(listhtml)
    tags = cjson["liveTagDetails"]

    filtered = {k.replace(tag, ""): v for k, v in tags.items() if k.startswith(tag) and "-" not in k}
    agregate = ["ALL ["+ str(count_all) + "]"] + sorted({f"{k} [{v['modelsLive']}]" for k, v in filtered.items()})
    selection = xbmcgui.Dialog().select('Select ' + tag , agregate)

    if selection != -1:
        if selection == 0:
            utils.addon.setSetting("stripchattag", "")
        else:
            selected_url = str(agregate[selection]).split(' ')[0]
            utils.addon.setSetting("stripchattag", tag + selected_url)
        utils.refresh()
        return


@site.register()
def topModels(url):
    genders = [
        {"name": "Girls", "code": "female"},
        {"name": "Couples", "code": "couple"},
        {"name": "Guys", "code": "male"},
        {"name": "Trans", "code": "tranny"}
    ]
    names = [item["name"] for item in genders]
    selection = xbmcgui.Dialog().select('Select Gender', names)
    if selection == -1:
        return
    url = genders[selection]["code"]

    if url == "female":
        zones = [
            {"name": "Europe", "code": "eu"},
            {"name": "North America", "code": "na"},
            {"name": "South America", "code": "sa"},
            {"name": "Asia & Pacific", "code": "as"},
            {"name": "Africa", "code": "af"}
        ]
        names = [item["name"] for item in zones]

        selection = xbmcgui.Dialog().select('Select zone', names)
        if selection == -1:
            return
        zone = zones[selection]["code"]
    else:
        zone = ""

    periodes = [
        {"name": "Current Month Top", "code": "current", "url": "https://stripchat.com/api/front/v5/models/top?gender={0}&period=current&offset=0&limit=100&continent={1}".format(url, zone)},
        {"name": "Last 24h Winners", "code": "hourly", "url": "https://stripchat.com/api/front/v4/models/top/hourly?gender={}".format(url)},
        {"name": "Last Month Winners", "code": "monthly", "url": "https://stripchat.com/api/front/v5/models/top?gender={0}&period=monthly&offset=0&limit=100&continent={1}".format(url, zone)},
        {"name": "Hall of Fame 2026", "code": "hallOfFame", "url": "https://stripchat.com/api/front/v3/models/top/hallOfFame?year=2026&gender={}".format(url)}
    ]
    names = [item["name"] for item in periodes]

    selection = xbmcgui.Dialog().select('Select Period', names)
    if selection == -1:
        return
    period = periodes[selection]["code"]
    url = periodes[selection]["url"]
    List(url)
    
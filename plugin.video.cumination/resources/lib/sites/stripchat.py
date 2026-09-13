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
import random
import urllib.parse
import xbmc
import xbmcgui
import calendar
import time
from datetime import datetime, timedelta

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse


try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    import urllib2 as urlreq
    from urlparse import urlparse, parse_qs
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import urllib.request as urlreq
    from urllib.parse import urlparse, parse_qs


abbr_to_full = {abbr.lower(): name for abbr, name in zip(calendar.day_abbr, calendar.day_name)}
UA = "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

site = AdultSite('stripchat', '[COLOR hotpink]stripchat.com[/COLOR]', 'http://stripchat.com/', 'stripchat.jpg', 'stripchat', True)
bu = "https://stripchat.com/api/front/models?removeShows=false&recInFeatured=false&limit=80&offset=0&filterGroupTags=&sortBy=stripRanking&parentTag=&nic=true&byw=false&rcmGrp=A&rbCnGr=true&iem=true&decMb=true&ctryTop=true&primaryTag="
cam = "https://stripchat.com/api/front/v2/models/{}/cam"


def get_api_status(model):
    """
    Affiche le statut brut tel que renvoyé par l'API Stripchat
    """
    status = model.get('status', 'unknown').lower()
    p2p_rate = model.get('p2pRate', 0)
    
    # Mapping des statuts avec couleurs
    status_map = {
        'public': ('PUBLIC', 'green'),
        'private': ('PRIVE', 'red'),
        'group': ('GROUPE SHOW', 'orange'),
        'ticket': ('TICKET SHOW', 'yellow'),
        'hidden': ('CACHE', 'grey'),
        'away': ('ABSENT', 'blue'),
        'idle': ('INACTIF', 'blue'),
        'p2p': ('P2P', 'hotpink')
    }
    
    label, color = status_map.get(status, (status.upper(), 'white'))
    
    # Si P2P disponible (même si status est public)
    if p2p_rate > 0:
        label += ' + P2P({})'.format(p2p_rate)
    
    return label, color


@site.register(default_mode=True)
def Main():
    modelInfo_setting = utils.addon.getSetting('stripchat_modelInfo') == "true"
    site.add_download_link(u'Model Info: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format("Visible" if modelInfo_setting else "Hidden"), site.url, 'ShowModelInfo', '', '', noDownload=True)

    img_mode = utils.addon.getSetting('stripchat_img_mode') or 'live'
    mode_label = "Live Snapshot" if img_mode == 'live' else "Profile Photo"
    site.add_download_link(u'Image Mode: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format(mode_label), site.url, 'ToggleImageMode', '', '', noDownload=True)

    player = utils.addon.getSetting('stripchatplayer') or 'Playvid_Adaptive'
    pretty_name = {'Playvid_Adaptive': 'Adaptive', 'Playvid_proxy': 'Proxy', 'Playvid_classic': 'Classic'}.get(player, 'Adaptive')
    site.add_download_link(u'Current player: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format(pretty_name), site.url, 'Playvid_change', site.img_player, '', noDownload=True)

    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    
    site.add_dir('[COLOR red]Refresh Stripchat images[/COLOR]', '', 'clean_database', site.img_refresh, Folder=False)
    site.add_dir('[COLOR red]Top Models[/COLOR]', 'girls', 'topModels', site.img_models, '')
    site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', '{}girls'.format(bu), 'onlineFav', site.img_favorites, 1)
    
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
def ToggleImageMode():
    current = utils.addon.getSetting('stripchat_img_mode')
    new_mode = 'profile' if current == 'live' else 'live'
    utils.addon.setSetting('stripchat_img_mode', new_mode)
    mode_text = "Profile Photo" if new_mode == 'profile' else "Live Snapshot"
    utils.notify("Image Mode Changed", "Now using: {}".format(mode_text))
    xbmc.executebuiltin('Container.Refresh')


@site.register()
def List(url, page=1):
    online_only = utils.addon.getSetting("online_only").lower() == 'true'
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    perPage = 80
    perPage_setting = utils.addon.getSetting('stripchatper_page')
    if perPage_setting and perPage_setting.strip().isdigit():
        perPage = int(perPage_setting)

    if '/models/top' not in url:
        tag_setting = utils.addon.getSetting('stripchattag') or 'ALL'
        site.add_download_link('Filter: [COLOR fuchsia][B]{}[/B][/COLOR] - [COLOR red][B]Change[/B][/COLOR]'.format(tag_setting), url, 'filters', '', '', noDownload=True)
        tag_param = '' if tag_setting == 'ALL' else tag_setting
        url = url.replace('filterGroupTags=&', 'filterGroupTags=%5B%5D%5B%22{0}%22%5D%5D&'.format(tag_param)).replace('&parentTag=&', '&parentTag={0}&'.format(tag_param))
    else:
        if utils.addon.getSetting("online_only") == "true":
            site.add_download_link('[COLOR red][B]Show all models[/B][/COLOR]', url, 'online', '', '', noDownload=True)
        else:
            site.add_download_link('[COLOR red][B]Show only models online[/B][/COLOR]', url, 'online', '', '', noDownload=True)

    # Récupération des favoris
    favorite = []
    try:
        conn = sqlite3.connect(utils.favoritesdb)
        conn.text_factory = str
        c = conn.cursor()
        c.execute("SELECT name FROM favorites WHERE mode='stripchat.Playvid'")
        favorite = [row[0] for row in c.fetchall()]
        c.close()
    except:
        pass

    try:
        response = utils._getHtml(url)
        data = json.loads(response)
    except:
        return None
        
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
        model_list = [item["model"] for item in data.get("items", [])]

    total_items = data.get('filteredCount', 0)
    img_mode = utils.addon.getSetting('stripchat_img_mode') or 'live'

    for model in model_list:
        if online_only and not model.get("isLive"):
            continue
            
        # Récupération du statut API brut
        status_label, status_color = get_api_status(model)
        
        # Nom avec étoile si favoris
        raw_name = utils.cleanhtml(model.get('username', ''))
        
        is_favorite = any(raw_name == fav_name for fav_name in favorite)
        if is_favorite:
            name = u'[COLOR yellow]\u2605[/COLOR] ' + raw_name
            fav = 'del'
        else:
            name = raw_name
            fav = 'add'

        # URL vidéo
        videourl = model.get('hlsPlaylist') or ''
        if not videourl and model.get('stream'):
            videourl = model.get('stream', {}).get('url', '')
        if not videourl:
            videourl = site.url

        # Images
        profile_img = model.get("previewUrlThumbBig") or model.get("previewUrl") or ""
        profile_small = model.get('previewUrlThumbSmall') or profile_img
        
        live_img = profile_img
        if model.get("isLive"):
            snap = model.get("popularSnapshotTimestamp") or model.get("snapshotTimestamp") or int(time.time() / 60)
            cb = random.randint(1000, 9999)
            live_img = f"https://img.doppiocdn.media/snapshot/{model.get('id')}/{snap}_webp?cb={cb}"

        if img_mode == 'profile':
            img = profile_img
            fanart = live_img if model.get("isLive") else profile_small
        else:
            img = live_img if model.get("isLive") else profile_img
            fanart = profile_small
        
        if not img:
            img = site.image
        if not fanart:
            fanart = img

        # Construction du subject avec statut API
        subject = model.get('groupShowTopic') or ''
        if subject:
            subject += '[CR]'
        
        # AJOUT DU STATUT API BRUT
        subject += '[COLOR {}][B]{}[/B][/COLOR][CR]'.format(status_color, status_label)
        
        # RÉSOLUTION (width x height) + Mobile si isMobile
        width = 0
        height = 0
        
        broadcast_settings = model.get('broadcastSettings', {})
        if broadcast_settings:
            width = broadcast_settings.get('width', 0)
            height = broadcast_settings.get('height', 0)
        
        if not width and model.get('stream'):
            stream_data = model.get('stream', {})
            width = stream_data.get('width', 0)
            height = stream_data.get('height', 0)
        
        if width and height:
            if model.get('isMobile'):
                subject += 'Resolution: {0}x{1} (Mobile)[CR]'.format(width, height)
            else:
                subject += 'Resolution: {0}x{1}[CR]'.format(width, height)
        
        # Informations standards
        if model.get('country'):
            subject += 'Location: {0}[CR]'.format(utils.get_country(model.get('country')))
        if model.get('languages'):
            langs = [utils.get_language(x) for x in model.get('languages')]
            subject += 'Languages: {0}[CR]'.format(', '.join(langs))
        if model.get('broadcastGender'):
            subject += 'Gender: {0}[CR]'.format(model.get('broadcastGender'))
        if model.get('viewersCount'):
            subject += 'Watching: {0}[CR]'.format(model.get('viewersCount'))
        
        # Tags
        if model.get('tags'):
            subject += '#'
            tags = [t for t in model.get('tags') if 'tag' not in t.lower()]
            subject += ' #'.join(tags)

        streamName = model.get('streamName') or ''

        # Model Info étendu
        if utils.addon.getSetting('stripchat_modelInfo') == "true":
            try:
                api = cam.format(model.get("id"))
                data = json.loads(utils._getHtml(api))
                if data.get('cam', {}).get('broadcastSchedule', {}).get('nearest', {}).get("day"):
                    sched = data['cam']['broadcastSchedule']['nearest']
                    subject += '[CR]Next broadcast: {0} '.format(abbr_to_full.get(sched.get("day", ""), ""))
                    if sched.get('period'):
                        t1 = (datetime.min + timedelta(seconds=sched['period'][0])).time().strftime("%I %p")
                        t2 = (datetime.min + timedelta(seconds=sched['period'][1])).time().strftime("%I %p")
                        subject += '{0} - {1}[CR]'.format(t1, t2)
            except:
                pass

        context = []
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(raw_name))
        context.append(('Find recordings featuring {}'.format(raw_name), 'RunPlugin(' + contextrecord + ')'))

        display_name = name if model.get("isLive") else name + ' [Offline]'
        
        site.add_download_link(display_name, videourl + '&streamName=' + str(streamName),
            'Playvid', img, subject, contextm=context, noDownload=True, fav=fav, quality='HD', fanart=fanart)

    nextp = (page * perPage) < total_items
    if nextp:
        next_p = (page * perPage) + 1
        lastpg = -1 * (-total_items // perPage)
        page += 1
        nurl = re.sub(r'offset=\d+', 'offset={0}'.format(next_p), url)
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page - 1, lastpg), nurl, 'List', site.img_next, page)

    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    try:
        conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
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
    next_player = {'Playvid_Adaptive': 'Playvid_proxy', 'Playvid_proxy': 'Playvid_classic', 'Playvid_classic': 'Playvid_Adaptive'}
    new = next_player.get(current, 'Playvid_Adaptive')
    utils.addon.setSetting('stripchatplayer', new)
    names = {'Playvid_Adaptive': 'Adaptive', 'Playvid_proxy': 'Proxy', 'Playvid_classic': 'Classic'}
    utils.notify('Player switched', 'Now using ' + names.get(new) + ' mode')
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
            req = urlreq.Request(final_url, headers={'User-Agent': UA, 'Origin': 'https://stripchat.com', 'Referer': 'https://stripchat.com/'})
            data = urlreq.urlopen(req, timeout=10).read()
        except Exception as e:
            self.send_error(500, "Error: %s" % e)
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
    if port in _proxy_servers:
        return
    server = HTTPServer(('127.0.0.1', port), GenericProxy)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    _proxy_servers[port] = server
    _proxy_threads[port] = thread


def stop_generic_proxy(port):
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
    try:
        altUrl = 'https://go.stripchat.com/api/models?limit=1&modelsList='
        data = json.loads(utils._getHtml(altUrl + name))
        model_data = data['models'][0]
        if model_data["username"] == name:
            stream_url = model_data['stream']['url']
            vp.progress.update(75, "[CR]Found Stream[CR]")
            vp.play_from_direct_link(stream_url)
        else:
            utils.notify(name, 'Couldn\'t find a playable webcam link', icon='thumb')
    except:
        utils.notify(name, 'Error loading stream', icon='thumb')
    vp.progress.close()


@site.register()
def Playvid_ISA(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        api = "https://go.stripchat.com/api/models?limit=1&modelsList="
        data = json.loads(utils._getHtml(api + name))
        model_data = data['models'][0]
        if model_data.get("username") == name:
            stream_url = model_data['stream']['url']
            vp.progress.update(75, "[CR]Found Stream[CR]")
            vp.play_from_direct_link(stream_url)
        else:
            utils.notify(name, "Couldn't find a playable webcam link", icon='thumb')
    except:
        utils.notify(name, "Error at API interrogation", icon='thumb')
    vp.progress.close()


@site.register()
def Playvid_Proxy(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        api = "https://go.stripchat.com/api/models?limit=1&modelsList="
        data = json.loads(utils._getHtml(api + name))
        model_data = data['models'][0]
        if model_data["username"] == name:
            stream_url = model_data['stream']['url']
            vp.progress.update(75, "[CR]Found Stream[CR]")
            
            port = random.randint(30000, 60000)
            stop_generic_proxy(port)
            start_generic_proxy(port)
            encoded = urllib.parse.quote_plus(stream_url)
            proxy_url = "http://127.0.0.1:%d/proxy.m3u8?u=%s" % (port, encoded)
            
            vp.play_from_direct_link(proxy_url)
        else:
            utils.notify(name, "Couldn't find a playable webcam link", icon='thumb')
    except Exception as e:
        utils.notify(name, "Error: %s" % str(e), icon='thumb')
    vp.progress.close()


def status(url):
    if '&streamName=' in url:
        streamName = url.split('&streamName=')[-1]
        if streamName:
            try:
                api = cam.format(streamName)
                data = json.loads(utils._getHtml(api))
                streamStatus = data.get('user', {}).get('user', {}).get("status")
                if streamStatus == 'public':
                    return True
                else:
                    utils.notify(streamName, streamStatus)
                    return False
            except:
                return True
    return True


@site.register()
def Playvid(url, name):
    if not status(url):
        return
    if "[Offline]" in name:
        utils.notify(name.split("[")[0] + " is OFFLINE")
        return
    player = utils.addon.getSetting('stripchatplayer')
    if player == 'Playvid_proxy':
        return Playvid_Proxy(url, name)
    elif player == 'Playvid_Adaptive':
        return Playvid_ISA(url, name)
    else:
        return Playvid_Classic(url, name)


@site.register()
def online(url):
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()


@site.register()
def onlineFav(url):
    favorite_data = {}
    try:
        conn = sqlite3.connect(utils.favoritesdb)
        conn.text_factory = str
        c = conn.cursor()
        c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='stripchat.Playvid'")
        favorite_data = {row[0]: {'db_url': row[1], 'db_image': row[2]} for row in c.fetchall()}
        c.close()
    except:
        pass

    for model_name in favorite_data:
        try:
            altUrl = 'https://stripchat.com/api/front/v4/models/search/suggestion?limit=24&primaryTag=girls&query=' + model_name
            raw = utils._getHtml(altUrl)
            data = json.loads(raw)
            models = data.get('models', [])
            found = next((m for m in models if m.get("username") == model_name), None)
            if not found or not found.get("isOnline"):
                continue
            
            display_name = u'[COLOR yellow]\u2605[/COLOR] ' + found["username"]
            img = found.get("previewUrl")
            
            site.add_download_link(display_name, url, 'Playvid', img, quality='HD', fav='del')
        except:
            continue
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

    try:
        count_all = json.loads(utils._getHtml("https://stripchat.com/api/front/models/count"))["count"]
        listhtml = utils._getHtml('https://stripchat.com/api/front/models/liveTags')
        cjson = json.loads(listhtml)
        tags = cjson.get("liveTagDetails", {})
        filtered = {k.replace(tag, ""): v for k, v in tags.items() if k.startswith(tag) and "-" not in k}
        agregate = ["ALL [" + str(count_all) + "]"] + sorted({f"{k} [{v['modelsLive']}]" for k, v in filtered.items()})
        selection = xbmcgui.Dialog().select('Select ' + tag, agregate)
        if selection != -1:
            if selection == 0:
                utils.addon.setSetting("stripchattag", "")
            else:
                selected_url = str(agregate[selection]).split(' ')[0]
                utils.addon.setSetting("stripchattag", tag + selected_url)
            utils.refresh()
    except:
        pass


@site.register()
def topModels(url):
    import xbmcgui
    genders = [{"name": "Girls", "code": "female"}, {"name": "Couples", "code": "couple"}, 
               {"name": "Guys", "code": "male"}, {"name": "Trans", "code": "tranny"}]
    names = [item["name"] for item in genders]
    selection = xbmcgui.Dialog().select('Select Gender', names)
    if selection == -1:
        return
    gender_code = genders[selection]["code"]

    zone = ""
    if gender_code == "female":
        zones = [{"name": "Europe", "code": "eu"}, {"name": "North America", "code": "na"}, 
                {"name": "South America", "code": "sa"}, {"name": "Asia & Pacific", "code": "as"}, 
                {"name": "Africa", "code": "af"}]
        names = [item["name"] for item in zones]
        selection = xbmcgui.Dialog().select('Select zone', names)
        if selection == -1:
            return
        zone = zones[selection]["code"]

    periodes = [
        {"name": "Current Month Top", "url": "https://stripchat.com/api/front/v5/models/top?gender={0}&period=current&offset=0&limit=100&continent={1}".format(gender_code, zone)},
        {"name": "Last 24h Winners", "url": "https://stripchat.com/api/front/v4/models/top/hourly?gender={}".format(gender_code)},
        {"name": "Last Month Winners", "url": "https://stripchat.com/api/front/v5/models/top?gender={0}&period=monthly&offset=0&limit=100&continent={1}".format(gender_code, zone)},
        {"name": "Hall of Fame 2026", "url": "https://stripchat.com/api/front/v3/models/top/hallOfFame?year=2026&gender={}".format(gender_code)}
    ]
    names = [item["name"] for item in periodes]
    selection = xbmcgui.Dialog().select('Select Period', names)
    if selection == -1:
        return
    List(periodes[selection]["url"])


@site.register()
def ShowModelInfo():
    current = utils.addon.getSetting('stripchat_modelInfo') == "true"
    new_value = not current
    utils.addon.setSetting('stripchat_modelInfo', "true" if new_value else "false")
    utils.notify("Visible" if new_value else "Hidden", "Model Info")
    xbmc.executebuiltin('Container.Refresh')
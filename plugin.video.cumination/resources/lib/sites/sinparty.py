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

import re
import json
import sqlite3
import math
import json
import xbmcgui
import urllib.request
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
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


site = AdultSite('sinparty', '[COLOR hotpink]Sinparty[/COLOR]', 'https://sinparty.com/', 'https://content.spmediacdn.com/resources/img/logos/logo-sinparty-1200x630.jpg', 'sinparty', True, extract_meta=True)
# UA = "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

addon = utils.addon
bu = 'https://api.sinparty.com/v2/web/live-cams/web-rtc/{}?gender%5B%5D={}&per_page=100&page=1'     #&ethnicity%5B%5D=asian'
favorites = []

@site.register(default_mode=True)
def Main():
    global favorites
    favorites = getFavorites()

    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    site.add_dir('[COLOR red]Refresh Sinparty images[/COLOR]', '', 'clean_database', site.img_refresh, Folder=False)
    if favorites:  
        site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', '{}girls'.format(bu), 'onlineFav', site.img_favorites, 1)

    if female:
        site.add_dir('[COLOR hotpink]Female[/COLOR]', bu.format('girls', 'f'), 'List', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', '{0}couples'.format(bu), 'List', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male[/COLOR]', '{0}men'.format(bu), 'List', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', '{0}trans'.format(bu), 'List', '', '')

    utils.eod()


@site.register()
def List(url):
    global favorites
    favorites = getFavorites()
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    # req = urlreq.Request(url, headers={
    #     'User-Agent': UA,
    #     'Origin': site.url,
    #     'Referer': site.url
    # })

    categ_setting = utils.addon.getSetting('sinParty_categ')
    filter_setting = utils.addon.getSetting('sinParty_filter')
    if not categ_setting:
        categ_setting = ''
        filter_setting = ''
        utils.addon.setSetting('sinParty_categ', categ_setting)
        utils.addon.setSetting('sinParty_filter', filter_setting)

    url = (add_or_replace_param(url, categ_setting, filter_setting)).replace('&=', '')
    text = 'ALL' if categ_setting == '' else categ_setting.replace('[]', '') + '=' + filter_setting
    site.add_download_link(
        'Filter - currently: [COLOR fuchsia][B]' + text + '[/B][/COLOR] - '
        '[COLOR red][B]Change[/B][/COLOR]',
        url,
        'sinparty_select_filters',
        '',
        '',
        noDownload=True
    )

    try:
        response = utils._getHtml(url)
        data = json.loads(response)
    except Exception as e:
        xbmcgui.Dialog().textviewer("Error", f"URL: {url}\n{str(e)}")
        utils.kodilog(str(e))
        return None

    status = data.get("status", "Unknown")

    items = data.get("data", {}).get("items", [])
    if not items:
        utils.notify(filter_setting, "We're sorry, we could not find any live creators related to your search")
    
    for item in items:
        name = item.get("title")
        subject = ''
        if name == None:
            if any(item.get('Nickname') in name for name in favorites):
                name = '[COLOR yellow]★ [/COLOR]'
                fav = 'del'
            else:
                name = ''
                fav = 'add'
            name += item.get("Nickname") 
            img = item.get("Snapshot")
            if item.get('Age'):
                subject += u'[B][COLOR hotpink]Age:[/COLOR][/B] {}\n'.format(item.get('Age'))
            if item.get('Country'):
                subject += u'[B][COLOR hotpink]Country:[/COLOR][/B] {}\n'.format(item.get('Country'))
            if item.get('Headline'):
                subject += u'[B][COLOR hotpink]Topic:[/COLOR][/B] {}\n'.format(utils.cleantext(item.get('Headline')))
            if item.get('Languages'):
                subject += u'[B][COLOR hotpink]Languages:[/COLOR][/B] '
                subject += u', '.join(item.get('Languages'))                
            api_url = 'https://manifest-server.naiadsystems.com/live/s:{}.json?'.format(item.get('Nickname'))
        else:
            # if not item.get("isLive"):
            #     continue
            if any(item.get("title") in name for name in favorites):
                name = '[COLOR yellow]★ [/COLOR]'
                fav = 'del'
            else:
                name = ''
                fav = 'add'
            name += item.get("title") 

            if item.get('age'):
                subject += u'[B][COLOR hotpink]Age:[/COLOR][/B] {}\n'.format(item.get('age'))
            if item.get('country'):
                subject += u'[B][COLOR hotpink]Country:[/COLOR][/B] {}\n'.format(item.get('country'))
            if item.get('topic'):
                subject += u'[B][COLOR hotpink]Topic:[/COLOR][/B] {}\n'.format(utils.cleantext(item.get('topic')))
            if item.get('categories'):
                subject += u'[B][COLOR hotpink]Categories:[/COLOR][/B] '
                subject += u', '.join(item.get('categories'))

            img = item.get("thumbnail_url")
            api_url = 'https://api.sinparty.com/v2/web/live-cams/web-rtc/' + item.get('creator_user_hash')

        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(name))
        contextmenu=[(('[COLOR violet]Find recordings featuring [/COLOR]{}'.format(name), 'RunPlugin(' + contextrecord + ')'))]
        site.add_download_link(name, api_url, 'Playvid', img, subject.encode('utf-8') if utils.PY2 else subject, contextm=contextmenu, fav='add', noDownload=True)
    next_url, next_page, total_pages, is_last = sinparty_next_page(url, data)
    if not is_last and next_url:
        site.add_dir('Next Page... [COLOR hotpink]({}/{})[/COLOR]'.format(next_page, total_pages), next_url, 'List', site.img_next)

    utils.eod()


def sinparty_next_page(url, json_data):
    total = json_data.get("data", {}).get("total", 0)
    if not total:
        return None, None, None, True
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    current_page = int(query_params.get("page", ["1"])[0])
    per_page = int(query_params.get("per_page", ["100"])[0])
    total_pages = math.ceil(total / per_page)
    if current_page >= total_pages:
        return None, current_page, total_pages, True

    next_page = current_page + 1
    query_params["page"] = [str(next_page)]

    new_query = urlencode(query_params, doseq=True)
    next_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return next_url, next_page, total_pages, False



@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    try:
        response = utils._getHtml(url)
    except Exception as e:
        utils.kodilog("Error on utils._getHtml for Playvid SinParty - {m}: {e}".format(e=e, m=name))
        if '404' in str(e):
            utils.notify(name, 'Offline!')
        elif '403' in str(e):
            utils.notify(name, 'Private show!')
        else:
            utils.notify(name, str(e))
        return
    data = json.loads(response)
    if data.get("data", {}).get("isLive") == False:
        utils.notify(name, 'Model offline!')
        return
    if data.get("data", {}).get("type") == "private":
        utils.notify(name, 'In private show!')
        return
    videourl = data.get("data", {}).get("playback_url")
    if videourl == None:
        hls = data.get("formats", {}).get("mp4-hls", {})
        encodings = hls.get("encodings", [])

        sources = {}

        for enc in encodings:
            w = enc.get("videoWidth")
            h = enc.get("videoHeight")
            kbps = enc.get("videoKbps")
            url = enc.get("location")

            if w and h and url:
                label = f"{w}x{h} ({kbps} kbps)"
                sources[label] = url

        videourl = utils.selector(
            'Select quality',
            sources,
            setting_valid='qualityask',
            sort_by=lambda x: int(x.split('x')[1].split()[0]),
            reverse=True
        )

    vp.play_from_direct_link(videourl)


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % "sinparty.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % "sinparty.com")
            if showdialog:
                utils.notify('Finished', 'sinparty.com images cleared')
    except:
        pass

@site.register()
def sinparty_select_filters():
    url_filters = "https://api.sinparty.com/v2/web/live-cams/list/filters"

    try:
        response = utils._getHtml(url_filters)
        data = json.loads(response)
    except Exception as e:
        xbmcgui.Dialog().textviewer("SinParty Filters Error", str(e))
        return None, None

    filters = data.get("data", {}).get("filters", {})
    if not filters:
        xbmcgui.Dialog().textviewer("SinParty Filters", "No filters found")
        return None, None

    categ_list = sorted(filters.keys())
    categ_list = [" ALL (reset filters)"] + categ_list

    try:
        setting_val = int(addon.getSetting("sinParty_categask"))
    except:
        setting_val = None

    selected_categ = utils.selector(
        "Select category",
        categ_list,
        setting_valid="sinParty_categask" if setting_val is not None else False,
        sort_by=lambda x: x.lower(),
        reverse=False
    )
    if not selected_categ:
        return None, None

    if " ALL" in selected_categ:
        addon.setSetting("sinParty_categ", "")
        addon.setSetting("sinParty_filter", "")
        utils.refresh()
        return "ALL", None

    sub = filters.get(selected_categ, {})
    if isinstance(sub, list):
        subfilters = sub
    elif isinstance(sub, dict):
        subfilters = sub.get("girls") or sub.get("guys") or sub.get("trans") or []
    else:
        subfilters = []

    if not subfilters:
        xbmcgui.Dialog().textviewer("SinParty Filters", "No subfilters found for selected category")
        addon.setSetting("sinParty_categ", selected_categ)
        addon.setSetting("sinParty_filter", "")
        return selected_categ, None

    try:
        setting_val2 = int(addon.getSetting("sinParty_filterask"))
    except:
        setting_val2 = None

    selected_filter = utils.selector(
        f"Select filter for {selected_categ}",
        sorted(subfilters),
        setting_valid="sinParty_filterask" if setting_val2 is not None else False,
        sort_by=lambda x: x.lower(),
        reverse=False
    )

    addon.setSetting("sinParty_categ", selected_categ + '[]')
    addon.setSetting("sinParty_filter", selected_filter if selected_filter else "")
    utils.refresh()
    return selected_categ, selected_filter

def getFavorites():
    favorites = {}
    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT name, url, image FROM favorites WHERE mode='{}.Playvid'".format(site.name))
    favorites = [{"name": row[0], "url": row[1], "image": row[2]} for row in c.fetchall()]
    c.close()
    return favorites

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def add_or_replace_param(url, key, value):
    parsed = urlparse(url)

    params = parse_qs(parsed.query)

    params[key] = [value]

    new_query = urlencode(params, doseq=True)

    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return new_url

def http_head(url):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req) as response:
            return response.status
    except Exception as e:
        return e

@site.register()
def onlineFav():
    favorites = getFavorites()
    for fav in favorites:
        name  = fav.get("name")
        url   = fav.get("url")
        image = fav.get("image")
        try:
            status = http_head(url)
        except Exception as e:
            utils.kodilog("HEAD error for Playvid SinParty - {m}: {e}".format(e=e, m=name))
            utils.notify(name, str(e))
            continue

        if isinstance(status, Exception):
            err = str(status)
            utils.kodilog("HEAD exception for {m}: {e}".format(m=name, e=err))

            if '404' in err:
                utils.kodilog(name + ' Offline!')
            elif '403' in err:
                utils.kodilog(name + ' Private show!')
            else:
                utils.notify(name + ' - ' + err)
            continue

        if status == 404:
            utils.kodilog(name + ' Offline!')
            continue
        elif status == 403:
            utils.kodilog(name + ' Private show!')
            continue
        elif status >= 400:
            utils.kodilog(name + f" - Error {status}")
            continue

        # utils.notify(name, "Online!")
        site.add_download_link(name, url, 'Playvid', image)
    utils.eod()

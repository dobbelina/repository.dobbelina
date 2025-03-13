'''
    Cumination
    Copyright (C) 2015 Whitecream

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
import os
import sqlite3
from six.moves import urllib_parse
import six
import json
import random
import time
from resources.lib import utils
from resources.lib.adultsite import AdultSite

bu = 'https://chaturbate.com/'
rapi = 'https://chaturbate.com/api/ts/roomlist/room-list/'
tapi = 'https://chaturbate.com/api/ts/hashtags/tag-table-data/'
site = AdultSite('chaturbate', '[COLOR hotpink]Chaturbate[/COLOR]', bu, 'chaturbate.png', 'chaturbate', True)

addon = utils.addon
HTTP_HEADERS_IPAD = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B410 Safari/600.1.4'}


@site.register(default_mode=True)
def Main():
    female = addon.getSetting("chatfemale") == "true"
    male = addon.getSetting("chatmale") == "true"
    couple = addon.getSetting("chatcouple") == "true"
    trans = addon.getSetting("chattrans") == "true"

    site.add_dir('[COLOR red]Refresh Chaturbate images[/COLOR]', '', 'clean_database', '', Folder=False)
    # site.add_dir('[COLOR hotpink]Look for Online Models[/COLOR]', rapi + '?limit=100&offset=0&keywords=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Look for Online Models[/COLOR]', site.url + 'ax/search/?keywords=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Featured[/COLOR]', rapi + '?limit=100&offset=0', 'List', '', '')
    site.add_dir('[COLOR yellow]Current Hour\'s Top Cams[/COLOR]', bu + 'api/ts/contest/leaderboard/', 'topCams', '', '')
    site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', bu, 'onlineFav', '', '')
    site.add_dir('[COLOR yellow]Followed Cams[/COLOR]', rapi + '?enable_recommendations=true&follow=true&limit=100&offline=false&offset=0', 'List', '', '')

    if female:
        site.add_dir('[COLOR violet]Female[/COLOR]', rapi + '?genders=f&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - Female[/COLOR]', tapi + '?sort=ht&page=1&g=f&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Female[/COLOR]', rapi + '?genders=f&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=SA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=O&offset=0', 'List', '', '')
    if couple:
        site.add_dir('[COLOR violet]Couple[/COLOR]', rapi + '?genders=c&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - Couple[/COLOR]', tapi + '?sort=ht&page=1&g=c&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Couple[/COLOR]', rapi + '?genders=c&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=SA&offCoupleMaleset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=O&offset=0', 'List', '', '')
    if male:
        site.add_dir('[COLOR violet]Male[/COLOR]', rapi + '?genders=m&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - Male[/COLOR]', tapi + '?sort=ht&page=1&g=m&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Male[/COLOR]', rapi + '?genders=m&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=SA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=O&offset=0', 'List', '', '')
    if trans:
        site.add_dir('[COLOR violet]TransSexual[/COLOR]', rapi + '?genders=t&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - TransSexual[/COLOR]', tapi + '?sort=ht&page=1&g=t&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - TransSexual[/COLOR]', rapi + '?genders=t&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=SA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=O&offset=0', 'List', '', '')

    utils.eod()


def Online(stamp):
    days, weeks, years = None, None, None
    mins, secs = divmod(int(time.time()) - stamp, 60)
    hours, mins = divmod(mins, 60)
    if hours > 23:
        days, hours = divmod(hours, 24)
    if days and days > 6:
        weeks, days = divmod(days, 7)
    if weeks and weeks > 51:
        years, weeks = divmod(weeks, 52)
    if years:
        ret = '{:2d} years {:2d} weeks'.format(years, weeks)
    elif weeks:
        ret = '{:2d} weeks {:2d} days'.format(weeks, days)
    elif days:
        ret = '{:2d} days {:2d} hours'.format(days, hours)
    else:
        ret = '{:2d} hours {:2d} minutes'.format(hours, mins)
    ret = re.sub(r'(\s0\s\S+)', '', ret)
    ret = re.sub(r'(\s1\s\S+)s', r'\1', ret)
    return ret


@site.register()
def List(url, page=1):
    if 'follow=true' in url and 'offline=false' in url:
        site.add_dir('[COLOR yellow]Offline Rooms[/COLOR]', rapi + '?enable_recommendations=true&follow=true&limit=100&offline=true&offset=0', 'List', '', '')
    if 'follow=true' in url:
        login()
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)
    if not isinstance(page, int):
        page = 1

    listhtml = utils._getHtml(url)
    listhtml = json.loads(listhtml)
    models = listhtml.get('rooms')
    for model in models:
        name = model.get('username')
        videopage = '{0}{1}/'.format(bu, name)
        age = model.get('display_age')
        age = 'Unknown' if age is None else age
        location = model.get('location')
        if location:
            location = location.encode('utf8') if six.PY2 else location
            location = utils.cleantext(location)
        else:
            location = ''

        subject = model.get('subject')
        subject = subject.encode('utf8') if six.PY2 else subject
        subject = re.sub(r'<a.+', '', subject).strip()
        if 'offline=true' not in url:
            subject = utils.cleantext(subject) + "[CR][CR][COLOR deeppink]Location: [/COLOR]" + location + "[CR]" \
                + "[COLOR deeppink]Duration: [/COLOR]{0}[CR]".format(Online(model.get('start_timestamp'))) \
                + "[COLOR deeppink]Watching: [/COLOR]{0}[CR]".format(model.get('num_users')) \
                + "[COLOR deeppink]Followers: [/COLOR]{0}".format(model.get('num_followers'))
            name = '{0} [COLOR deeppink][{1}][/COLOR] {2}'.format(name, age, model.get('current_show'))
        else:
            subject = utils.cleantext(subject)
            if model.get('start_timestamp'):
                ago = re.sub(r'^\s*(\d+\s+\S+).*$', r'\1', Online(model.get('start_timestamp')))
                name = '{0} [COLOR deeppink][{1}][/COLOR] [COLOR blue]{2} ago[/COLOR]'.format(name, age, ago)
            else:
                name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)
        tags = model.get('tags')
        if tags:
            tags = '[COLOR deeppink]#[/COLOR]' + ', [COLOR deeppink]#[/COLOR]'.join(tags)
            tags = tags.encode('utf-8') if six.PY2 else tags
            subject += "[CR][CR]" + tags
        img = model.get('img')

        id = model.get('username')
        follow = model.get('is_following')
        contextfollow = (utils.addon_sys + "?mode=chaturbate.Follow&id=" + urllib_parse.quote_plus(id))
        contextunfollow = (utils.addon_sys + "?mode=chaturbate.Unfollow&id=" + urllib_parse.quote_plus(id))
        contextmenu = [('[COLOR violet]Follow [/COLOR]{}'.format(name), 'RunPlugin(' + contextfollow + ')')] if not follow else [('[COLOR violet]Unfollow [/COLOR]{}'.format(name), 'RunPlugin(' + contextunfollow + ')')]

        site.add_download_link(name, videopage, 'Playvid', img, subject, contextm=contextmenu, noDownload=True)

    total_items = listhtml.get('total_count')
    nextp = (page * 100) < total_items
    if nextp:
        next = (page * 100) + 1
        lastpg = -1 * (-total_items // 100)
        page = page + 1
        nurl = re.sub(r'offset=\d+', 'offset={0}'.format(next), url)
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page - 1, lastpg), nurl, 'List', site.img_next, page)

    utils.eod()


@site.register()
def SList(url):
    hdr = utils.base_hdrs.copy()
    hdr.update({'X-Requested-With': 'XMLHttpRequest'})
    listhtml = utils._getHtml(url, site.url, headers=hdr)
    jlist = json.loads(listhtml)
    for model in jlist.get('online', []):
        img = 'https://thumb.live.mmcdn.com/riw/{}.jpg'.format(model)
        contextfollow = (utils.addon_sys + "?mode=chaturbate.Follow&id=" + urllib_parse.quote_plus(model))
        contextunfollow = (utils.addon_sys + "?mode=chaturbate.Unfollow&id=" + urllib_parse.quote_plus(model))
        contextmenu = [('[COLOR violet]Follow [/COLOR]{}'.format(model), 'RunPlugin(' + contextfollow + ')'), ('[COLOR violet]Unfollow [/COLOR]{}'.format(model), 'RunPlugin(' + contextunfollow + ')')]
        videopage = '{0}{1}/'.format(bu, model)
        site.add_download_link(model, videopage, 'Playvid', img, contextm=contextmenu, noDownload=True)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".live.mmcdn.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".live.mmcdn.com")
            if showdialog:
                utils.notify('Finished', 'Chaturbate images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    playmode = int(addon.getSetting('chatplay'))
    listhtml = utils._getHtml(url, headers=HTTP_HEADERS_IPAD)

    r = re.search(r'initialRoomDossier\s*=\s*"([^"]+)', listhtml)
    if r:
        data = six.b(r.group(1)).decode('unicode-escape')
        data = data if six.PY3 else data.encode('utf8')
        data = json.loads(data)
    else:
        data = False

    if data:
        m3u8stream = data['hls_source']
    else:
        m3u8stream = False

    m3u8stream = m3u8stream.replace('playlist.m3u8', 'playlist_sfm4s.m3u8').replace('live-hls', 'live-c-fhls').replace('live-edge', 'live-c-fhls')

    if playmode == 0:
        if m3u8stream:
            videourl = "{0}|{1}".format(m3u8stream, urllib_parse.urlencode(HTTP_HEADERS_IPAD))
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    elif playmode == 1:
        if data:
            streamserver = "rtmp://{}/live-edge".format(m3u8stream.split('/')[2])
            # streamserver = "rtmp://{}/live-edge".format(data['flash_host'])
            modelname = data['broadcaster_username']
            username_full = data['viewer_username']
            username = 'anonymous'
            room_pass = data['room_pass']
            swfurl = 'https://ssl-ccstatic.highwebmedia.com/theatermodeassets/CBV_TS_v1.0.swf'
            edge_auth = data['edge_auth']
            videourl = "%s app=live-edge swfUrl=%s pageUrl=%s conn=S:%s conn=S:%s conn=S:3.22 conn=S:%s conn=S:%s conn=S:%s playpath=mp4" % (streamserver, swfurl, url, username_full, modelname, username, room_pass, edge_auth)
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    vp = utils.VideoPlayer(name)
    vp.IA_check = 'IA'
    vp.play_from_direct_link(videourl)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = urllib_parse.quote_plus(keyword)
        url += title
        SList(url)


@site.register()
def topCams(url):
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)
    response = utils._getHtml(url)
    jsonTop = json.loads(response)['top']
    for iTop in jsonTop:
        subject = '[COLOR deeppink]Name: [/COLOR]' + iTop['room_user'] + '[CR]' \
            + '[CR][COLOR deeppink]Points: [/COLOR]' + str(iTop['points']) + '[CR]' \
            + '[COLOR deeppink]Watching: [/COLOR]' + str(iTop['viewers'])
        site.add_download_link(iTop['room_user'], bu + iTop['room_user'] + '/', 'Playvid',
                               iTop['image_url'], subject, noDownload=True)
    utils.eod()


@site.register()
def Tags(url, page=1):
    cat = re.search(r'&g=([^&]*)', url).group(1)
    html = utils.getHtml(url, site.url)
    jdata = json.loads(html)
    total = jdata["total"]
    for tag in jdata["hashtags"]:
        name = tag["hashtag"]
        count = tag["room_count"]
        img = tag["top_rooms"][0].get("img", '') if tag["top_rooms"] else ''
        tagurl = rapi + '?genders={0}&hashtags={1}&limit=100&offset=0'.format(cat, name)
        name += ' [COLOR hotpink][' + str(count) + '][/COLOR]'
        site.add_dir(name, tagurl, 'List', img, 1)
    if page * 100 < total:
        lastpg = -1 * (-total // 100)
        np_url = url.replace('&page={}'.format(page), '&page={}'.format(page + 1))
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page, lastpg), np_url, 'Tags', site.img_next, page=page + 1)
    utils.eod()


@site.register()
def onlineFav(url):
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)

    wmArray = ["C9m5N", "tfZSl", "jQrKO", "5XO2a", "WXomN", "zM6MR", "Lb2aB", "cIbs3", "zM6MR", "mnzQo", "N6TZA"]
    chaturbate_url = 'https://chaturbate.com/affiliates/api/onlinerooms/?format=json&wm=' + random.choice(wmArray)
    data_chat = utils._getHtml(chaturbate_url, '')
    model_list = json.loads(data_chat)
    model_lookup = {item['username']: item for item in model_list}
    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='chaturbate.Playvid'")
    result = c.fetchall()
    c.close()
    for (name, url, image) in result:
        stripped_name = name.split('[COLOR')[0].strip()
        if stripped_name in model_lookup:
            model = model_lookup[stripped_name]
            image = model["image_url"]
            current_show = ''
            if "current_show" in model:
                if model["current_show"] != "public":
                    current_show = '[COLOR blue] {}[/COLOR]'.format(model["current_show"])
            subject = model["room_subject"] if utils.PY3 else model["room_subject"].encode('utf8')
            location = model["location"] if utils.PY3 else model["location"].encode('utf8')
            subject = utils.cleantext(subject.split(' #')[0]) + "[CR][CR][COLOR deeppink]Location: [/COLOR]" + location + "[CR]" \
                + "[COLOR deeppink]Duration: [/COLOR]" + str(round(model["seconds_online"] / 3600, 1)) + " hrs[CR]" \
                + "[COLOR deeppink]Watching: [/COLOR]" + str(model["num_users"]) + " viewers"
            tags = '[COLOR deeppink]#[/COLOR]' + ', [COLOR deeppink]#[/COLOR]'.join(model["tags"])
            tags = tags if utils.PY3 else tags.encode('utf8')
            subject += "[CR][CR]" + tags

            site.add_download_link(name + current_show, url, 'Playvid', image, utils.cleantext(subject), noDownload=True)
    utils.eod()


def login():
    sessionid = addon.getSetting('sessionid')
    if len(sessionid) == 32:
        session_cookie = get_cookie()
        if sessionid not in session_cookie:
            cookie = {'solution': {"cookies": [{'name': "sessionid", 'domain': ".chaturbate.com", 'value': sessionid, 'path': '/', 'secure': True, 'expiry': None, 'httpOnly': None}],
                                   "userAgent": utils.USER_AGENT}}
            utils.savecookies(cookie)

    url = 'https://chaturbate.com/followed-cams/'
    loginurl = 'https://chaturbate.com/auth/login/?next=/followed-cams/'

    loginhtml = utils._getHtml(url, site.url)
    if '<h1>Chaturbate Login</h1>' not in loginhtml:
        return

    username = utils._get_keyboard(default='', heading='Input your Chaturbate username')
    password = utils._get_keyboard(default='', heading='Input your Chaturbate password', hidden=True)

    match = re.compile(r'"csrfmiddlewaretoken"\s+value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(loginhtml)
    if not match:
        return

    csrfmiddlewaretoken = match[0]
    hdr = utils.base_hdrs
    hdr.update({'Referer': 'https://chaturbate.com/auth/login/?next=/followed-cams/'})
    postRequest = {"next": "/followed-cams/",
                   "csrfmiddlewaretoken": csrfmiddlewaretoken,
                   "username": username,
                   "password": password,
                   "rememberme": "on"}
    response = utils._postHtml(loginurl, headers=hdr, form_data=postRequest)
    if '<h1>Chaturbate Login</h1>' in response:
        utils.notify('Chaturbate', 'Login failed please check your username and password')


@site.register()
def Unfollow(id):
    url = 'https://chaturbate.com/follow/unfollow/{}/'.format(id)
    html = utils._getHtml(url, site.url)
    if '<h1>Chaturbate Login</h1>' in html:
        login()
        html = utils._getHtml(url, site.url)
    match = re.compile(r'"csrfmiddlewaretoken"\s+value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if not match:
        return
    csrfmiddlewaretoken = match[0]
    hdr = utils.base_hdrs
    hdr.update({'Referer': 'https://chaturbate.com/'})
    postRequest = {"csrfmiddlewaretoken": csrfmiddlewaretoken}
    response = utils._postHtml(url, headers=hdr, form_data=postRequest)
    if '"following": false' in response:
        utils.notify('Chaturbate', 'NOT FOLLOWING [COLOR hotpink]{}[/COLOR]'.format(id))
        utils.refresh()


@site.register()
def Follow(id):
    url = 'https://chaturbate.com/follow/follow/{}/'.format(id)
    html = utils._getHtml(url, site.url)
    if '<h1>Chaturbate Login</h1>' in html:
        login()
        html = utils._getHtml(url, site.url)
    match = re.compile(r'"csrfmiddlewaretoken"\s+value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if not match:
        return
    csrfmiddlewaretoken = match[0]
    hdr = utils.base_hdrs
    hdr.update({'Referer': 'https://chaturbate.com/'})
    postRequest = {"csrfmiddlewaretoken": csrfmiddlewaretoken}
    response = utils._postHtml(url, headers=hdr, form_data=postRequest)
    if '"following": true' in response:
        utils.notify('Chaturbate', 'FOLLOWING [COLOR hotpink]{}[/COLOR]'.format(id))
        utils.refresh()


def get_cookie():
    domain = ".chaturbate.com"
    cookiestr = ""
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'sessionid':
            cookiestr = cookie.value
    return cookiestr

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

bu = 'https://chaturbate.com/'
site = AdultSite('chaturbate', '[COLOR hotpink]Chaturbate[/COLOR]', bu, 'chaturbate.png', 'chaturbate', True)

addon = utils.addon
HTTP_HEADERS_IPAD = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B410 Safari/600.1.4'}


@site.register(default_mode=True)
def Main():
    female = True if addon.getSetting("chatfemale") == "true" else False
    male = True if addon.getSetting("chatmale") == "true" else False
    couple = True if addon.getSetting("chatcouple") == "true" else False
    trans = True if addon.getSetting("chattrans") == "true" else False

    site.add_dir('[COLOR red]Refresh Chaturbate images[/COLOR]', '', 'clean_database', '', Folder=False)
    site.add_dir('[COLOR hotpink]Look for Model[/COLOR]', bu, 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Featured[/COLOR]', bu + '?page=1', 'List', '', '')
    site.add_dir('[COLOR yellow]Current Hour\'s Top Cams[/COLOR]', bu + 'api/ts/contest/leaderboard/', 'topCams', '', '')

    if female:
        site.add_dir('[COLOR hotpink]Female[/COLOR]', bu + 'female-cams/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Female[/COLOR]', bu + 'new-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Female[/COLOR]', bu + 'teen-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]18 to 21 Cams - Female[/COLOR]', bu + '18to21-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Female[/COLOR]', bu + '20to30-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Female[/COLOR]', bu + '30to50-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Female[/COLOR]', bu + 'mature-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]HD Cams - Female[/COLOR]', bu + 'hd-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Female[/COLOR]', bu + 'north-american-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Female[/COLOR]', bu + 'south-american-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Female[/COLOR]', bu + 'euro-russian-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Philippines Cams - Female[/COLOR]', bu + 'philippines-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Female[/COLOR]', bu + 'asian-cams/female/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Female[/COLOR]', bu + 'other-region-cams/female/?page=1', 'List', '', '')
    if couple:
        site.add_dir('[COLOR hotpink]Couple[/COLOR]', bu + 'couple-cams/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Couple[/COLOR]', bu + 'new-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Couple[/COLOR]', bu + 'teen-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]18 to 21 Cams - Couple[/COLOR]', bu + '18to21-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Couple[/COLOR]', bu + '20to30-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Couple[/COLOR]', bu + '30to50-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Couple[/COLOR]', bu + 'mature-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]HD Cams - Couple[/COLOR]', bu + 'hd-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Couple[/COLOR]', bu + 'north-american-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Couple[/COLOR]', bu + 'south-american-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Couple[/COLOR]', bu + 'euro-russian-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Philippines Cams - Couple[/COLOR]', bu + 'philippines-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Couple[/COLOR]', bu + 'asian-cams/couple/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Couple[/COLOR]', bu + 'other-region-cams/couple/?page=1', 'List', '', '')
    if male:
        site.add_dir('[COLOR hotpink]Male[/COLOR]', bu + 'male-cams/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Male[/COLOR]', bu + 'new-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Male[/COLOR]', bu + 'teen-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]18 to 21 Cams - Male[/COLOR]', bu + '18to21-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Male[/COLOR]', bu + '20to30-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Male[/COLOR]', bu + '30to50-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Male[/COLOR]', bu + 'mature-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]HD Cams - Male[/COLOR]', bu + 'hd-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Male[/COLOR]', bu + 'north-american-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Male[/COLOR]', bu + 'south-american-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Male[/COLOR]', bu + 'euro-russian-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Philippines Cams - Male[/COLOR]', bu + 'philippines-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Male[/COLOR]', bu + 'asian-cams/male/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Male[/COLOR]', bu + 'other-region-cams/male/?page=1', 'List', '', '')
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', bu + 'transsexual-cams/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Transsexual[/COLOR]', bu + 'new-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Transsexual[/COLOR]', bu + 'teen-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]18 to 21 Cams - Transsexual[/COLOR]', bu + '18to21-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Transsexual[/COLOR]', bu + '20to30-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Transsexual[/COLOR]', bu + '30to50-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Transsexual[/COLOR]', bu + 'mature-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]HD Cams - Transsexual[/COLOR]', bu + 'hd-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Transsexual[/COLOR]', bu + 'north-american-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Transsexual[/COLOR]', bu + 'south-american-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Transsexual[/COLOR]', bu + 'euro-russian-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Philippines Cams - Transsexual[/COLOR]', bu + 'philippines-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Transsexual[/COLOR]', bu + 'asian-cams/transsexual/?page=1', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Transsexual[/COLOR]', bu + 'other-region-cams/transsexual/?page=1', 'List', '', '')
    # new
    # site.add_dir('[COLOR hotpink]New Cams[/COLOR]', bu + 'new-cams/?page=1', 'List', '', '')
    # age
    # site.add_dir('[COLOR hotpink]Teen Cams (18+)[/COLOR]', bu + 'teen-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]18 to 21 Cams[/COLOR]', bu + '18to21-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]20 to 30 Cams[/COLOR]', bu + '20to30-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]30 to 50 Cams[/COLOR]', bu + '30to50-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]Mature Cams (50+)[/COLOR]', bu + 'mature-cams/?page=1', 'List', '', '')
    # status
    # site.add_dir('[COLOR hotpink]HD Cams[/COLOR]', bu + 'hd-cams/?page=1', 'List', '', '')
    # region
    # site.add_dir('[COLOR hotpink]North American Cams[/COLOR]', bu + 'north-american-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]South American Cams[/COLOR]', bu + 'south-american-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]Euro Russian Cams[/COLOR]', bu + 'euro-russian-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]Philippines Cams[/COLOR]', bu + 'philippines-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]Asian Cams[/COLOR]', bu + 'asian-cams/?page=1', 'List', '', '')
    # site.add_dir('[COLOR hotpink]Other Region Cams[/COLOR]', bu + 'other-region-cams/?page=1', 'List', '', '')

    utils.eod()


@site.register()
def List(url, page=1):
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)

    listhtml = utils._getHtml(url)
    match = re.compile(r'room_list_room".+?href="([^"]+).+?src="([^"]+).+?<div[^>]+>([^<]+)</div>.+?href[^>]+>([^<]+)<.+?age[^>]+>([^<]+).+?title="([^"]+).+?location.+?>([^<]+).+?cams">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, status, name, age, subject, location, duration in match:
        name = utils.cleantext(name.strip())
        age = utils.cleantext(age.strip())
        subject = utils.cleantext(subject.strip()) + "[CR][COLOR deeppink]Location: [/COLOR]" + utils.cleantext(location.strip()) + "[CR]" + utils.cleantext(duration.strip())
        status = utils.cleantext(status.replace("[CR]", "").strip())
        name = name + " [COLOR deeppink][" + age + "][/COLOR] " + status
        videopage = bu[:-1] + videopage
        site.add_download_link(name, videopage, 'Playvid', img, subject, noDownload=True)

    nextp = re.compile(r'<a\s*href="([^"]+)"\s*class="next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        page = page + 1 if page else 2
        next = bu[:-1] + nextp.group(1)
        site.add_dir('Next Page (' + str(page) + ')', next, 'List', site.img_next, page)

    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".highwebmedia.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".highwebmedia.com")
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

    if playmode == 0:
        if m3u8stream:
            videourl = "{0}|{1}".format(m3u8stream, urllib_parse.urlencode(HTTP_HEADERS_IPAD))
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    elif playmode == 1:
        if data:
            streamserver = "rtmp://{}/live-edge".format(data['flash_host'])
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
    vp.play_from_direct_link(videourl)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = urllib_parse.quote_plus(keyword)
        searchUrl = searchUrl + title + '/'
        Playvid(searchUrl, title)


@site.register()
def topCams(url):
    response = utils._getHtml(url)
    jsonTop = json.loads(response)['top']
    for iTop in jsonTop:
        subject = 'Name: ' + iTop['room_user'] + '\n'
        subject = subject + 'Points: ' + str(iTop['points']) + '\n'
        subject = subject + 'Watching: ' + str(iTop['viewers'])
        site.add_download_link(iTop['room_user'], bu + iTop['room_user'] + '/', 'Playvid',
                               iTop['image_url'], subject, noDownload=True)
    utils.eod()

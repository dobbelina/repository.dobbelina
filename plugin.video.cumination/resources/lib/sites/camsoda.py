'''
    Cumination
    Copyright (C) 2016 Whitecream, hdgdl, Team Cumination
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
import random
import sqlite3
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('camsoda', '[COLOR hotpink]Camsoda[/COLOR]', 'https://www.camsoda.com', 'camsoda.png', 'camsoda', True)
addon = utils.addon


@site.register(default_mode=True)
def Main():
    female = addon.getSetting("chatfemale") == "true"
    male = addon.getSetting("chatmale") == "true"
    couple = addon.getSetting("chatcouple") == "true"
    trans = addon.getSetting("chattrans") == "true"
    site.add_dir('[COLOR red]Refresh Camsoda images[/COLOR]', '', 'clean_database', '', Folder=False)
    if female:
        site.add_dir('[COLOR violet]Female[/COLOR]', site.url + '/api/v1/browse/react?gender-hide=c,t,m', 'List', '', 1)
        site.add_dir('[COLOR hotpink]North America - Female[/COLOR]', site.url + '/api/v1/browse/react/girls/region/usa?gender-hide=c,t,m', 'List', '', 1)
        site.add_dir('[COLOR hotpink]Central/South America - Female[/COLOR]', site.url + '/api/v1/browse/react/girls/region/central-south-america?gender-hide=c,t,m', 'List', '', 1)
        site.add_dir('[COLOR hotpink]Europe - Female[/COLOR]', site.url + '/api/v1/browse/react/girls/region/europe?gender-hide=c,t,m', 'List', '', 1)
        site.add_dir('[COLOR hotpink]Eastern Europe - Female[/COLOR]', site.url + '/api/v1/browse/react/girls/region/eastern-europe?gender-hide=c,t,m', 'List', '', 1)
        site.add_dir('[COLOR hotpink]Asia - Female[/COLOR]', site.url + '/api/v1/browse/react/girls/region/asia?gender-hide=c,t,m', 'List', '', 1)
    if couple:
        site.add_dir('[COLOR violet]Couple[/COLOR]', site.url + '/api/v1/browse/react?gender-hide=f,t,m', 'List', '', 1)
    if male:
        site.add_dir('[COLOR violet]Male[/COLOR]', site.url + '/api/v1/browse/react?gender-hide=c,t,f', 'List', '', 1)
    if trans:
        site.add_dir('[COLOR violet]Transexual[/COLOR]', site.url + '/api/v1/browse/react?gender-hide=c,f,m', 'List', '', 1)

    utils.eod()


@site.register()
def List(url, page):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    response = utils._getHtml(url + '&p={}'.format(page))
    jd = json.loads(response)
    camgirls = jd.get('userList')
    for camgirl in camgirls:
        name = camgirl.get('displayName')
        name = name if utils.PY3 else name.encode('utf8')
        subject = camgirl.get('subjectText')
        subject += u'[CR][CR][COLOR deeppink] Viewers: [/COLOR]{}[CR]'.format(camgirl.get('connectionCount'))
        if camgirl.get('status'):
            subject += u'[COLOR deeppink] Status: [/COLOR]{}[CR]'.format(camgirl.get('status'))
        subject = subject if utils.PY3 else subject.encode('utf8')
        # cid = camgirl.get('id')
        username = camgirl.get('username')
        img = camgirl.get('thumbUrl')
        fanart = camgirl.get('offlinePictureUrl')
        # videourl = '{0}/api/v1/video/vtoken/{1}'.format(site.url, cid)
        videourl = '{0}/api/v1/chat/react/{1}'.format(site.url, username)
        site.add_download_link(name, videourl, 'Playvid', img, subject, noDownload=True, fanart=fanart)
    perPageCount = jd.get('perPageCount')
    totalCount = jd.get('totalCount')
    if (perPageCount * page) < totalCount:
        lastpg = -1 * (-totalCount // perPageCount)
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page, lastpg), url, 'List', site.img_next, page + 1)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            lst = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".camsoda.com")
            for row in lst:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".camsoda.com")
            if showdialog:
                utils.notify('Finished', 'Camsoda images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    if 'm3u8' not in url:
        url = url + "?username=guest_" + str(random.randrange(100, 55555))
        response = json.loads(utils._getHtml(url))
        data = response.get('stream')
        if len(data.get('edge_servers', [])) > 0:
            videourl = "https://" + random.choice(data['edge_servers']) + "/" + data['stream_name'] + "_v1/index.ll.m3u8?token=" + data['token']
            videourl += '|User-Agent=iPad&verifypeer=false'
            vp = utils.VideoPlayer(name)
            vp.play_from_direct_link(videourl)
        else:
            utils.notify('Finished', 'Model gone Offline or Private')

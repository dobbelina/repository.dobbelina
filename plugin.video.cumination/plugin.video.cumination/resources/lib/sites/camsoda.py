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
import time
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('camsoda', '[COLOR hotpink]Camsoda[/COLOR]', 'https://www.camsoda.com', 'camsoda.png', 'camsoda', True)


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR red]Refresh Camsoda images[/COLOR]', '', 'clean_database', '', Folder=False)
    List(site.url + '/api/v1/browse/online')
    utils.eod()


@site.register()
def List(url):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    response = utils._getHtml(url)
    camgirls = json.loads(response)['results']
    for camgirl in camgirls:
        if 'tpl' in list(camgirl.keys()):
            camgirl = camgirl.get('tpl')
            if type(camgirl) is dict:
                name = camgirl.get('2')
                name = name if utils.PY3 else name.encode('utf8')
                subject = camgirl.get('6')
                subject += u'[CR][CR][COLOR deeppink] Viewers: [/COLOR]{}[CR]'.format(camgirl.get('4'))
                if camgirl.get('3'):
                    subject += u'[COLOR deeppink] Status: [/COLOR]{}[CR]'.format(camgirl.get('3'))
                subject = subject if utils.PY3 else subject.encode('utf8')
                id = camgirl.get('1')
                img = camgirl.get('10')
                img = 'http:' + img if img.startswith('//)') else img.replace('https:', 'http:')
                fanart = 'http:' + camgirl.get('15') if camgirl.get('15') else None
            elif type(camgirl) is list:
                name = camgirl[2]
                name = name if utils.PY3 else name.encode('utf8')
                subject = camgirl[6]
                subject = subject if utils.PY3 else subject.encode('utf8')
                id = camgirl[1]
                img = 'http:' + camgirl[10]
                fanart = None
        else:
            name = camgirl['display_name'] if utils.PY3 else camgirl['display_name'].encode('utf8')
            subject = camgirl['subject_html'] if utils.PY3 else camgirl['subject_html'].encode('utf8')
            id = camgirl['username']
            img = 'https://md.camsoda.com/thumbs/%s.jpg?cb=%s' % (id, int(time.time()))
        videourl = '{0}/api/v1/video/vtoken/{1}'.format(site.url, id)
        site.add_download_link(name, videourl, 'Playvid', img, subject, noDownload=True, fanart=fanart)
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
    url = url + "?username=guest_" + str(random.randrange(100, 55555))
    response = utils._getHtml(url)
    data = json.loads(response)
    if "camhouse" in data['stream_name']:
        videourl = "https://camhouse.camsoda.com/" + data['app'] + "/mp4:" + data['stream_name'] + "_h264_aac_480p/playlist.m3u8?token=" + data['token']
    elif "enc" in data['stream_name']:
        if len(data['edge_servers']) > 0:
            videourl = "https://" + random.choice(data['edge_servers']) + "/" + data['app'] + "/mp4:" + data['stream_name'] + "_h264_aac_480p/playlist.m3u8?token=" + data['token']
        else:
            videourl = ""
            utils.notify('Finished', 'Model gone Offline')
    else:
        if len(data['edge_servers']) > 0:
            videourl = "https://" + random.choice(data['edge_servers']) + "/" + data['stream_name'] + "_v1/index.m3u8?token=" + data['token']
        else:
            videourl = ""
            utils.notify('Finished', 'Model gone Offline or Private')
    if videourl:
        videourl += '|User-Agent=iPad&verifypeer=false'
        vp = utils.VideoPlayer(name)
        vp.play_from_direct_link(videourl)

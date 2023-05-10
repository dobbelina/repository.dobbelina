'''
    Cumination
    Copyright (C) 2017 Whitecream, hdgdl
    Copyright (C) 2020 Team Cumination
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
import json
# import websocket
import math
from resources.lib import utils
from resources.lib import favorites
from resources.lib.adultsite import AdultSite

site = AdultSite('streamate', '[COLOR hotpink]streamate.com[/COLOR]', 'http://www.streamate.com', 'streamate.png', 'streamate', True)


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR red]Refresh streamate.com images[/COLOR]', '', 'clean_database', '', Folder=False)
    site.add_dir('[COLOR hotpink]Search + Fav add[/COLOR]', 'https://www.streamate.com/cam/', 'Search', site.img_search)
    List('https://member.naiadsystems.com/search/v3/performers?domain=streamate.com&from=0&size=100&filters=gender:f,ff,mf,tm2f,g%3Bonline:true&genderSetting=f')
    utils.eod()


@site.register()
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    try:
        headers = {"platform": "SCP",
                   "smtid": "ffffffff-ffff-ffff-ffff-ffffffffffffG0000000000000",
                   "smeid": "ffffffff-ffff-ffff-ffff-ffffffffffffG0000000000000",
                   "smvid": "ffffffff-ffff-ffff-ffff-ffffffffffffG0000000000000",
                   "User-Agent": utils.USER_AGENT}
        data = utils._getHtml(url, headers=headers)
    except:
        return None
    model_list = json.loads(data)
    total_models = model_list.get('totalResultCount')
    for camgirl in model_list['performers']:
        img = "http://m1.nsimg.net/media/snap/{0}.jpg".format(camgirl.get('id'))
        status = 'HD' if camgirl.get('highDefinition') else ''
        name = "{0} [COLOR deeppink][{1}][/COLOR] {2}".format(camgirl.get('nickname'), camgirl.get('age'), status)
        subject = '{0}[CR][COLOR deeppink]Location: [/COLOR]{1}'.format(utils.cleantext(camgirl.get('headlineMessage', '')), camgirl.get('country'))
        site.add_download_link(name, '{0}$${1}'.format(camgirl.get('nickname'), camgirl.get('id')), 'Playvid', img, subject, noDownload=True)
    if total_models > page * 100:
        url = re.sub(r"&from=\d+", "&from={0}".format(page * 100), url)
        lastpg = math.ceil(total_models / 100)
        site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(page, lastpg), url, 'List', site.img_next, page + 1)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % "m1.nsimg.net")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % "m1.nsimg.net")
            if showdialog:
                utils.notify('Finished', 'streamate.com images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    url, performerID = url.split('$$')

    # response = utils._getHtml("https://streamate.com/ajax/config/?name=" + url + "&sakey=&sk=streamate.com&userid=0&version=2.2.0&ajax=1")
    # data = json.loads(response)

    # host = data['liveservices']['host'] + "/socket.io/?puserid=" + performerID + "&EIO=3&transport=websocket"
    # ws = websocket.WebSocket()
    # ws = websocket.create_connection(host)

    # ws.send('40/live')

    # quitting = 0
    # i = 0
    # while quitting == 0:
    #     i += 1
    #     message = ws.recv()
    #     match = re.compile('performer offline', re.DOTALL | re.IGNORECASE).findall(message)
    #     if match:
    #         quitting = 1
    #         ws.close()
    #         utils.notify('Model is offline')
    #         return None

    #     match = re.compile('isPaid":true', re.DOTALL | re.IGNORECASE).findall(message)
    #     if match:
    #         quitting = 1
    #         ws.close()
    #         utils.notify('Model not in freechat')
    #         return None

    #     if message == '40/live':
    #         ws.close()
    #         quitting = 1
    #         playmode = int(utils.addon.getSetting('chatplay'))
    #         videourl = ''
    #         response = utils._getHtml("https://manifest-server.naiadsystems.com/live/s:{0}.json?last=load&format=mp4-hls".format(url))
    #         data = json.loads(response).get('formats')

    #         if playmode == 0:
    #             videourl = data.get('mp4-hls').get('manifest')

    #         elif playmode == 1:
    #             sources = {'{0}p'.format(item['videoHeight']): item['location'] for item in data.get('mp4-rtmp').get('encodings')}
    #             videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)

    videourl = ''
    try:
        response = utils._getHtml("https://manifest-server.naiadsystems.com/live/s:{0}.json?last=load&format=mp4-hls".format(url))
        data = json.loads(response).get('formats')
    except:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
        return

    playmode = int(utils.addon.getSetting('chatplay'))
    if playmode == 0:
        videourl = data.get('mp4-hls').get('manifest')
    elif playmode == 1:
        sources = {'{0}p'.format(item['videoHeight']): item['location'] for item in data.get('mp4-rtmp').get('encodings')}
        videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)

    if videourl:
        vp = utils.VideoPlayer(name)
        vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
        return


@site.register()
def Search(url):
    keyword = utils._get_keyboard(heading="Searching for...")
    if (not keyword):
        return False, 0
    try:
        response = utils.getHtml(url + keyword)
    except:
        utils.notify('Model not found - try again')
        return None
    match = re.compile("p_signupargs: 'smid%3D([^']+)'", re.DOTALL | re.IGNORECASE).findall(response)
    if match:
        utils.notify('Found ' + keyword + ' adding to favorites now')
        img = "http://m1.nsimg.net/media/snap/" + match[0] + ".jpg"
        performerID = match[0]
        name = keyword
        favorites.Favorites('add', 'Playvid', name, performerID, img)

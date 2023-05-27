'''
    Cumination
    Copyright (C) 2016 Whitecream, hdgdl

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
import os
import sqlite3
import time
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('naked', '[COLOR hotpink]Naked[/COLOR]', 'https://www.naked.com/', 'naked.png', 'naked', True)


@site.register(default_mode=True)
def Main():
    female = True if utils.addon.getSetting("chatfemale") == "true" else False
    male = True if utils.addon.getSetting("chatmale") == "true" else False
    trans = True if utils.addon.getSetting("chattrans") == "true" else False
    site.add_dir('[COLOR red]Refresh naked.com images[/COLOR]', '', 'clean_database', '', Folder=False)
    if female:
        site.add_dir('[COLOR hotpink]Females[/COLOR]', site.url + 'live/girls/', 'List', '', 1)
    if male:
        site.add_dir('[COLOR hotpink]Males[/COLOR]', site.url + 'live/guys/', 'List', '', 1)
    if trans:
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', site.url + 'live/trans/', 'List', '', 1)
    utils.eod()


@site.register()
def List(url):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    data = utils._getHtml(url, site.url)
    data = re.compile(r"models':\s*(.*?),\s*'", re.DOTALL | re.IGNORECASE).findall(data)[0]
    data = re.sub(r'\s\s+', '', data)
    data = data[:-2] + ']'
    models = json.loads(data)
    for model in models:
        name = model.get('model_seo_name').replace('-', ' ').title()
        age = model.get('age')
        subject = utils.cleantext(model.get('tagline') if utils.PY3 else model.get('tagline').encode('utf8'))
        if model.get('location'):
            subject += "[CR][CR][COLOR deeppink]Location: [/COLOR]{0}[CR][CR]".format(
                model.get('location') if utils.PY3 else model.get('location').encode('utf8'))
        if model.get('topic'):
            subject += utils.cleantext(model.get('topic') if utils.PY3 else model.get('topic').encode('utf8'))
        status = model.get('room_status')
        name = name + " [COLOR deeppink][" + age + "][/COLOR] " + status
        mid = model.get('model_id')
        img = 'https://live-screencaps.vscdns.com/{0}-desktop.jpg'.format(mid)
        videourl = 'https://ws.vs3.com/chat/get-stream-urls.php?model_id={0}&video_host={1}'.format(
            mid, model.get('video_host'))
        site.add_download_link(name, videourl, 'Playvid', img, subject, noDownload=True)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".vscdns.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".vscdns.com")
            if showdialog:
                utils.notify('Finished', 'naked.com images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    playmode = int(utils.addon.getSetting('chatplay'))
    url = "{0}&t={1}".format(url, int(time.time() * 1000))
    params = urllib_parse.parse_qs(url.split('?')[1])
    murl = '{0}webservices/chat-room-interface.php?a=login_room&model_id={1}&t={2}'.format(
        site.url, params['model_id'][0], params['t'][0])
    mdata = utils._getHtml(murl, site.url)
    if mdata:
        mdata = json.loads(mdata).get('config', {}).get('room')
        if mdata:
            if mdata.get('status') != 'O':
                utils.notify('Model not in freechat')
                return None
        else:
            utils.notify('Model Offline')
            return None
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
        return None

    vdata = utils._getHtml(url, site.url)
    if vdata:
        vdata = json.loads(vdata).get('data')
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
        return

    if playmode == 0:
        sdata = vdata.get('hls')[0]
        if sdata:
            videourl = 'https:{0}'.format(sdata.get('url'))
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    elif playmode == 1:
        sdata = vdata.get('flash')[0]
        if sdata:
            swfurl = site.url + "chat/flash/live-video-player-nw2.swf"
            videourl = "rtmp://{0} app=liveEdge/{3} swfUrl={1} pageUrl={2} playpath=mp4:{3}".format(sdata.get('stream_host'), swfurl, site.url, sdata.get('stream_name'))
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    vp = utils.VideoPlayer(name)
    vp.play_from_direct_link(videourl)

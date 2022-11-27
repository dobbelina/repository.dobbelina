'''
    Cumination
    Copyright (C) 2022 Team Cumination

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
import random
import string
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('wizzgirl', '[COLOR hotpink]Wizzgirl[/COLOR]', 'https://sexy.wizzgirl.com/', 'https://cdn.strpst.com/assets/icons/headerlogo_sexy.wizzgirl.com.png?v=321aa1c3', 'wizzgirl', True)


@site.register(default_mode=True)
def Main():
    female = True if utils.addon.getSetting("chatfemale") == "true" else False
    male = True if utils.addon.getSetting("chatmale") == "true" else False
    couple = True if utils.addon.getSetting("chatcouple") == "true" else False
    trans = True if utils.addon.getSetting("chattrans") == "true" else False
    site.add_dir('[COLOR red]Refresh WizzGirl images[/COLOR]', '', 'clean_database', '', Folder=False)

    uniq = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
    if female:
        url = '{}api/front/v2/models?limit=12&topLimit=601&favoritesLimit=12&primaryTag=girls&device=desktop&uniq={}'.format(site.url, uniq)
        site.add_dir('[COLOR hotpink]Females[/COLOR]', url, 'List', '', 1)
    if couple:
        url = '{}api/front/v2/models?limit=12&topLimit=601&favoritesLimit=12&primaryTag=couples&device=desktop&uniq={}'.format(site.url, uniq)
        site.add_dir('[COLOR hotpink]Couples[/COLOR]', url, 'List', '', 1)
    if male:
        url = '{}api/front/v2/models?limit=12&topLimit=601&favoritesLimit=12&primaryTag=men&device=desktop&uniq={}'.format(site.url, uniq)
        site.add_dir('[COLOR hotpink]Males[/COLOR]', url, 'List', '', 1)
    if trans:
        url = '{}api/front/v2/models?limit=12&topLimit=601&favoritesLimit=12&primaryTag=trans&device=desktop&uniq={}'.format(site.url, uniq)
        site.add_dir('[COLOR hotpink]Transsexual[/COLOR]', url, 'List', '', 1)
    url = '{}api/front/v2/models?limit=12&topLimit=601&favoritesLimit=12&primaryTag=girls&device=desktop&uniq={}'.format(site.url, uniq)
    List(url, 1)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".strpst.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".strpst.com")
            if showdialog:
                utils.notify('Finished', 'Images cleared')
    except:
        pass


@site.register()
def List(url, page=1):
    if not page:
        page = 1
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    listhtml = utils._getHtml(url, site.url)
    jdata = json.loads(listhtml)
    for block in jdata['blocks']:
        if block['id'] == 'topStreamsModels':
            cams = block
            break

    cam_page = cams['models'][(page - 1) * 60:page * 60]
    for model in cam_page:
        if model['status'] == 'public':
            name = model['username']
            # avatar = model['avatarUrl']
            # thumb = model['previewUrlThumbBig']
            img = 'https://img.strpst.com/thumbs/' + str(model['popularSnapshotTimestamp']) + '/' + str(model['id']) + '_webp'
            videourl = model['hlsPlaylist']
            quality = str(model['broadcastSettings']['height']) + 'p'

            if model['isNonNude']:
                name = name + ' [COLOR blue][Non Nude][/COLOR]'
            if model['isMobile']:
                name = name + ' [COLOR deeppink][via mobile][/COLOR]'
            if model['isNew']:
                name = name + ' [COLOR deeppink][NEW][/COLOR]'
            if model['country']:
                name = '{} [COLOR brown][{}][/COLOR]'.format(name, model['country'])
            site.add_download_link(name, videourl, 'Playvid', img, '', noDownload=True, quality=quality)

    site.add_dir('Next Page ({})'.format(page + 1), url, 'List', site.img_next, page=page + 1)
    utils.eod()


@site.register()
def Playvid(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vurl = re.sub(r'_\d+p.m3u8', '.m3u8', url)
    vp.play_from_direct_link(vurl)

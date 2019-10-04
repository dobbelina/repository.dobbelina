'''
    Ultimate Whitecream
    Copyright (C) 2017 Whitecream, hdgdl
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
import sys
import sqlite3
import json

import xbmc
import xbmcplugin
import xbmcgui

from resources.lib import utils


@utils.url_dispatcher.register('520')
def Main():
    utils.addDir('[COLOR red]Refresh bongacams.com images[/COLOR]','',523,'',Folder=False)
    utils.addDir('[COLOR hotpink]Female[/COLOR]','http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]=female',521,'','')
    utils.addDir('[COLOR hotpink]Male[/COLOR]','http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]=male',521,'','')
    utils.addDir('[COLOR hotpink]Transsexual[/COLOR]','http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]=transsexual',521,'','')
    utils.addDir('[COLOR hotpink]Couples[/COLOR]','http://tools.bongacams.com/promo.php?c=226355&type=api&api_type=json&categories[]=couples',521,'','')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('521', ['url'])
def List(url):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    try:
        data = utils.getHtml(url)
    except:
        
        return None
    model_list = json.loads(data)
    for camgirl in model_list:
        img = 'https:' + camgirl['profile_images']['thumbnail_image_big_live']
        username = camgirl['username']
        name = camgirl['display_name']
        utils.addDownLink(name, username, 524, img, '', noDownload=True)

    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('523')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % "bongacams.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try: os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except: pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % "bongacams.com")
            if showdialog:
                utils.notify('Finished','bongacams.com images cleared')
    except:
        pass

@utils.url_dispatcher.register('524', ['url', 'name'])
def Playvid(username, name):
    try:
       postRequest = {'method' : 'getRoomData', 'args[]' : 'false', 'args[]' : str(username)}
       response = utils.postHtml('http://bongacams.com/tools/amf.php', form_data=postRequest,headers={'X-Requested-With' : 'XMLHttpRequest'},compression=False)
    except:
        utils.notify('Oh oh','Couldn\'t find a playable webcam link')
        return None

    amf_json = json.loads(response)

    if amf_json['localData']['videoServerUrl'].startswith("//mobile"):
       videourl = 'https:' + amf_json['localData']['videoServerUrl'] + '/hls/stream_' + username + '.m3u8'  
    else:
       videourl = 'https:' + amf_json['localData']['videoServerUrl'] + '/hls/stream_' + username + '/playlist.m3u8'

    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
    listitem.setProperty("IsPlayable","true")
    if int(sys.argv[1]) == -1:
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(videourl, listitem)
        xbmc.Player().play(pl)
    else:
        listitem.setPath(str(videourl))
        xbmcplugin.setResolvedUrl(utils.addon_handle, True, listitem)

'''
    Ultimate Whitecream
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

import urllib2
import os
import sys
import random
import sqlite3
import json

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils


@utils.url_dispatcher.register('475')
def Main():
    utils.addDir('[COLOR red]Refresh Camsoda images[/COLOR]', '', 479, '', Folder=False)
    List('https://www.camsoda.com/api/v1/browse/online')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('476', ['url'])
def List(url):
	if utils.addon.getSetting("chaturbate") == "true":
		clean_database(False)
	try:
		response = utils.getHtml(url)
	except:
		return None
	data = json.loads(response)
#	print(json.dumps(data["results"], indent = 4, sort_keys=True))
        print "url: " + url
        for camgirl in data["results"]:
		try:
#	                print ( camgirl )
#			userid=camgirl['user_id']
#			userid = camgirl["tpl"]["0"]
		        gender = camgirl["tpl"]["8"].encode("ascii", errors="ignore")
#		        print "GENDER: " + gender
		        username = camgirl["tpl"]["1"].encode("ascii", errors="ignore")
#		        print "USERNAME: " + username
		        display_name = camgirl["tpl"]["2"].encode("utf-8", errors="ignore")
#	 		print "DISPLAY_NAME: " + display_name		        
			videourl = "https://www.camsoda.com/api/v1/video/vtoken/" + username
#			imag='http://md.camsoda.com/thumbs/%s.jpg'%(name)
#			imag = 'http:' + camgirl['tpl'][9]
			imag = 'https:' + camgirl["tpl"]["10"].encode("ascii", errors="ignore")
#	 		print "IMAG: " + imag	
			if 'f' in gender:
			       utils.addDownLink(username, videourl, 478, imag, '', noDownload=True)
		except:
			pass
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('479')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            lst = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".camsoda.com")
            for row in lst:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".camsoda.com")
            if showdialog:
                utils.notify('Finished', 'Camsoda images cleared')
    except:
        pass


@utils.url_dispatcher.register('478', ['url', 'name'])
def Playvid(url, name):
    url = url + "?username=guest_" + str(random.randrange(100, 55555))
    response = utils.getHtml(url)
    data = json.loads(response)
    print(json.dumps(data, indent = 4, sort_keys=True))
    if len(data["edge_servers"])==0:
        utils.notify('Model is Offline or Private')
        return None
    if "camhouse" in data['stream_name']:
        videourl = "https://camhouse.camsoda.com/" + data['app'] + "/mp4:" + data['stream_name'] + "_h264_aac_480p/playlist.m3u8?token=" + data['token']
    elif "edge" in data["edge_servers"][0]:
        videourl = "https://" + data["edge_servers"][0] + "/" +  data["stream_name"] + "_h264_aac_720p/index.m3u8?token=" + data["token"]
    else:
        videourl = "https://" + data["edge_servers"][0] + "/" + data["app"] + "/mp4:" + data["stream_name"] + "_aac/mono.m3u8?token=" + data["token"]
    print "VideoURL: " + videourl
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
    listitem.setProperty("IsPlayable", "true")
    if int(sys.argv[1]) == -1:
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(videourl, listitem)
        xbmc.Player().play(pl)
    else:
		iconimage = xbmc.getInfoImage("ListItem.Thumb")
		listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
		xbmc.Player().play(videourl, listitem)

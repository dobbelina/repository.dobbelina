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

import re
import os
import sys
import sqlite3

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

@utils.url_dispatcher.register('480')
def Main():
	utils.addDir('[COLOR red]Refresh naked.com images[/COLOR]','',483,'',Folder=False)
	#List('https://www.naked.com/live/girls/')
	List('https://www.naked.com/?tpl=index2&model=json')
	xbmcplugin.endOfDirectory(utils.addon_handle)

def cleanname(s):
        if not s:
            return ''
        badchars = '\\*?\"<>|\''
        for c in badchars:
            s = s.replace(c, '')
        return s


@utils.url_dispatcher.register('481', ['url'])
def List(url):
	if utils.addon.getSetting("chaturbate") == "true":
		clean_database(False)
	try:
		data = utils.getHtml(url, '')
	except:		
		return None

	models = re.compile('"video_host":.*?"(.+?)".*?"model_id":.*?"(.+?)".+?"image".*?"(.+?)".+?"model_name".*?"(.+?)","model_seo_name".*?"(.+?)".+?"sample_long_id".*?"(.+?)"', re.DOTALL | re.IGNORECASE).findall(data)

	for videohost, model_id, img, model, seo_name, long_id in models:
		img = 'https:'+img if img.startswith('//') else img
                img = cleanname(img)
                name = cleanname(model)
		videourl = "http://www.naked.com/?model=" + cleanname(seo_name)
#	        videourl = 'https://manifest.vscdns.com/chunklist.m3u8?model_id=' + cleanname(model_id) + '&host=' + cleanname(videohost) + '&provider=level3&secure=true'
                print "VIDEOURL: " + videourl
		utils.addDownLink(name, videourl, 482, img, '', noDownload=True)
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('483')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".nk-img.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try: os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except: pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".nk-img.com")
            if showdialog:
                utils.notify('Finished','naked.com images cleared')
    except:
        pass


@utils.url_dispatcher.register('482', ['url', 'name'])
def Playvid(url, name):
	listhtml = utils.getHtml(url, '')
	namex=name.replace(' ','-').lower()      
	try:
                seo_nameurl=url.split('=')[1]
	        model_list = re.compile('live clearfix model-wrapper.*?data-model-id=(.*?)data-model-name=(.*?)data-model-seo-name=(.*?)data.*?data-video-host=(.*?)data.*?data-live-image-src=(.*?)data.*?End Live', re.DOTALL | re.IGNORECASE).findall(listhtml)
                print (model_list)
	        for model_id, model, seo_name, videohost, img in model_list:
			if seo_nameurl in seo_name:
	        		videourl = 'https://manifest.vscdns.com/chunklist.m3u8?model_id=' + cleanname(model_id) + '&host=' + cleanname(videohost) + '&provider=highwinds&secure=true'

		iconimage = xbmc.getInfoImage("ListItem.Thumb")
		listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
		listitem.setProperty("IsPlayable","true")
		if int(sys.argv[1]) == -1:
			pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			pl.clear()
			pl.add(videourl, listitem)
                        listitem.setProperty('inputstreamaddon','inputstream.adaptive')
                        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
			xbmc.Player().play(pl)
		else:
			iconimage = xbmc.getInfoImage("ListItem.Thumb")
			listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
			listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
			xbmc.Player().play(match, listitem)	
	except:
		utils.notify('Oh oh','Couldn\'t find a playable webcam link')

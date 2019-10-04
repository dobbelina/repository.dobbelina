'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream

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
import urllib

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils


mobileagent = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'}


@utils.url_dispatcher.register('280')
def Main():
    utils.addDir('[COLOR red]Refresh Cam4 images[/COLOR]','',283,'',Folder=False)
    utils.addDir('[COLOR hotpink]Featured[/COLOR]','http://www.cam4.com/featured/1',281,'',1)
    utils.addDir('[COLOR hotpink]Females[/COLOR]','http://www.cam4.com/female/1',281,'',1)
    utils.addDir('[COLOR hotpink]Couples[/COLOR]','http://www.cam4.com/couple/1',281,'',1)
    utils.addDir('[COLOR hotpink]Males[/COLOR]','http://www.cam4.com/male/1',281,'',1)
    utils.addDir('[COLOR hotpink]Transsexual[/COLOR]','http://www.cam4.com/shemale/1',281,'',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('283')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".cam4s.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try: os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except: pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".cam4s.com")
            if showdialog:
                utils.notify('Finished','Cam4 images cleared')
    except:
        pass


@utils.url_dispatcher.register('281', ['url'], ['page'])
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    try:
        listhtml = utils.getHtml(url, url)
    except:
        return None
    match = re.compile('data-hls-preview-url="([^"]+)".*? src="([^"]+)".*?title="Chat Now Free with ([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videourl, img, name in match:
        name = utils.cleantext(name)
#        videourl = "http://www.cam4.com" + videourl
        utils.addDownLink(name, videourl, 282, img, '', noDownload=True)
    if re.search('<link rel="next"', listhtml, re.DOTALL | re.IGNORECASE):
            npage = page + 1        
            url = url.replace('/'+str(page),'/'+str(npage))
            utils.addDir('Next Page ('+str(npage)+')', url, 281, '', npage)        
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('282', ['url', 'name'])
def Playvid(url, name):
#    listhtml = utils.getHtml(url, '', mobileagent)
#    match = re.compile('src="(http[^"]+m3u8)', re.DOTALL | re.IGNORECASE).findall(listhtml)
#    if match:
#       videourl = match[0] + "|User-Agent=" + urllib.quote_plus(mobileagent['User-Agent'])
    videourl = url + "|User-Agent=" + urllib.quote_plus(mobileagent['User-Agent'])
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

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
from resources.lib import favorites
from resources.lib import websocket

@utils.url_dispatcher.register('515')
def Main():
    utils.addDir('[COLOR red]Refresh streamate.com images[/COLOR]','',517,'',Folder=False)
    utils.addDir('[COLOR hotpink]Search + Fav add[/COLOR]','https://www.streamate.com/cam/',519,'','')
    List('http://api.naiadsystems.com/search/v1/list?results_per_page=100')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('516', ['url'], ['page'])
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    try:
        data = utils.getHtml(url + "&page_number=" + str(page))
    except:
        
        return None
    model_list = json.loads(data)
    for camgirl in model_list['Results']:
        img = "http://m1.nsimg.net/media/snap/" + str(camgirl['PerformerId']) + ".jpg"
        performerID = str(camgirl['PerformerId'])
        name = camgirl['Nickname']
        utils.addDownLink(name, performerID, 518, img, '', noDownload=True)
    npage = page + 1
    utils.addDir('Next Page (' + str(npage) + ')', url, 516, '', npage)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('517')
def clean_database(showdialog=True):
    conn = sqlite3.connect(xbmc.translatePath("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % "m1.nsimg.net")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try: os.remove(xbmc.translatePath("special://thumbnails/" + row[1]))
                except: pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % "m1.nsimg.net")
            if showdialog:
                utils.notify('Finished','streamate.com images cleared')
    except:
        pass

@utils.url_dispatcher.register('518', ['url', 'name'])
def Playvid(performerID, name):
    response = utils.getHtml("https://streamate.com/ajax/config/?name=" + name + "&sakey=&sk=streamate.com&userid=0&version=2.2.0&ajax=1")
    data = json.loads(response)
    
    host = data['liveservices']['host'] + "/socket.io/?puserid=" + performerID + "&EIO=3&transport=websocket" #24824942
    ws = websocket.WebSocket()
    ws = websocket.create_connection(host)
    
    ws.send('40/live')
    
    quitting = 0
    i = 0
    while quitting == 0:
        i += 1
        message =  ws.recv()
        match = re.compile('performer offline', re.DOTALL | re.IGNORECASE).findall(message)
        if match:
            quitting=1
            ws.close()
            utils.notify('Model is offline')
            return None

        match = re.compile('isPaid":true', re.DOTALL | re.IGNORECASE).findall(message)
        if match:
            quitting=1
            ws.close()
            utils.notify('Model not in freechat')
            return None
            
        if message == '40/live':
            ws.close()
            quitting=1
            link = 'https://sea1b-ls.naiadsystems.com/sea1b-edge-ls/80/live/s:' + data['performer']['nickname'] + '.json'
            ref = 'https://www.streamate.com/cam/' + data['performer']['nickname']
            j = utils.getHtml(link, ref)
            match = re.compile('location":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(j)
            videourl = match[0]
        
        # match = re.compile('roomInfoUpdate', re.DOTALL | re.IGNORECASE).findall(message)
        # if match:
            # ws.send('42/live,["GetVideoPath",{"nginx":1,"protocol":2,"attempt":1}]')
            # while quitting == 0:
                # message = ws.recv()
                # match = re.compile('(http[^"]+m3u8)', re.DOTALL | re.IGNORECASE).findall(message)
                # if match:
                    # videourl = match[0]
                    # quitting=1
                    # ws.close()

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
        #iconimage = xbmc.getInfoImage("ListItem.Thumb")
        #listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        #listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        xbmc.Player().play(videourl, listitem)

@utils.url_dispatcher.register('519', ['url'])
def Search(url):
    keyword = utils._get_keyboard(heading="Searching for...")
    if (not keyword): return False, 0
    try:
        response = utils.getHtml(url + keyword)
    except:
        utils.notify('Model not found - try again')
        return None
    match = re.compile("'page',\s*'\/signup\/\?smid=([^']+)&", re.DOTALL | re.IGNORECASE).findall(response)
    if match:
        utils.notify('Found ' + keyword + ' adding to favorites now')
        img = "http://m1.nsimg.net/media/snap/" + match[0] + ".jpg"
        performerID = match[0]
        name = keyword
        favorites.Favorites('add', 518, name, performerID, img)

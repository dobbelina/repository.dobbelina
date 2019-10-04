'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream

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

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

    
@utils.url_dispatcher.register('40')
def NFMain():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.nudeflix.com/browse',44,'','')
    utils.addDir('[COLOR hotpink]HD[/COLOR]','http://www.nudeflix.com/browse/cover?order=hd&page=1',41,'',1)
    NFList('http://www.nudeflix.com/browse/cover?order=released&page=1',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('44', ['url'])
def NFCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<li>\s+<a href="/browse/category/([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        catpage = catpage.replace(' ','%20')
        catpage = 'http://www.nudeflix.com/browse/category/' + catpage + '/cover?order=released&page=1'
        utils.addDir(name, catpage, 41, '', 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('41', ['url'], ['page'])
def NFList(url,page=1):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('href="([^"]+)" class="link">[^"]+?"([^"]+)" alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        videopage = 'http://www.nudeflix.com' + videopage
        utils.addDir(name, videopage, 42, img, '')
    if re.search("<strong>next &raquo;</strong>", listhtml, re.DOTALL | re.IGNORECASE):
        npage = page + 1        
        url = url.replace('page='+str(page),'page='+str(npage))
        utils.addDir('Next Page ('+str(npage)+')', url, 41, '', npage)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('42', ['url'])
def NFScenes(url):
    scenehtml = utils.getHtml(url, '')
    match = re.compile('class="scene">.*?<img class="poster" src="([^"]+)".*?data-src="([^"]+)".*?<div class="description">[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(scenehtml)
    scenecount = 1
    for img, sceneurl, desc in match:
        name = 'Scene ' + str(scenecount)
        sceneurl = sceneurl.replace("&amp;","&")
        scenecount = scenecount + 1
        utils.addDownLink(name, sceneurl, 43, img, desc)        
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('43', ['url', 'name'], ['download'])
def NFPlayvid(url, name, download=None):
    videourl = url
    if download == 1:
        utils.downloadVideo(videourl, name)
    else:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
        listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        xbmc.Player().play(videourl, listitem)

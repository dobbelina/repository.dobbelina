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
dialog = utils.dialog

@utils.url_dispatcher.register('250')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://en.paradisehill.cc/porn/',253,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://en.paradisehill.cc/search/?pattern=',254,'','')
    List('https://en.paradisehill.cc/all/?page=1',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('251', ['url'], ['page'])
def List(url, page=1):  
    if page == 1:
        url = url.replace('page=1','page='+str(page))
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None 
    match = re.compile(r'Movie">.+?<a href="([^"]+)".+?<span itemprop="name">(.+?)</span.?</div>.+?</span>.+?src="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        img = "https://en.paradisehill.cc" + img
        videopage = "https://en.paradisehill.cc" + videopage
        utils.addDownLink(name, videopage, 252, img, '')
    if re.search('<li class="last">', listhtml, re.DOTALL | re.IGNORECASE):
        npage = page + 1        
        url = url.replace('page='+str(page),'page='+str(npage))
        utils.addDir('Next Page ('+str(npage)+')', url, 251, '', npage)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('253', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("Categories</h2>(.*?)<noindex>", re.DOTALL | re.IGNORECASE).findall(cathtml)
    
    
    match1 = re.compile('href="([^"]+)".+?<span.+?<span>(.+?)<.+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(match[0])
    
    
    
    #match1 = re.compile('link" href="([^"]+)".*?bci-title">([^<]+)<.*?src="([^"]+)".*?cat-title">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
    for caturl, name, img in match1:
        #name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        img = "http://en.paradisehill.cc" + img
        catpage = "http://en.paradisehill.cc" + caturl + "&page=1"
        utils.addDir(name, catpage, 251, img, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('254', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 254)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title + '&page=1'
        List(searchUrl, 1)


@utils.url_dispatcher.register('252', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    if utils.addon.getSetting("paradisehill") == "true": playall = True
    else: playall = ''
    videopage = utils.getHtml(url, '')
    
    match0 = re.compile('<div class="fp-playlist">(.+?)</div>', re.DOTALL | re.IGNORECASE).findall(videopage)[0]    
    match = re.compile('<a href="(.+?)">', re.DOTALL | re.IGNORECASE).findall(match0)
    videos = match
    
    if playall == '':
        if len(videos) > 1:
            i = 1
            videolist = []
            for x in videos:
                videolist.append('Part ' + str(i))
                i += 1
            videopart = dialog.select('Multiple videos found', videolist)
            if videopart == -1:
                return
            videourl = videos[videopart]
        else: videourl = videos[0]
        videourl = videourl.replace('\/','/')
        videourl = videourl + "|referer="+ url
    
    if download == 1 and playall == '':
        utils.downloadVideo(videourl, name)
    else:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
    
        if playall:
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            i = 1
            for videourl in videos:
                newname = name + ' Part ' + str(i)
                listitem = xbmcgui.ListItem(newname, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
                listitem.setInfo('video', {'Title': newname, 'Genre': 'Porn'})
                listitem.setProperty("IsPlayable","true")
                videourl = videourl + "|referer="+ url
                pl.add(videourl, listitem)
                i += 1
                listitem = ''
            xbmc.Player().play(pl)
        else:
            xbmc.Player().play(str(videourl))
            #listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
            #listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})        
            #xbmc.Player().play(videourl, listitem)
            
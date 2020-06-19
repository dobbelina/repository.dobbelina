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

@utils.url_dispatcher.register('490')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://www.amateurcool.com/most-recent/',493,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.amateurcool.com/search/videos/',494,'','')
    List('https://www.amateurcool.com/most-recent/')


@utils.url_dispatcher.register('491', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile(r'data-video="(.+?)">.+?<img src="(.+?)" alt="(.+?)".+?<span>(.+?) Video</span>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, duration in match:
        name = utils.cleantext(name + ' [COLOR deeppink]' +  duration + '[/COLOR]' )
        utils.addDownLink(name, videopage, 492, img, '')
    try:
        next_page = re.compile("<a href='([^']+)' class=\"next\">NEXT").findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + str(page_nr) + ')', url[:url.rfind('/')+1] + next_page, 491, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('492', ['url', 'name'], ['download'])
def Playvid(videourl, name, download=None):

	
	if download == 1:
		utils.downloadVideo(videourl, name)
	else:    
	#	xbmc.Player().play(str(videourl))
		iconimage = xbmc.getInfoImage("ListItem.Thumb")
		listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
		xbmc.Player().play(videourl, listitem)		


@utils.url_dispatcher.register('493', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    category_list = re.compile('<ul class="right-categories">(.*?)</ul>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile("<a href='([^']+)'>([^<]+)</a>", re.DOTALL | re.IGNORECASE).findall(category_list)
    for catpage, name in match:
        utils.addDir(name, catpage, 491, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('494', ['url'], ['keyword'])  
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 494)
    else:
        title = keyword.replace(' ','-')
        searchUrl = searchUrl + title + '/page1.html'
        List(searchUrl)

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

@utils.url_dispatcher.register('500')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://pornone.com/categories/',503,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://pornone.com/search?q=',504,'','')
    List('https://pornone.com/newest/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('501', ['url'])
def List(url):
	xbmc.log("List: " + url)
	try:
		listhtml = utils.getHtml(url, '')
	except:
		return None

	match = re.compile('class="video">.*?href="([^"]+)".*?class="time">([^<]+)</span>.*?span class="hd([^<]+)</span>.*?<img src="([^"]+)" alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
	for videopage, duration, hd, img, name in match:
		name = utils.cleantext(name)
		if hd.find('HD Video') > 0:
			hd = " [COLOR orange]HD[/COLOR] "
		else:
			hd = " "
		name = name + hd + "[COLOR deeppink]" + duration + "[/COLOR]"
		utils.addDownLink(name, videopage, 502, img, '')
	try:
		nextp = re.compile('<link rel="next" href="(.+?)">').findall(listhtml)
		utils.addDir('Next Page', nextp[0], 501, '')
	except:
		pass
	xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('502', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
	html = utils.getHtml(url, '')
	videourl = re.compile('video id="pornone-video-player".*?<source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)[0]
	if download == 1:
		utils.downloadVideo(videourl, name)
	else:    
	#	xbmc.Player().play(str(videourl))
		iconimage = xbmc.getInfoImage("ListItem.Thumb")
		listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
		xbmc.Player().play(videourl, listitem)		

@utils.url_dispatcher.register('503', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url)
    cat_block = cathtml.split('>All Categories<')[2]
    match = re.compile('a href="([^"]+)".+?img src="([^"]+)".+?"title">([^<]+)<.+?"videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cat_block)
    for cat, img, name, videos in match:
        catpage = "https://pornone.com"+ cat
        name = utils.cleantext(name) + "[COLOR deeppink] " + videos + "[/COLOR]"
        utils.addDir(name, catpage, 501, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)
    
@utils.url_dispatcher.register('504', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    xbmc.log("Search: " + searchUrl)
    if not keyword:
        utils.searchDir(url, 504)
    else:
        title = keyword.replace(' ','_')
        searchUrl = searchUrl + title
        xbmc.log("Search: " + searchUrl)
        List(searchUrl)

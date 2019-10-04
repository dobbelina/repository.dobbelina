'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 Fr33m1nd

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

import xbmcplugin
from resources.lib import utils

progress = utils.progress


@utils.url_dispatcher.register('170')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://streamxxx.tv/', 177, '', '')
    utils.addDir('[COLOR hotpink]Tags[/COLOR]','http://streamxxx.tv/top-tags/', 173, '', '')
    utils.addDir('[COLOR hotpink]Movies[/COLOR]','http://streamxxx.tv/category/movies-xxx/', 175, '', '')
    utils.addDir('[COLOR hotpink]International Movies[/COLOR]','http://streamxxx.tv/category/movies-xxx/international-movies/', 176, '', '')
    utils.addDir('[COLOR hotpink]Search Overall[/COLOR]','http://streamxxx.tv/?s=', 174, '', '')
    utils.addDir('[COLOR hotpink]Search Scenes[/COLOR]','http://streamxxx.tv/?cat=5562&s=', 174, '', '')
    List('http://streamxxx.tv/category/clips/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('175')
def MainMovies():

    List('http://streamxxx.tv/category/movies-xxx/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('176')
def MainInternationalMovies():
    List('http://streamxxx.tv/category/movies/international-movies/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('171', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, url)
    except:
        
        return None
    match = re.compile('<h2 class="st-loop-entry-title">.*?<a href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        if videopage.startswith('/'):
            videopage = 'http://streamxxx.tv/' + videopage
        utils.addDownLink(name, videopage, 172, img, '')
    try:
        nextp=re.compile('<a class="next page-numbers" href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Next Page', nextp, 171,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('174', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 174)
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('177', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("Clips</a>(.*)</ul>", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match1 = re.compile('href="(/[^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
    for catpage, name in match1:
        catpage = 'http://streamxxx.tv' + catpage
        utils.addDir(name, catpage, 171, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('173', ['url'])
def Tags(url):
	html = utils.getHtml(url, '')
	match1 = re.compile('<a id="tag-link.+?href="([^"]+)".+?"tag">(.+?)</a>', re.DOTALL | re.IGNORECASE).findall(html)
	for catpage, name in match1:
		utils.addDir(name, catpage, 171, '')
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('172', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)

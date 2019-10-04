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

import urllib
import re
import base64

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

progress = utils.progress


@utils.url_dispatcher.register('70')
def PHMain():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.pornhive.tv/en/categories',73,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.pornhive.tv/en/search?keyword=',74,'','')
    PHList('http://www.pornhive.tv/en/page/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('71', ['url'])
def PHList(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile(r'anel-img">\s+<a href="([^"]+)">\s+<img.*?data-src="([^"]+)".*?alt="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 72, img, '')
    try:
        nextp=re.compile('<a href="([^"]+)"[^>]+>Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', nextp[0],71,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('74', ['url'], ['keyword'])    
def PHSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 74)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        PHList(searchUrl)


@utils.url_dispatcher.register('73', ['url'])
def PHCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'panel-img">\s+<A href="([^"]+)".*?alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        utils.addDir(name, catpage, 71, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('72', ['url', 'name'], ['download'])
def PHVideo(url, name, download=None):
    progress.create('Play video', 'Searching videofile.')
    progress.update( 10, "", "Loading video page", "" )
    videopage = utils.getHtml(url, '')
    if 'extra_urls' in videopage:
        baseurls = re.compile("'(aHr[^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)
        for base in baseurls:
            videopage = 'src="' + base64.b64decode(base) + '"' + " " + videopage
    utils.playvideo(videopage, name, download, url=url)




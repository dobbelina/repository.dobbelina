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

import xbmcplugin
from resources.lib import utils

progress = utils.progress


@utils.url_dispatcher.register('200')
def XTCMain():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://xtasie.com/video-porn-categories/',203,'','')
    utils.addDir('[COLOR hotpink]Top Rated[/COLOR]','http://xtasie.com/top-rated-porn-videos/',201,'','')
    utils.addDir('[COLOR hotpink]Most Viewed[/COLOR]','http://xtasie.com/most-viewed-porn-videos/',201,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://xtasie.com/?s=',204,'','')
    XTCList('http://xtasie.com/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('201', ['url'])
def XTCList(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<a href="([^"]+)"(?:>| title=".*?">)<img.*?data-original="([^"]+)" alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 202, img, '')
    try:
        nextp=re.compile('<(?:link rel="next"|a class="next page-numbers") href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        next = nextp[0]
        utils.addDir('Next Page', next, 201,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('204', ['url'], ['keyword'])    
def XTCSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 204)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        XTCList(searchUrl)


@utils.url_dispatcher.register('203', ['url'])
def XTCCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<p><a href="([^"]+)".*?<img src="([^"]+)".*?<h2>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name in match:
        utils.addDir(name, catpage, 201, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('202', ['url', 'name'], ['download'])
def XTCPlayvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)

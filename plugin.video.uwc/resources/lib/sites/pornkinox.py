'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 anton40

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


@utils.url_dispatcher.register('470')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://pornkinox.to/?s=', 473, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://pornkinox.to/', 474, '', '')
    List('http://pornkinox.to/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('471', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('<article[^>]+>.+?<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 472, img, '')
    try:
        nextp=re.compile('<a class="next page-numbers" href="(.+?)"><i class="fa fa-angle-right"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        nextp = nextp[0].replace("&#038;", "&")
        utils.addDir('Next Page', nextp, 471,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('473', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 473)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('474', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<li class="cat-item.+?"><a href="(.+?)" title=".+?">(.+?)</a> \((.+?)\)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = name + ' [COLOR deeppink](%s)[/COLOR]' % videos
        utils.addDir(name, catpage, 471, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('472', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)
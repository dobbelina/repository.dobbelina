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


@utils.url_dispatcher.register('330')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://pornkino.to/?s=', 333, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://pornkino.to/', 334, '', '')
    List('http://pornkino.to/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('331', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('<article id=.*?class="cover" src="([^"]+)".*?alt="([^"]+)".*?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, videopage in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 332, img, '')
    try:
        nextp=re.compile('<a class="next page-numbers" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        nextp = nextp[0].replace("&#038;", "&")
        utils.addDir('Next Page', nextp, 331,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('333', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 333)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('334', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("Kategorien</span>.*?<ul>(.*?)</ul>", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match1 = re.compile(r'href="([^"]+)"[^>]+>([^<]+)</a> \((\d+)', re.DOTALL | re.IGNORECASE).findall(match[0])
    for catpage, name, videos in match1:
        name = name + ' [COLOR deeppink](%s)[/COLOR]' % videos
        utils.addDir(name, catpage, 331, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('332', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)
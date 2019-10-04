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


@utils.url_dispatcher.register('240')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://justporn.to/?s=', 244, '', '')
    utils.addDir('[COLOR hotpink]Movies[/COLOR]','http://justporn.to/category/dvdrips-full-movies/', 245, '', '')
    List('http://justporn.to/category/scenes/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('245')
def MainMovies():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://justporn.to/?s=', 244, '', '')
    utils.addDir('[COLOR hotpink]Scenes[/COLOR]','http://justporn.to/category/scenes/', 240, '', '')
    List('http://justporn.to/category/dvdrips-full-movies/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('241', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('<a href="(.+?)" title="(.+?)">\n.+?<img src="(.+?)".+?style="position').findall(listhtml)
    for videopage, name, img in match:
        print "Processing: " + name
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 242, img, '')
    try:
        print "Adding next"
        nextp=re.compile("<span class='current'>[0-9]+</span><a href='(.+?)'", re.DOTALL | re.IGNORECASE).findall(listhtml)
        nextp = nextp[0]
        utils.addDir('Next Page', nextp, 241,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('244', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 244)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('242', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)

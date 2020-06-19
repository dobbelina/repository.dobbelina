'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream

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

siteurl = 'http://www.perfectgirls.net/'
    
@utils.url_dispatcher.register('710')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.perfectgirls.net/',713,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.perfectgirls.net/search/',714,'','')
    List(siteurl)
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('711', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="list__item_link">.+?href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?<time>(.*?)</time>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    
    for videopage, name, img, duration in match:
	videopage = siteurl + videopage
        name = utils.cleantext(name)
        name = "[COLOR deeppink]" + duration + "[/COLOR] " + name
        img = 'http:' + img
        utils.addDownLink(name, videopage, 712, img, '')
    try:
        nextp = re.compile('class="pagination__item pagination__next".+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', siteurl + nextp[0], 711,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('712', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download,'','<source src="([^"]+)" [^>]+default')
    vp.play_from_site_link(url, url)


@utils.url_dispatcher.register('713', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('class="header-submenu__item_link" href="([^"]+)">([^<]+)</a></li>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name.strip())
        utils.addDir(name, siteurl + catpage, 711, '', 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('714', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 714)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


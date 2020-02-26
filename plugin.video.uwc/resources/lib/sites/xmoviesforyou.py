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

siteurl = 'https://xmoviesforyou.com/'
    
@utils.url_dispatcher.register('750')
def Main():
    utils.addDir('[COLOR hotpink]Category[/COLOR]',siteurl,755,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/?s=',754,'','')
    List(siteurl)
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('751', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="grid-box-img"><a href="([^"]+)" rel="bookmark" title="([^"]+)">.+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 752, img, '')
    try:
        (nextp, page) = re.compile('<link rel="next" href="([^"]+/(\d*))"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Next Page (' + str(page) + ')', nextp, 751,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('752', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)


@utils.url_dispatcher.register('754', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 754)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

@utils.url_dispatcher.register('755', ['url'])
def Cat(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('a href="([^"]+)" rel="tag">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    catlist = []
    for catpage, name in sorted(match, key=lambda x: x[1]):
	if name not in catlist:
	    catlist.append(name)
            utils.addDir(name, catpage, 751, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

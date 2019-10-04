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

siteurl = 'https://porndoe.com'
    
@utils.url_dispatcher.register('720')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl+'/categories/',723,'','')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]',siteurl+'/channels?sort=ranking&page=1',725,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/search?keywords=',724,'','')
    List(siteurl+'/videos')
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('721', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('img data-src="([^"]+)".+?alt="([^"]+)".+?<span class="txt">([^<]+)</span>.+?<span class="ico (.+?)"></span>.+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, duration, ico, videopage in match:
	videopage = siteurl + videopage
        name = utils.cleantext(name)
        if ico == 'ico-hd':
            ico = " [COLOR orange]HD[/COLOR] "
	else:
            if ico == 'ico-vr' > 0:
                ico = " [COLOR green]VR[/COLOR] "
	    else:
	        ico = " "
        name = name + ico + "[COLOR deeppink]" + utils.cleantext(duration) + "[/COLOR]"
        utils.addDownLink(name, videopage, 722, img, '')
    try:
        nextp = re.compile('<li class="page next"><a href="([^"]+)"><span>', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', siteurl + nextp[0], 721,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('722', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download,'','src="([^"]+.mp4)')
    vp.play_from_site_link(url, url)


@utils.url_dispatcher.register('723', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('data-src="([^"]+)".+?href="([^"]+)">.+?class="txt">([^<]+)<.+?class="count">(\(\d+\))</span>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for img, catpage, name, count in match:
        name = utils.cleantext(name.strip()) + " [COLOR deeppink]" + utils.cleantext(count) + "[/COLOR]"
	catpage = siteurl + catpage
        utils.addDir(name, catpage, 721, img, 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('725', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match1 = re.compile('<h2 class="title"(.+?)Pagination: end -->', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<div class="item">[^<]+?<a href="([^"]+)".+?data-src="([^"]+)".+?"title">([^<]+)<.+?class="number">([^<]+)</span>', re.DOTALL | re.IGNORECASE).findall(match1)
    for catpage, img, name, rank in match:
        name = "[COLOR deeppink]" + rank + "[/COLOR] " + utils.cleantext(name.strip())
	catpage = siteurl + catpage
        utils.addDir(name, catpage, 721, img, 2)    
    try:
        nextp = re.compile('<li class="page next"><a href="[^"]+(page=\d+)"><span>', re.DOTALL | re.IGNORECASE).findall(match1)
        utils.addDir('Next Page', siteurl + '/channels?sort=ranking&' + nextp[0], 725,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('724', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 724)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


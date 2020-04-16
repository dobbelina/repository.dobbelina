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

siteurl = 'http://freepornstreams.org'
    
@utils.url_dispatcher.register('740')
def Main():
#    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl,743,'','')
    utils.addDir('[COLOR hotpink]Clips[/COLOR]',siteurl+'/free-stream-porn/',746,'','')
    utils.addDir('[COLOR hotpink]Movies[/COLOR]',siteurl+'/free-full-porn-movies/',747,'','')
    utils.addDir('[COLOR hotpink]HD[/COLOR]',siteurl+'/tag/high-def-porn-video/',748,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/?s=',744,'','')
    List(siteurl)
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('741', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<a href="([^"]+)" rel="bookmark">([^<]+)</a>.+?<img src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        if 'Siterip' in name or 'Ubiqfile' in name:
            continue
        utils.addDownLink(name, videopage, 742, img, '')
    try:
        nextp = re.compile('<div class="nav-previous"><a href="([^"]+)" ><span class="meta-nav">', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', nextp[0], 741,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('746', ['url'])
def ListClips(url):
    List(url)

@utils.url_dispatcher.register('747', ['url'])
def ListMovies(url):
    List(url)

@utils.url_dispatcher.register('748', ['url'])
def ListHD(url):
    List(url)


@utils.url_dispatcher.register('742', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download,'a href="([^"]+)" rel="nofollow')
    vp.play_from_site_link(url, url)


@utils.url_dispatcher.register('743', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="([^"]+)" rel="tag">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name) 
        utils.addDir(name, catpage, 741, '', 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('744', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 744)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


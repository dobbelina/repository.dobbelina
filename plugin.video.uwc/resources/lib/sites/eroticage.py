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


@utils.url_dispatcher.register('430')
def Main():
    utils.addDir('[COLOR hotpink]Tags[/COLOR]','http://www.eroticage.net/',433,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.eroticage.net/?s=',434,'','')
    List('http://www.eroticage.net/page/1/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('431', ['url'])
def List(url):
    try:
        html = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('id="wrapper"(.*?)sayfala', re.DOTALL | re.IGNORECASE).findall(html)[0]
    match1 = re.compile('<div class="titleFilm"><a href="([^"]+)">([^<]+)<.*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(match)
    for videopage, name, img in match1:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 432, img, '')
    try:
        nextp = re.compile('rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
        utils.addDir('Next Page', nextp[0], 431,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('432', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    videolink = re.compile('<iframe src="([^"]+)" ', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    videolink = videolink.replace('woof.tube','verystream.com')
    vp.play_from_link_to_resolve(videolink)


@utils.url_dispatcher.register('433', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="([^"]+)" class="tag[^>]+>([^<]+)<').findall(cathtml)
    for catpage, name in match:
        utils.addDir(name, catpage, 431, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('434', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 434)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


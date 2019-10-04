'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream
    Copyright (C) 2016 anton40
 
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

 
@utils.url_dispatcher.register('420') 
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://xxxstreams.org/',423,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://xxxstreams.org/?s=',424,'','')
    List('http://xxxstreams.org/page/1')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('421', ['url']) 
def List(url):
    try:
        html = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('<div class="entry-content">.*?<img src="([^"]+)".*?<a href="([^"]+)" class="more-link">.+?<span class="screen-reader-text">([^"]+)</span>', re.DOTALL | re.IGNORECASE).findall(html)
    for img, videopage, name in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 422, img, '')
    try:
        nextp = re.compile('<a class="next.*?href="(.+?)">', re.DOTALL | re.IGNORECASE).findall(html)
        utils.addDir('Next Page', nextp[0], 421,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('425', ['url'])
def ListSearch(url):
    html = utils.getHtml(url, '').replace('\n','')
    match = re.compile('bookmark">([^<]+)</a></h1>.*?<img src="([^"]+)".*?href="([^"]+)"').findall(html)
    for name, img, videopage in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 422, img, '')
    try:
        nextp = re.compile('<link rel="next" href="(.+?)" />', re.DOTALL | re.IGNORECASE).findall(html)
        utils.addDir('Next Page', nextp[0], 425,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('422', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    video_page = utils.getHtml(url, '')
    entry_content = re.compile('entry-content">(.*?)</div>', re.DOTALL | re.IGNORECASE).search(video_page).group(1)
    vp.play_from_html(entry_content)


@utils.url_dispatcher.register('423', ['url']) 
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<li.+?class=".+?menu-item-object-post_tag.+?"><a href="(.+?)">(.+?)</a></li>').findall(cathtml)
    for catpage, name in match:
        utils.addDir(name, catpage, 421, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('424', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 424)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        ListSearch(searchUrl)
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

@utils.url_dispatcher.register('370') 
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.freeomovie.com/', 373, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.freeomovie.com/?s=', 374, '', '')    
    List('http://www.freeomovie.com/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('371', ['url']) 
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('<h2><a href="([^"]+)".*?title="([^"]+)">.+?<img src="([^"]+)".+? width="', re.DOTALL).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        img = img.replace('/i/','/t/')
        utils.addDownLink(name, videopage, 372, img, '')
    try:
        nextp = re.compile('a class="nextpostslink" rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', nextp)[-1]
        utils.addDir('Next Page (' + page_nr + ')', nextp, 371,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('374', ['url'], ['keyword'])     
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 374)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)

@utils.url_dispatcher.register('373', ['url']) 
def Cat(url):
    listhtml = utils.getHtml(url, '')
    match0 = re.compile('<h2>Categories(.+?)<div id="enhancedtextwidget-11"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]	
    match = re.compile('<a href="(.+?)"\s+title=".+?">(.+?)<', re.DOTALL | re.IGNORECASE).findall(match0)
    for catpage, name in match:
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 371, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('372', ['url', 'name'], ['download'])   
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, '<a href="([^"]+)" target','')
    vp.play_from_site_link(url, url)

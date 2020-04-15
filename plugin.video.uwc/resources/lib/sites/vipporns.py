'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream

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


@utils.url_dispatcher.register('190')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://www.vipporns.com/categories/',193,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.vipporns.com/search/',194,'','')
    List('https://www.vipporns.com/latest-updates/')

@utils.url_dispatcher.register('191', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        
        return None
    match = re.compile('class="item.+?href="([^"]+)" title="([^"]+)".+?data-original="([^"]+)".+?class="duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, videopage, 192, img, '')
    try:
        nextp=re.compile('<li class="next"><a href="([^"]+)"').findall(listhtml)[0]
        next_page_nr = re.compile('from:(\d+)">Next<').findall(listhtml)[0]
        page = re.findall('/\d+/$', url)
        if not page:
            page = '/1/'
            url = url + '1/'
        else:
            page = page[0]
        next_page = url.replace(page, '/' + next_page_nr + '/')
        utils.addDir('Next Page (' + next_page_nr + ')', next_page, 111,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('194', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 194)
    else:
        title = keyword.replace(' ','-')
        searchUrl = searchUrl + title + '/'
        List(searchUrl)


@utils.url_dispatcher.register('193', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)">.+?src="([^"]+)".+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"    
        utils.addDir(name, catpage, 191, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('192', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download,'', "video_url: '([^']+)'")
    videohtml = utils.getHtml(url)
    vp.play_from_html(videohtml)

'''
    Ultimate Whitecream
    Copyright (C) 2018 Whitecream, Fr33m1nd, holisticdioxide

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

import urllib
import re
import os.path
import base64

import xbmcplugin
from resources.lib import utils


sites = ['https://reallifecam.to', 'https://voyeur-house.to']

@utils.url_dispatcher.register('230', ['url'], ['page'])
def REAL(url, page=0):
    siteurl = sites[page]
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl + '/categories', 233, '', page)
    utils.addDir('[COLOR hotpink]Search[/COLOR]', siteurl + '/search/videos?search_query=', 234, '', page)
    List(siteurl + '/videos?o=mr', page)


@utils.url_dispatcher.register('231', ['url'], ['page'])
def List(url, page=0):
    siteurl = sites[page]
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="well well-sm">\s*<a href="([^"]+)".+?img src="([^"]+)" title="([^"]+)" .+?class="duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, duration in match:
#        hd = '[COLOR orange]HD[/COLOR]' if 'hd sprite' in hd else ''
        name = utils.cleantext(name) + " [COLOR deeppink]" + duration.strip() + "[/COLOR]"
        if videopage.startswith('/'): videopage = siteurl + videopage
        utils.addDownLink(name, videopage, 232, img, '')
    try:
        next_page = re.compile('href="([^"]+)" class="prevnext">&raquo;<', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 231, '', page)
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('234', ['url'], ['keyword', 'page'])
def Search(url, keyword=None, page=0):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 234, page)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl, page)


@utils.url_dispatcher.register('233', ['url'], ['page'])
def Cat(url, page=0):
    siteurl = sites[page]
    cathtml = utils.getHtml(url, '')
    match = re.compile('div class="col-sm.+?a href="([^"]+)">.+?title-truncate">([^<]+)<.+?class="badge">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        if catpage.startswith('/'): catpage = siteurl + catpage
        name = name.strip().title() + " [COLOR deeppink]" + videos + "[/COLOR]"
        utils.addDir(utils.cleantext(name), catpage, 231, '', page)
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('232', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")

    videopage = utils.getHtml(url)
    refurl = re.compile('<iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    vp.progress.update(50, "", "Loading video page", "")
    utils.kodilog(refurl)
    refpage = utils.getHtml(refurl)
    
    videourl = re.compile('JuicyCodes.Run\(([^\)]+)\)', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
    videourl = videourl.replace('"+"','').replace('"','')
    videourl = base64.b64decode(videourl)
    
    videourl = utils.unpack(videourl)
    videolinks = re.compile('"src":"([^"]+)".+?"res":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videourl)
    list = {}
    for url, quality in videolinks:
        list[quality] = url
    url = utils.selector('Select quality', list, dont_ask_valid=True,  sort_by=lambda x: int(x), reverse=True)
    if not url:
        return
    videolink = url + '|Referer=' + refurl
    vp.play_from_direct_link(videolink)

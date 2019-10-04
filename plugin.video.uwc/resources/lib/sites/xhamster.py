'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream, hdgdl, holisticdioxide

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

import urllib2
import os
import re
import sys
import json

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

# xhamster serves different sites to newer and older browsers, a predefined user agent is needed
xhamster_headers = dict(utils.headers)
xhamster_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'

@utils.url_dispatcher.register('505')
def Main():
    utils.addDir('[COLOR hotpink]Categories - Straight[/COLOR]','https://xhamster.com/categories',508,'','')
    utils.addDir('[COLOR hotpink]Categories - Gay[/COLOR]','https://xhamster.com/gay/categories',508,'','')
    utils.addDir('[COLOR hotpink]Categories - Shemale[/COLOR]','https://xhamster.com/shemale/categories',508,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://xhamster.com/search.php?q=',509,'','')
    List('https://xhamster.com/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

    
@utils.url_dispatcher.register('506', ['url'])
def List(url):
    try:
        response = utils.getHtml(url, hdr=xhamster_headers)
    except:
        return None
    
    match0 = re.compile('<head>(.*?)</head>.*?index-videos.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(response)
    header_block = match0[0][0]
    main_block = match0[0][1]
    match = re.compile('thumb-image-container" href="([^"]+)".*?<i class="thumb-image-container__icon([^>]+)>.*?src="([^"]+)".*?alt="([^"]+)".*?duration">([^<]+)</div', re.DOTALL | re.IGNORECASE).findall(main_block)
    for video, hd, img, name, length in match:
        hd = ' [COLOR orange]HD[/COLOR]' if 'hd' in hd else ''
        name = utils.cleantext(name) + hd + ' [COLOR hotpink]' + length + '[/COLOR]'
        utils.addDownLink(name, video, 507, img, '')
    try:
        next_page = re.compile('<link rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(header_block)[0]
        utils.addDir('Next Page', next_page, 506, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('507', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    response = utils.getHtml(url, hdr=xhamster_headers)    
    match = get_xhamster_link(response)
    vp.progress.update(25, "", "Loading video page", "")
    if match:
        vp.play_from_direct_link(match)
    else:
        utils.notify('Oh oh','Couldn\'t find a video')


@utils.url_dispatcher.register('508', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, hdr=xhamster_headers)
    match0 = re.compile('<div class="letter-blocks page">(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    match = re.compile('<a href="(.+?)" >([^<]+)<').findall(match0[0])
    for url, name in match:
        utils.addDir(name, url, 506, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)
    
@utils.url_dispatcher.register('509', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 509)
    else:
        title = keyword.replace(' ','_')
        searchUrl = searchUrl + title
        List(searchUrl)

def get_xhamster_link(html):
    for line in html.split('\n'):
        line = line.strip()
        if line.startswith("window.initials"):
            jsonline = line[18:-1]
            break
    else:
        return None
    try:        
        xjson = json.loads(jsonline)
        highest_quality_source = xjson["xplayerSettings"]["sources"]['standard']["mp4"][0]#[-1]
        links = (highest_quality_source["url"], highest_quality_source["fallback"])
        return links[0] if 'xhcdn' in links[0] or not links[1] else links[1]
    except IndexError:
        return None

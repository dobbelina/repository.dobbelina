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

import xbmcplugin
from resources.lib import utils

siteurl = 'https://www.hotpornfile.org/'


@utils.url_dispatcher.register('550')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl, 553,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', siteurl + '?s=', 554,'','')
    List(siteurl + 'category/videos')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('551', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="thumbnail".+?src="([^"]+)".+?href="([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, videopage, name in match:
        name = utils.cleantext(name)
        if 'IMAGESET' in name.upper():
            continue
        name = name.replace('720p','[COLOR yellow]720p[/COLOR]')
        name = name.replace('1080p','[COLOR orange]1080p[/COLOR]')
        name = name.replace('2160p','[COLOR red]2160p[/COLOR]')
        name = name.replace('XXX ','')
        name = name.replace('MP4','')
        utils.addDownLink(name, videopage, 552, img, '')
    try:
        (next_page, page_nr) = re.compile('class="next" href="([^"]+/(\d+)/??)">&raquo;<', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Page #' + page_nr, next_page, 551,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('554', ['url'], ['keyword'])      
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 554)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


@utils.url_dispatcher.register('553', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="([^"]+/category/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    cats = []
    for catpage, name in match:
        if not name in cats: 
            utils.addDir(utils.cleantext(name), catpage, 551, '')
            cats.append(name)
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('552', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url, url)
    videourl = re.compile('"><iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    vp.progress.update(50, "", "Loading video page", "")
    videourl1 = utils.getHtml(videourl, url)
    packed = re.compile('>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(videourl1)[0]
    unpacked = utils.unpack(packed)
    vp.progress.update(75, "", "Loading video page", "")    
    source = re.search('src:"([^"]+)"', unpacked)
    if source:
        vp.play_from_direct_link(source.group(1))
    else:
        utils.notify('Video not found.')

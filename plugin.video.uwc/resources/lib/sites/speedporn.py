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
import base64
from resources.lib import utils
import xbmc
import xbmcplugin
import xbmcgui
import sys
import urllib2,urllib
@utils.url_dispatcher.register('780')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'https://speedporn.net/porn-genres/', 783, '', '')
    utils.addDir('[COLOR hotpink]Tags[/COLOR]', 'https://speedporn.net/home/', 784, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://speedporn.net/?s=',785,'','')
    List('https://speedporn.net/?filter=latest')


@utils.url_dispatcher.register('781', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    match = re.compile('<article id=.+?href="([^"]+)"\s*title="([^"]+)".+?data-src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 782, img, '')
    try:
        nextp = re.compile('<link rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Next Page', nextp, 781,'')
    except:
        pass
        
    xbmcplugin.endOfDirectory(utils.addon_handle)


def url_decode(str):
    if '/goto/' not in str:
        result = str
    else:
        try:
            result = url_decode(base64.b64decode(re.search('/goto/(.+)', str).group(1)))
        except:
            result = str
    return result


@utils.url_dispatcher.register('783', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="(https://speedporn.net\?genres=[^"]+)"\s*title="([^"]+)".+?src="([^"]+)" class', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in match:
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 781, img)
    match = re.compile('href="(https://speedporn.net[^"]+)" class="inactive">(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for pageurl, pagenr in match:
        utils.addDir('[COLOR pink]Page ' + str(pagenr) + '[/COLOR]', pageurl, 783, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('784', ['url'])
def Tags(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a href="(https://speedporn.net/tag/[^"]+)">([^<]+)</a>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 781, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('782', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)

    srcs = re.compile('<a title="([^"]+)" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    for title, src in srcs:
        title = title.replace(name.split("[",1)[0],'').replace(' on','')
        if '/goto/' in src:
            src = url_decode(src)
        if vp.resolveurl.HostedMediaFile(src):
            links[title] = src
        if 'mangovideo' in src:
            title = title.replace(' - ','')
            html = utils.getHtml(src)
            match = re.compile("video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)[0]
            links[title] = match
    videourl = utils.selector('Select server', links, dont_ask_valid=False, reverse=True)
    if not videourl:
        return
    vp.progress.update(90, "", "Loading video page", "")
    if 'mango' in videourl:
        vp.direct_regex = '(' + re.escape(videourl) + ')'
        vp.play_from_html(html)
    else:
        vp.play_from_link_to_resolve(videourl)


@utils.url_dispatcher.register('785', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 785)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

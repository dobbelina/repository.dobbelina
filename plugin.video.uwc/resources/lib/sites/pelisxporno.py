'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 Fr33m1nd

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


@utils.url_dispatcher.register('140')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.pelisxporno.com/',143,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.pelisxporno.com/?s=',144,'','')
    List('http://www.pelisxporno.com/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('141', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('id="video.+?img src="([^"]+)".+?href="([^"]+)" rel="bookmark" title="([^"]+)".+?class="duration" align="right">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)    
    for img, videopage, name, duration in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + duration + "[/COLOR]"
        utils.addDownLink(name, videopage, 142, img, '')
    try:
        nextp=re.compile('<a class="nextpostslink" rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', nextp[0], 141,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('144', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 144)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('143', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<li id="categories-4"(.*?)</ul>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    match1 = re.compile('href="([^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
    for catpage, name in match1:
        utils.addDir(name, catpage, 141, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('142', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download = download)
    vp.progress.update(25, "", "Loading video page", "")
    videohtml = utils.getHtml(url, url)
    match = re.compile('<iframe[^/]+src="([^"]+)"[^>]+frameborder', re.DOTALL | re.IGNORECASE).findall(videohtml)
    links = {}
    for i,link in enumerate(match):
        if not link.startswith("http"): link = "https:" + link
        if vp.resolveurl.HostedMediaFile(link):
            links[str(i) + ': ' + link.split('/')[2]] = link
        if 'mixdrop.co' in link:
            html = utils.getHtml(link, url)
            videolink = re.compile('MDCore.vsrc = "([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)[0]
            if not videolink.startswith("http"): videolink = "https:" + videolink
            links[str(i) + ': ' + 'mixdrop.co'] = videolink 
    videourl = utils.selector('Select link', links, dont_ask_valid=False)
    if not videourl:
        return
    if 'mixdrop.co' in videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)


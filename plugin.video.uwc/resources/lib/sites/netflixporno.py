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
import urllib2
import xbmcplugin, xbmcgui
from resources.lib import utils

progress = utils.progress


@utils.url_dispatcher.register('810')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://netflixporno.net/search/', 813, '', '')
    utils.addDir('[COLOR hotpink]New Release[/COLOR]','https://netflixporno.net/genre/new-release/', 811, '', '')
    utils.addDir('[COLOR hotpink]XXX Scenes[/COLOR]','https://netflixporno.net/genre/clips-scenes/', 811, '', '')
    utils.addDir('[COLOR hotpink]Parody Movies[/COLOR]','https://netflixporno.net/genre/parodies/', 811, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://netflixporno.net/', 814, '', '')
    utils.addDir('[COLOR hotpink]Studios[/COLOR]','https://netflixporno.net/', 815, '', '')
    List('https://netflixporno.net/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('811', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('<article[^>]+>.+?<a href="([^"]+)".*?src="([^"]+)".+?Title">([^"]+)</div', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 812, img, '')
    try:
        nextp=re.compile('<a class="next page-numbers" href="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        nextp = nextp[0].replace("&#038;", "&")
        utils.addDir('Next Page', nextp, 811,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('813', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 813)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        utils.kodilog("NetFlixPorno Searching URL: " + searchUrl)
        List(searchUrl)


@utils.url_dispatcher.register('814', ['url'])
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except urllib2.URLError as e:
        utils.notify(e)
        return
    match = re.compile('rel="noopener noreferrer" href="(.+?)">(.+?)</a>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match[4:-1]:
        utils.addDir(name, catpage, 811, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('815', ['url'])
def Studios(url):
    try:
        studhtml = utils.getHtml(url, '')
    except urllib2.URLError as e:
        utils.notify(e)
        return
    match = re.compile('menu-category-list"><a href="(.+?)">(.+?)</a>', re.DOTALL | re.IGNORECASE).findall(studhtml)
    for studpage, name in match[2:]:
        utils.addDir(name, studpage, 811, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('812', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    try:
        html = utils.getHtml(url)
    except urllib2.URLError as e:
        utils.notify(e)
        return
#    html = re.compile('<center><!-- Display player -->(.+?)<center>', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    srcs = re.compile('<a title="([^"]+)" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
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

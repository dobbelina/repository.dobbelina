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

import xbmcplugin
from resources.lib import utils

siteurl = 'http://ipornovideos.com/'

@utils.url_dispatcher.register('260')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl, 263, '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', siteurl + '?s=', 264, '')
    List(siteurl)


@utils.url_dispatcher.register('261', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    videos = listhtml.split('<div id="post')
    for vid in videos:
        match = re.compile('href="([^"]+)" rel="bookmark">([^<]+)<(.+)', re.DOTALL | re.IGNORECASE).findall(vid)
        if match:
            (videopage, name, img) = match[0]
        else:
            continue
        m = re.search("img src='(.+?)'", img)
        if m:
            img = m.group(1)
        else:
            img = ''
        name = name.split('(')
        hd = name[-1]
        name[-1] = ''
        name = ''.join(name)
        name = utils.cleantext(name)
        if 'FullHD' in hd:
            name = name + '[COLOR orange] FullHD[/COLOR]'
        else:
            if 'HD' in hd:
                name = name + '[COLOR yellow] HD[/COLOR]'
        utils.addDownLink(name, videopage, 262, img, '')
    try:
        next_page = re.compile('href="([^"]+)" ><span class="meta-nav">&larr;<', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 261, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('264', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 264)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


@utils.url_dispatcher.register('263', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<li class="cat-item[^>]+><a href="([^"]+)" >([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        utils.addDir(utils.cleantext(name), catpage, 261, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('262', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex="<a href='([^']+)'[^>]+>Watch Online")
    vp.progress.update(25, "", "Loading video page", "")
    vp.play_from_site_link(url, url)

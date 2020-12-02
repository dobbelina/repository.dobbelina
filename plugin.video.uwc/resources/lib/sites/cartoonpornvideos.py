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

import xbmcplugin, xbmcgui
from resources.lib import utils


@utils.url_dispatcher.register('930')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://www.cartoonpornvideos.com/categories/',933,'','')
    utils.addDir('[COLOR hotpink]Characters[/COLOR]','https://www.cartoonpornvideos.com/characters/',935,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.cartoonpornvideos.com/search/video/',934,'','')
    List('https://www.cartoonpornvideos.com/videos/straight/all-recent-1.html')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('931', ['url'])
def List(url):
    try:
        html = utils.getHtml(url, '')
    except:
        return None
    #match = re.compile('class="item".+?href="(.*?)".+?src="(.+?)".+?alt="(.+?)".+?flag-hd">(.+?)<.+?time">(.+?)<', re.DOTALL | re.IGNORECASE).findall(html)[0]
    match = re.compile('class="item".+?href="(.*?)".+?src="(.+?)".+?alt="(.+?)".+?class="time">(.+?)</span>', re.DOTALL | re.IGNORECASE).findall(html)
    for videopage, img, name, duration in match:
        name = '[COLOR yellow]' + duration.strip() + '[/COLOR] ' + utils.cleantext(name)
        utils.addDownLink(name, videopage, 932, img, '')
    try:
        (nextlink, nextp) = re.compile('a href="([^"]+-(\d*)\.html)" class="next"', re.DOTALL | re.IGNORECASE).findall(html)[0]
        utils.addDir('Next Page (%s)'%str(nextp), nextlink, 931,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('932', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    try:
        html = utils.getHtml(url, '')
    except:
        return None
    videourl = re.compile('file: "(.+?)"', re.DOTALL | re.IGNORECASE).findall(html)[0]
    #vp.play_from_direct_link(videourl)
    #vp.play_from_link_to_resolve(url)
    vp.play_from_html(html)


@utils.url_dispatcher.register('933', ['url'])
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="item video-category".+?href="([^"]+)".+?src="([^"]+)".+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name in match:
        utils.addDir(name, catpage, 931, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('934', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 934)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

@utils.url_dispatcher.register('935', ['url'])
def Characters(url):
    try:
        charhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('div class="item".+?href="([^"]+)".+?src="([^"]+)".+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(charhtml)
    for charpage, img, name in match:
        utils.addDir(name.replace('Videos', '').strip(), charpage, 931, img.replace('\r\n', ''))
    xbmcplugin.endOfDirectory(utils.addon_handle)

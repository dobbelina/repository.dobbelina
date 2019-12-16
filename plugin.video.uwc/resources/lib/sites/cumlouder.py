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

siteurl = 'https://www.cumlouder.com'


@utils.url_dispatcher.register('210')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl + '/categories/', 213,'','')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]', siteurl + '/channels/', 213,'','')
    utils.addDir('[COLOR hotpink]Series[/COLOR]', siteurl + '/series/', 213,'','')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + '/girls/', 213,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', siteurl + '/search/?q=', 214,'','')
    List(siteurl + '/porn/')


@utils.url_dispatcher.register('211', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('a class="muestra-escena" href="([^"]+)".+?data-src="([^"]+)".+?alt="([^"]+)".+?class="ico-minutos sprite"></span>([^<]+)<(.+?)</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, duration, hd in match:
        hd = '[COLOR orange]HD[/COLOR]' if 'hd sprite' in hd else ''
        name = utils.cleantext(name) + "[COLOR deeppink]" + duration + "[/COLOR] " + hd
        if videopage.startswith('/'): videopage = siteurl + videopage
        if img.startswith('//'): img = 'https:' + img
        utils.addDownLink(name, videopage, 212, img, '')
    try:
        next_page = re.compile('class="btn-pagination" itemprop="name"\s+href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', siteurl + next_page, 211,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('214', ['url'], ['keyword'])      
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 214)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


@utils.url_dispatcher.register('213', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('(?:-url=|onclick=).+?href="([^"]+)".+?data-src="([^"]+)".+?alt="([^"]+)".+?>((?:\d+|[\s\d]+Videos))<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, videos in match:
        if catpage.startswith('/'): catpage = siteurl + catpage
        if img.startswith('//'): img = 'https:' + img
        name = name.title() + " [COLOR deeppink]" + videos + "[/COLOR]"
        utils.addDir(utils.cleantext(name), catpage, 211, img)
    try:
        next_page = re.compile('class="btn-pagination" itemprop="name"\s+href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        page_nr = [x for x in next_page.split('/') if x.isdigit()][0]
        utils.addDir('Next Page (' + page_nr + ')', siteurl + next_page, 213,'')
    except:
        pass           
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('212', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    embedurl = re.compile('<iframe src="([^"]+/\d+/)"', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    vp.progress.update(50, "", "Loading video page", "")
    embedpage = utils.getHtml(embedurl)
    videourl = re.compile('<source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(embedpage)[0]
    videourl = videourl.replace('&amp;','&')
    if videourl.startswith('//'): videourl = 'https:' + videourl
    videourl += '|Referer=' + embedurl
    vp.play_from_direct_link(videourl)

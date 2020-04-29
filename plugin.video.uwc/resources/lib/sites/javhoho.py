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


@utils.url_dispatcher.register('310')
def Main():
    utils.addDir('[COLOR hotpink]JAV Uncensored[/COLOR]','https://javhoho.com/category/free-jav-uncensored/',311,'','')
    utils.addDir('[COLOR hotpink]JAV Censored[/COLOR]','https://javhoho.com/category/free-jav-censored/',311,'','')
    utils.addDir('[COLOR hotpink]Chinese Porn[/COLOR]','https://javhoho.com/category/free-chinese-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Korean Porn[/COLOR]','https://javhoho.com/category/free-korean-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Asian Porn[/COLOR]','https://javhoho.com/category/free-asian-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Virtual Reality Porn[/COLOR]','https://javhoho.com/category/free-jav-vr-virtual-reality/',311,'','')    
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://javhoho.com/search/',314,'','')
    List('https://javhoho.com/all-movies-free-jav-uncensored-censored-asian-porn-korean/')


@utils.url_dispatcher.register('311', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        
        return None
    match = re.compile('class="item-thumbnail".+?href="([^"]+)">.+?srcset="(\S+).+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        for videopage, img, name in match:
            name = utils.cleantext(name)
            utils.addDownLink(name, videopage, 312, img, '')
    else:   # search
        match = re.compile('class="item-thumbnail".+?href="([^"]+)".+?title="([^"]+)".+?srcset="(\S+)', re.DOTALL | re.IGNORECASE).findall(listhtml)       
        for videopage, name, img in match:
            name = utils.cleantext(name)
            utils.addDownLink(name, videopage, 312, img, '')
    try:
        next_page = re.compile('href="([^"]+)">&raquo;<').findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 311, '')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('314', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 314)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        utils.kodilog(searchUrl)
        List(searchUrl)


@utils.url_dispatcher.register('313', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)">.+?src="([^"]+)".+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"    
        utils.addDir(name, catpage, 311, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('312', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    videohtml = utils.getHtml(url)
    try: 
        allplayer = re.compile('<iframe src="(//allplayer[^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
        allplayer = 'https:' + allplayer
        vp.progress.update(20, "", "Loading video page", "")
        allplayerhtml = utils.getHtml(allplayer,url)
        vp.progress.update(40, "", "Loading video page", "")    
        packed = re.compile('>(eval.+?)jwplayer\(\)', re.DOTALL | re.IGNORECASE).findall(allplayerhtml)[0]
        unpacked = utils.unpack(packed)
        unpacked = unpacked.replace('\\','')
        directlinks = re.compile("file:'([^']+)',.+?,label:'([^']+)'", re.DOTALL | re.IGNORECASE).findall(unpacked)
        vp.progress.update(60, "", "Loading video page", "")
        for video_link, quality in directlinks:
            links[quality] = video_link
        selected = utils.selector('Select quality', links, dont_ask_valid=True, sort_by=lambda x: int(x[:-1]), reverse=True)
        if not selected: return
        vp.play_from_direct_link(selected + '|Referer=' + allplayer)
    except:
        vp.play_from_html(videohtml)
    

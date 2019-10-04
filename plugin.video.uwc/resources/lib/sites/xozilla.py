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

import xbmcplugin
from resources.lib import utils

siteurl = 'https://www.xozilla.com'
    
@utils.url_dispatcher.register('770')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl+'/categories/',773,'','')
    utils.addDir('[COLOR hotpink]Categories - TOP RATED[/COLOR]',siteurl+'/categories/',776,'','')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]',siteurl+'/channels/',777,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/search/',774,'','')
    List(siteurl + '/latest-updates/')
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('771', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<a href="([^"]+)" class="item.+?vthumb=.+?thumb="([^"]+)".+?"duration">([^<]+)</div>.+?class="title">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, duration, name in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " +  duration + "[/COLOR]"
        utils.addDownLink(name, videopage, 772, img, '')
    try:
	page = re.compile('<li class="page-current"><span>0*(\d+)<\/span>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
	nextp = re.sub(r'/\d+/', '/', url) + str(int(page) + 1) + '/'
        utils.addDir('Next Page (' + str(int(page) + 1) +')', nextp, 771,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('773', ['url'])
def Cat(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('a href="([^"]+)">([^<]+)<span class="rating">', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        utils.addDir(name, catpage, 771, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('776', ['url'])
def CatTR(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('"item" href="([^"]+)" title="([^"]+)".+?src="([^"]+)".+?i>([^<]+)videos<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name) + "[COLOR deeppink] " +  count + "[/COLOR]"
        utils.addDir(name, catpage, 771, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('777', ['url'])
def Chan(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('"item" href="([^"]+)" title="([^"]+)".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 771, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('772', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, '', 'Download:.+?href="([^"]+)"')

    videopage = utils.getHtml(url, '')
    match = re.compile('Download:(.+?)<\/div>', re.DOTALL | re.IGNORECASE).findall(videopage)
    srcs = re.compile('href="([^"]+)".+?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
    sources =  {}	
    for videourl, quality in srcs:
        if videourl:
            sources[quality] = videourl
#    videourl = utils.selector('Select quality', sources, dont_ask_valid=True, sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
    videourl = utils.selector('Select quality', sources, dont_ask_valid=True, sort_by=lambda x: int(x.split('x')[0]), reverse=True)
    vp.play_from_direct_link(videourl)


@utils.url_dispatcher.register('774', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 774)
    else:
        title = keyword.replace(' ','-')
        searchUrl = searchUrl + title + '/'
        List(searchUrl)


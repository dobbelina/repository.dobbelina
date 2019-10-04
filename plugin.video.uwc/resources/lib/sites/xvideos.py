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

siteurl = 'https://www.xvideos.com'
hdr = dict(utils.headers)
hdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'

    
@utils.url_dispatcher.register('790')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl,793,'','')
    utils.addDir('[COLOR hotpink]Tags[/COLOR]',siteurl+'/tags',796,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/?k=',794,'','')
    List(siteurl)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('791', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, hdr=hdr)
    except:
        return None
    match = re.compile('div id="video.+?href="([^"]+)".+?data-src="([^"]+)"(.+?)title="([^"]+)">.+?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, res, name, duration in match:
        match = re.search('mark">(.+?)<', res)
        if match:
            res = match.group(1)
        else:
            res = ' '
        name = utils.cleantext(name) + "[COLOR deeppink] " +  duration + "[/COLOR]" + "[COLOR blue] " +  res + "[/COLOR]"
        utils.addDownLink(name, siteurl + videopage, 792, img, '')
    try:
        (npage, pagenr) = re.compile('href="([^"]+\D(\d+)/{0,1})" class="no-page next-page', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        npage = npage.replace('&amp;','&')
        pagenr = int(pagenr)+1
        utils.addDir('Next Page (' +str(pagenr) + ')', siteurl + npage, 791,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('793', ['url'])
def Cat(url):
    try:
        cathtml = utils.getHtml(url, hdr=hdr)
    except:
        return None
    match = re.compile('href="([^"]+)" class="btn btn-default">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        utils.addDir(name, siteurl + catpage, 791, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('796', ['url'])
def CatTR(url):
    try:
        cathtml = utils.getHtml(url, hdr=hdr)
    except:
        return None
    match = re.compile('href="([^"]+)"><b>([^<]+)</b>.+?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " +  count + "[/COLOR]"
        utils.addDir(name, siteurl + catpage, 791, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('792', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, '', 'Download:.+?href="([^"]+)"')
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url, hdr=hdr)
    videopage1 = re.compile('iframe src=&quot;(.+?)&quot;', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    html = utils.getHtml(videopage1, url)
#   best quality    
    srcs = re.compile("html5player.setVideo(HLS.*?)\('([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)                          
#   select quality
#    srcs = re.compile("html5player.setVideo(HLS|UrlLow|UrlHigh)\('([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)
    sources = {}
    for quality, videourl in srcs:
        if videourl:
            sources[quality] = videourl
    videourl = utils.selector('Select quality', sources, dont_ask_valid=True)
    vp.play_from_direct_link(videourl)


@utils.url_dispatcher.register('794', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 794)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


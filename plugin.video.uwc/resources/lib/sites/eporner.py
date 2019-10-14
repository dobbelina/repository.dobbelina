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

siteurl = 'https://www.eporner.com'
    
@utils.url_dispatcher.register('540')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl + '/categories/',543,'','')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]',siteurl + '/pornstars/',545,'','')
    utils.addDir('[COLOR hotpink]Lists[/COLOR]',siteurl,546,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/search/',544,'','')
    List(siteurl + '/category/all/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('541', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('div class="mb.+?class="mvhdico">.*?<span>([^<]+)<.+?href="([^"]+)"\s*title="([^"]+)".+?src="([^"]+)".+?class="mbtim">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for hd, videopage, name, img, duration in match:
        name = utils.cleantext(name) + "[COLOR orange] " + hd + "[COLOR deeppink] " +  duration + "[/COLOR]"
        utils.addDownLink(name, siteurl + videopage, 542, img, '')
    try:
        nextp, page = re.compile("href='([^']+/(\d+)/)' class='nmnext' title='Next page'", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Next Page (' + page +')', siteurl + nextp, 541,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('542', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, '"contentUrl": "([^"]+)"')
    vp.play_from_site_link(url)

@utils.url_dispatcher.register('543', ['url'])
def Cat(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="ctbinner"[^=]+href="([^"]+)" title="([^"]+)"[^:]+img src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in match:
        catpage = siteurl + catpage
        utils.addDir(name, catpage, 541, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('545', ['url'])
def Pornstars(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="mbprofile"[^=]+href="([^"]+)" title="([^"]+)".+?img src="([^"]+)".+?Videos:[^>]+>(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " +  count + "[/COLOR]"
        catpage = siteurl + catpage
        utils.addDir(name, catpage, 541, img)
    try:
        nextp, page = re.compile("href='([^']+/(\d+)/)' class='nmnext' title='Next page'", re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        utils.addDir('Next Page (' + page +')', siteurl + nextp, 545,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('546', ['url'])
def Lists(url):
    lists = {}
    lists['HD Porn 1080p Videos - Recent'] = siteurl + '/category/hd-1080p/'
    lists['HD Porn 1080p Videos - Top Rated'] = siteurl + '/category/hd-1080p/SORT-top-rated/'
    lists['HD Porn 1080p Videos - Longest'] = siteurl + '/category/hd-1080p/SORT-longest/'
    lists['60 FPS Porn Videos - Recent'] = siteurl + '/category/60fps/'
    lists['60 FPS Porn Videos - Top Rated'] = siteurl + '/category/60fps/SORT-top-rated/'
    lists['60 FPS Porn Videos - Longest'] = siteurl + '/category/60fps/SORT-longest/'
    lists['Popular Porn Videos'] = siteurl + '/popular-videos/'
    lists['Best HD Porn Videos'] = siteurl + '/top-rated/'
    lists['Currently Watched Porn Videos'] = siteurl + '/currently/'
    lists['4K Porn Ultra HD - Recent'] = siteurl + '/category/4k-porn/'
    lists['4K Porn Ultra HD - Top Rated'] = siteurl + '/category/4k-porn/SORT-top-rated/'
    lists['4K Porn Ultra HD - Longest'] = siteurl + '/category/4k-porn/SORT-longest/'
    lists['HD Sex Porn Videos - Recent'] = siteurl + '/category/hd-sex/'
    lists['HD Sex Porn Videos - Top Rated'] = siteurl + '/category/hd-sex/SORT-top-rated/'
    lists['HD Sex Porn Videos - Longest'] = siteurl + '/category/hd-sex/SORT-longest/'
    lists['Amateur Porn Videos - Recent'] = siteurl + '/category/amateur/'
    lists['Amateur Porn Videos - Top Rated'] = siteurl + '/category/amateur/SORT-top-rated/'
    lists['Amateur Porn Videos - Longest'] = siteurl + '/category/amateur/SORT-longest/'
    lists['Solo Girls Porn Videos - Recent'] = siteurl + '/category/solo/'
    lists['Solo Girls Porn Videos - Top Rated'] = siteurl + '/category/solo/top-rated/'
    lists['Solo Girls Porn Videos - Longest'] = siteurl + '/category/solo/longest/'
    lists['VR Porn Videos - Recent'] = siteurl + '/category/vr-porn/'
    lists['VR Porn Videos - Top Rated'] = siteurl + '/category/vr-porn/SORT-top-rated/'
    lists['VR Porn Videos - Longest'] = siteurl + '/category/vr-porn/SORT-longest/'
    url = utils.selector('Select', lists)
    if not url:
        return
    List(url)

@utils.url_dispatcher.register('544', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 544)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title 
        List(searchUrl)
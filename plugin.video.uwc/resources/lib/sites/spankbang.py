'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 NothingGnome

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
import json

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

progress = utils.progress

base_url = 'https://spankbang.com'
main_mode = 440
list_mode =  441
play_mode = 442
categories_mode = 443
search_mode = 444


@utils.url_dispatcher.register('440')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://spankbang.com/s/', search_mode, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://spankbang.com/categories', categories_mode, '', '')
    utils.addDir('[COLOR hotpink]4k videos[/COLOR]','https://spankbang.com/new_videos/?4k=1', list_mode, '', '')
    utils.addDir('[COLOR hotpink]1080p videos[/COLOR]','https://spankbang.com/new_videos/?1080p=1', list_mode, '', '')
    List('https://spankbang.com/new_videos/1/')


@utils.url_dispatcher.register('441', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    main_block = re.compile('<main id="container">(.*?)</main>', re.DOTALL).findall(listhtml)[0]
    match = re.compile('<a href="(\/[^"]+\/)video[^"]+" class="thumb.*?data-src="([^"]+)".*?alt="([^"]+)".+?<span class="i-len">(.*?)<.+?<span class="i-hd">(.*?)<', re.DOTALL).findall(main_block)
    for videopage, img, name, duration, hd in match:
        videopage = videopage + "embed/"
#        res = re.findall('"i-hd">(.+?)<', hd, re.DOTALL | re.IGNORECASE)
#        if res == []:
#            hd = ""
#        else:
#            hd = "[COLOR orange] " + res[0]
        name = utils.cleantext(name) + "[COLOR orange] " + hd + " [COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, base_url + videopage, play_mode, img, '')
    try:
        nextp=re.compile('<li class="active"><a>.+?</a></li><li><a href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', base_url + nextp[0], list_mode)        
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('445', ['url'])
def List4k(url):
    List(url)

@utils.url_dispatcher.register('446', ['url'])
def List1080p(url):
    List(url)

@utils.url_dispatcher.register('444', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, search_mode)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title + '/'
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('443', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a href="/category/([^"]+)"><img src="([^"]+)"><span>([^>]+)</span>', re.DOTALL).findall(cathtml)
    for catpage, img, name in match:
        utils.addDir(name, base_url + '/category/' + catpage, list_mode, base_url + img, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('442', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videohtml = utils.getHtml(url, '')
    stream_key = re.compile('data-streamkey="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
    url = 'https://spankbang.com/api/videos/stream'
    form_data = { 'id': stream_key, 'data': 0 }
#, 'sb_csrf_session': sb_csrf_session }
    headers = {
    'Referer': 'https://spankbang.com/',
#   'X-CSRFToken': sb_csrf_session,
    }
    resp = utils.postHtml(url, form_data=form_data, headers=headers, compression=False, NoCookie=None)
#    sources = {}
#    srcs = re.compile('"stream_url_(240p|320p|480p|720p|1080p|4k)":\["([^"]+)"', re.DOTALL | re.IGNORECASE).findall(resp)
#    if not srcs:
#        srcs = re.compile('"stream_url_m(3u)8":\["([^"]+)"', re.DOTALL | re.IGNORECASE).findall(resp)
#    for quality, videourl in srcs:
#        if videourl:
#            sources[quality] = videourl
#    videourl = utils.selector('Select quality', sources, dont_ask_valid=True, sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
    sources = json.loads(resp)
    videourl = sources['m3u8'][0]
    if not videourl:
        return
    vp.play_from_direct_link(videourl)


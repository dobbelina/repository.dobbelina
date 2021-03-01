'''
    Cumination
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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('spankbang', '[COLOR hotpink]SpankBang[/COLOR]', 'https://spankbang.com/', 'spankbang.png',
                 'spankbang')

progress = utils.progress


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 's/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    List(site.url + 'new_videos/1/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    listhtml = re.compile(r'<main(.*?)</main>', re.DOTALL).findall(listhtml)[0]
    match = re.compile(r'class="video-item\s*".+?href="([^"]+).+?data-src="([^"]+).+?(<p.+?</p>)', re.DOTALL).findall(listhtml)
    for videopage, img, info in match:
        name = re.findall(r'class="n">(?:<strong>[^<]+</strong>)?\s*(?:<strong>[^<]+</strong>)?([^<]+)', info)[0]
        duration = re.findall(r'class="l">([^<]+)', info)[0]
        if '"h"' in info:
            hd = re.findall(r'class="h">([^<]+)', info)[0]
        else:
            hd = ""
        name = utils.cleantext(name)
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, duration=duration, quality=hd)
    nextp = re.compile('<li class="active"><a>.+?</a></li><li><a href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        site.add_dir('Next Page', site.url[:-1] + nextp.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title + '/'
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a href="/category/([^"]+)"><img src="([^"]+)"><span>([^>]+)</span>', re.DOTALL).findall(cathtml)
    for catpage, img, name in match:
        site.add_dir(name, site.url[:-1] + '/category/' + catpage, 'List', site.url[:-1] + img, '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, '')
    sources = {}
    srcs = re.compile(r'''["'](240p|320p|480p|720p|1080p|4k)["']:\s*\[["']([^"']+)''', re.DOTALL | re.IGNORECASE).findall(html)
    for quality, videourl in srcs:
        if videourl:
            sources[quality] = videourl
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
    vp.play_from_direct_link(videourl.replace(r'\u0026', '&'))

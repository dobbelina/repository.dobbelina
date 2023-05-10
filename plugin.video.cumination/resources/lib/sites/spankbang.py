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

site = AdultSite('spankbang', '[COLOR hotpink]SpankBang[/COLOR]', 'https://spankbang.com/', 'spankbang.png', 'spankbang')
filterQ = utils.addon.getSetting("spankbang_quality") or 'All'
filterL = utils.addon.getSetting("spankbang_length") or 'All'


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'pornstars_alphabet', 'Models_alphabet', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 's/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Quality: [/COLOR] [COLOR orange]{}[/COLOR]'.format(filterQ), '', 'FilterQ', '', Folder=False)
    site.add_dir('[COLOR hotpink]Length: [/COLOR] [COLOR orange]{}[/COLOR]'.format(filterL), '', 'FilterL', '', Folder=False)
    List(site.url + 'new_videos/1/')
    utils.eod()


@site.register()
def List(url):
    filtersQ = {'All': '', '4k': 'uhd', '1080p': 'fhd', '720p': 'hd'}
    filtersL = {'All': '', '10+min': 10, '20+min': 20, '40+min': 40}
    if '?' in url:
        url = url.split('?')[0]
    url += '?o=new&q={}&d={}'.format(filtersQ[filterQ], filtersL[filterL])
    listhtml = utils.getHtml(url, '')
    listhtml = re.compile(r'<main(.*?)</main>', re.DOTALL).findall(listhtml)[0]
    videos = listhtml.split('class="video-item')
    for video in videos:
        match = re.compile(r'href="([^"]+).+?data-src="([^"]+)"(.+)', re.DOTALL).findall(video)
        if match:
            videopage, img, info = match[0]
            info = info.replace('<strong>', '').replace('</strong>', '')
            duration = ''
            hd = ''
            name = ''
            if 'class="l"' in info:
                duration = info.split('class="l">')[-1].split('<')[0]
            if 'class="h"' in info:
                hd = info.split('class="h">')[-1].split('<')[0]
            if 'class="n"' in info:
                name = info.split('class="n">')[-1].split('<')[0]
            name = utils.cleantext(name)
            site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, duration=duration, quality=hd)
    nextp = re.compile(r'href="([^"]+)">&raquo', re.DOTALL | re.IGNORECASE).search(videos[-1])
    nextps = re.compile(r'href="([^"]+)"\s*class="next">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        np = re.findall(r'/(\d+)/', nextp)[-1]
        lp = re.compile(r'>(\d+)<[^"]+class="next"><', re.DOTALL | re.IGNORECASE).findall(videos[-1])
        if lp:
            lp = '/' + lp[0]
        else:
            lp = ''
        site.add_dir('Next Page({}{})'.format(np, lp), site.url[:-1] + nextp, 'List', site.img_next)
    elif nextps:
        nextp = nextps.group(1)
        pgtxt = re.findall(r'class="status">(.*?)</span', listhtml)[0].replace('<span>/', 'of').capitalize()
        site.add_dir('Next Page... (Currently in {})'.format(pgtxt), site.url[:-1] + nextp, 'List', site.img_next)

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
def Tags(url):
    cathtml = utils.getHtml(url, '')
    matchmain = re.compile('<div class="search_holder">(.*?)</html', re.IGNORECASE | re.DOTALL).findall(cathtml)[0]
    match = re.compile('<li><a href="([^"]+)" class="keyword">([^<]+)<', re.DOTALL).findall(matchmain)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        site.add_dir(name, site.url[:-1] + catpage, 'List')
    utils.eod()


@site.register()
def Models_alphabet(url):
    cathtml = utils.getHtml(url, '')
    cathtml = cathtml.split('<ul class="alphabets">')[-1].split('</ul>')[0]
    match = re.compile(r'<li><a href="([^"]+)".*?>([^<]+)<', re.DOTALL).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, site.url[:-1] + catpage, 'Models', '', '')
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, '')
    cathtml = cathtml.split('<ul class="list">')[-1].split('</ul>')[0]
    match = re.compile(r'<li><a href="([^"]+)".*?>([^<]+)<.+?svg>([\s\d]+)</span', re.DOTALL).findall(cathtml)
    for catpage, name, videos in match:
        name = name + '[COLOR hotpink]{}[/COLOR]'.format(videos)
        site.add_dir(name, site.url[:-1] + catpage, 'List', '', '')
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
    videourl = utils.prefquality(sources, sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
    if not videourl:
        return
    vp.play_from_direct_link(videourl.replace(r'\u0026', '&'))


@site.register()
def FilterQ():
    filters = {'All': 1, '4k': 2, '1080p': 3, '720p': 4}
    f = utils.selector('Select resolution', filters.keys(), sort_by=lambda x: filters[x])
    if f:
        utils.addon.setSetting('spankbang_quality', f)
        utils.refresh()


@site.register()
def FilterL():
    filters = {'All', '10+min', '20+min', '40+min'}
    f = utils.selector('Select length', filters, reverse=True)
    if f:
        utils.addon.setSetting('spankbang_length', f)
        utils.refresh()

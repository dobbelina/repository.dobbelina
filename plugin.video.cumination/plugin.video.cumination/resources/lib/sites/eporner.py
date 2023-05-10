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
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite('eporner', '[COLOR hotpink]Eporner[/COLOR]', 'https://www.eporner.com/', 'https://static-eu-cdn.eporner.com/new/logo.png', 'eporner')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'cats/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstar-list/', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Lists[/COLOR]', site.url, 'Lists', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'recent/')
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    vids = listhtml.split('data-vp=')
    for i, vid in enumerate(vids):
        if i == 0:
            continue
        match = re.compile(r'Quality"><span>(.+?)<.+? href="([^"]+)".+?src="(http[^"]+)".+?href.+?>(.+?)<.+?title="Duration">([^"]+)<\/', re.DOTALL | re.IGNORECASE).findall(vid)
        if match:
            hd, videopage, img, name, duration = match[0]
            name = utils.cleantext(name)
            site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, duration=duration, quality=hd)
    nextp = re.compile(r"href='([^']+)' class='nmnext' title='Next page'", re.DOTALL | re.IGNORECASE).findall(vids[-1])
    if nextp:
        nextp = nextp[0]
        page = re.findall(r'\d+', nextp)[-1]
        site.add_dir('Next Page ({})'.format(page), site.url[:-1] + nextp, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    embed = re.compile("vid = '(.+?)'.+?hash = '(.+?)'", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    vid = embed[0]
    s = embed[1]
    hash = ''.join((encode_base_n(int(s[lb:lb + 8], 16), 36) for lb in range(0, 32, 8)))
    jsonUrl = 'https://www.eporner.com/xhr/video/' + vid + '?hash=' + hash + '&domain=www.eporner.com&fallback=false&embed=true&supportedFormats=dash,mp4'
    listJson = utils.getHtml(jsonUrl, '')
    videoJson = json.loads(listJson)
    vp.progress.update(75, "[CR]Loading video page[CR]")
    videoArray = {}
    for (k, v) in videoJson['sources']['mp4'].items():
        videoArray[k] = v['src']
    videourl = utils.prefquality(videoArray, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
    if videourl:
        vp.play_from_direct_link(videourl)


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="ctbinner"[^=]+href="([^"]+)" title="([^"]+)"[^:]+img src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in sorted(match, key=lambda x: x[1]):
        catpage = site.url[:-1] + catpage
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Pornstars(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile(r'class="mbprofile"[^=]+href="([^"]+)" title="([^"]+)".+?img src="([^"]+)".+?Videos:[^>]+>(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + count + "[/COLOR]"
        catpage = site.url[:-1] + catpage
        site.add_dir(name, catpage, 'List', '')
    nextp = re.compile(r"href='([^']+)' class='nmnext' title='Next page'", re.DOTALL | re.IGNORECASE).findall(cathtml)
    if nextp:
        page = re.findall(r'\d+', nextp[0])[-1]
        site.add_dir('Next Page ({})'.format(page), site.url[:-1] + nextp[0], 'Pornstars', site.img_next)
    utils.eod()


@site.register()
def Lists(url):
    lists = {}
    lists['HD Porn 1080p Videos - Recent'] = site.url + '/cat/hd-1080p/'
    lists['HD Porn 1080p Videos - Top Rated'] = site.url + '/cat/hd-1080p/SORT-top-rated/'
    lists['HD Porn 1080p Videos - Longest'] = site.url + '/cat/hd-1080p/SORT-longest/'
    lists['60 FPS Porn Videos - Recent'] = site.url + '/cat/60fps/'
    lists['60 FPS Porn Videos - Top Rated'] = site.url + '/cat/60fps/SORT-top-rated/'
    lists['60 FPS Porn Videos - Longest'] = site.url + '/cat/60fps/SORT-longest/'
    lists['Popular Porn Videos'] = site.url + '/popular-videos/'
    lists['Best HD Porn Videos'] = site.url + '/top-rated/'
    lists['Currently Watched Porn Videos'] = site.url + '/currently/'
    lists['4K Porn Ultra HD - Recent'] = site.url + '/cat/4k-porn/'
    lists['4K Porn Ultra HD - Top Rated'] = site.url + '/cat/4k-porn/SORT-top-rated/'
    lists['4K Porn Ultra HD - Longest'] = site.url + '/cat/4k-porn/SORT-longest/'
    lists['HD Sex Porn Videos - Recent'] = site.url + '/cat/hd-sex/'
    lists['HD Sex Porn Videos - Top Rated'] = site.url + '/cat/hd-sex/SORT-top-rated/'
    lists['HD Sex Porn Videos - Longest'] = site.url + '/cat/hd-sex/SORT-longest/'
    lists['Amateur Porn Videos - Recent'] = site.url + '/cat/amateur/'
    lists['Amateur Porn Videos - Top Rated'] = site.url + '/cat/amateur/SORT-top-rated/'
    lists['Amateur Porn Videos - Longest'] = site.url + '/cat/amateur/SORT-longest/'
    lists['Solo Girls Porn Videos - Recent'] = site.url + '/cat/solo/'
    lists['Solo Girls Porn Videos - Top Rated'] = site.url + '/cat/solo/top-rated/'
    lists['Solo Girls Porn Videos - Longest'] = site.url + '/cat/solo/longest/'
    lists['VR Porn Videos - Recent'] = site.url + '/cat/vr-porn/'
    lists['VR Porn Videos - Top Rated'] = site.url + '/cat/vr-porn/SORT-top-rated/'
    lists['VR Porn Videos - Longest'] = site.url + '/cat/vr-porn/SORT-longest/'
    url = utils.selector('Select', lists)
    if not url:
        return
    List(url)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


def encode_base_n(num, n, table=None):
    FULL_TABLE = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if not table:
        table = FULL_TABLE[:n]

    if n > len(table):
        raise ValueError('base %d exceeds table length %d' % (n, len(table)))

    if num == 0:
        return table[0]

    ret = ''
    while num:
        ret = table[num % n] + ret
        num = num // n
    return ret

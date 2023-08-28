"""
    Cumination
    Copyright (C) 2023 Team Cumination

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
"""

import re
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("hentaistream", "[COLOR hotpink]HentaiStream[/COLOR]", 'https://hstream.moe/', "https://hstream.moe/images/hs_banner.png", "hentaistream")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'search?order=recently-uploaded&page=1', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?s=', 'Search', site.img_search)
    List(site.url + 'search?order=recently-uploaded&page=1')


@site.register()
def List(url, episodes=True):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile('<div class="w-full.*?href="([^"]+)".*?<img alt="([^"]+)".*?src="/([^"]+)".*?<p[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, hd in match:
        name = utils.cleantext(name)
        hd = " [COLOR orange]{0}[/COLOR]".format(hd.upper())
        img = site.url + img
        site.add_download_link(name, videopage, 'Playvid', img, name, quality=hd)

    nextregex = 'rel="next"' if episodes else 'nextPage'
    np = re.compile(nextregex, re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        pagelookup = re.search(r"page=(\d+)", url).group(1)
        if pagelookup:
            np = int(pagelookup) + 1
            url = url.replace("page={0}".format(pagelookup), "page={0}".format(np))
            site.add_dir('Next Page ({0})'.format(np), url, 'List', site.img_next)
    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('for="genre-list-([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = site.url + 'search?order=recently-uploaded&page=1&tags[0]={}'.format(tagpage)
        site.add_dir(name, tagpage, 'List', '', name)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        url = url + title + '&order=recently-uploaded'
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vpage = utils.getHtml(url, site.url)
    videoid = re.search('id="e_id" type="hidden" value="([^"]+)"', vpage)

    if videoid:
        videoid = videoid.group(1)
    else:
        utils.notify('Oh Oh', 'No Videos found')
        return

    payload = {'episode_id': videoid}

    hstreamhdrs = utils.base_hdrs
    xsrftoken = get_cookies()
    xsrftoken = urllib_parse.unquote(xsrftoken)
    if not xsrftoken:
        utils.notify('Oh Oh', 'No Videos found')
        return

    hstreamhdrs['x-xsrf-token'] = xsrftoken
    hstreamhdrs['content-type'] = 'application/json'

    videojson = utils._postHtml(site.url + 'player/api', headers=hstreamhdrs, json_data=payload)
    videojson = json.loads(videojson)

    if videojson['legacy'] == 0:
        qualities = {'2160': '/2160/manifest.mpd',
                     '1080': '/1080/manifest.mpd',
                     '720': '/720/manifest.mpd'}
    else:
        qualities = {'2160': '/av1.2160p.webm',
                     '1080': '"/av1.1080p.webm',
                     '720': '/x264.720p.mp4'}

    if videojson['resolution'] == '1080':
        qualities.pop('2160')
    elif videojson['resolution'] == '720':
        qualities.pop('2160')
        qualities.pop('1080')

    videoquality = utils.prefquality(qualities, sort_by=lambda x: int(x), reverse=True)
    if not videoquality:
        utils.notify('Oh Oh', 'No Videos found')
        return

    videourl = 'https://str.h-dl.xyz/{}{}'.format(videojson['stream_url'], videoquality)
    suburl = 'https://str.h-dl.xyz/{}/eng.ass'.format(videojson['stream_url'])

    if utils.checkUrl(suburl):
        utils.playvid(videourl, name, subtitle=suburl)
    else:
        vp = utils.VideoPlayer(name, download)
        vp.progress.update(50, "[CR]Loading video[CR]")
        vp.play_from_direct_link(videourl)


def get_cookies():
    domain = site.url.split('/')[2]
    for cookie in utils.cj:
        if domain in cookie.domain and cookie.name == 'XSRF-TOKEN':
            return cookie.value
    return ''

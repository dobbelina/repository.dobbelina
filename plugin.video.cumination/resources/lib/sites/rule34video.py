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
from resources.lib import utils
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite

site = AdultSite('rule34video', '[COLOR hotpink]Rule34 Video[/COLOR]', 'https://rule34video.com/', 'rule34video.png', 'rule34video')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tag', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    utils.kodilog(url)
    listhtml = utils.getHtml(url, site.url)
    match =  re.compile('open-popup" href="([^"]+)" title="([^"]+)".*?original="([^"]+)"(.*?)time">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(listhtml)

    for videopage, name, img, hd, duration in match:
        name = utils.cleantext(name.strip())
        if 'hd' in hd:
            hd = " [COLOR orange]HD[/COLOR]"
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    nextp = re.compile(r'pager next">\s+<a href="/([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        nextp = site.url + nextp[0]

        site.add_dir('Next Page..', nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = "{0}{1}/".format(searchUrl, title)
        List(searchUrl)


@site.register()
def Tag(url):
    taghtml = utils.getHtml(url, site.url)
    items = re.compile(r'item">\s+<a href="([^"]+)">\s+<strong>([^<]+)<.strong>\s+<span>([^<]+)<', re.IGNORECASE | re.DOTALL).findall(taghtml)
    for tagpage, name, videos in items:
        name = '{} [COLOR orange]{}[/COLOR]'.format(name, videos)
        site.add_dir(name, tagpage, 'List')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    surl = re.search(r"video(?:_alt)?_url:\s*'([^']+)", html)
    if surl:
        vp.progress.update(50, "[CR]Video found[CR]")
        surl = surl.group(1)
        if surl.startswith('function/'):
            lcode = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, lcode)
        if 'get_file' in surl:
            surl = utils.getVideoLink(surl, site.url)
        surl = '{0}|User-Agent=iPad&Referer={1}'.format(surl, site.url)
        vp.play_from_direct_link(surl)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')
        return

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
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'open-popup"\s*href="([^"]+)"\s*title="([^"]+)".*?original="([^"]+)"(.*?)time">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(listhtml)

    for videopage, name, img, hd, duration in match:
        name = utils.cleantext(name.strip())
        hd = " [COLOR orange]HD[/COLOR]" if 'hd' in hd else ''
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    nextp = re.compile(r'pager\s*next">.+?block-id="([^"]+)"\s*data-parameters="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)

    if nextp:
        currpg = re.compile(r'class="pagination".+?class="item\sactive">.+?from(?:_albums)?:(\d+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[-1]
        lastpg = re.compile(r'class="item">\s*<a[^>]*from(?:_albums)?:(\d+)">', re.DOTALL | re.IGNORECASE).findall(listhtml)[-1]
        params = nextp[-1][1].replace(':', '=').replace(';', '&')
        if '+' in params:
            params = params.replace('+', '={0}&'.format(params.split('=')[-1].zfill(2)))
        params = params.replace('%20', '+')
        nextpg = '{0}?mode=async&function=get_block&block_id={1}&{2}'.format(url.split('?')[0], nextp[-1][0], params)
        site.add_dir('Next Page... (Currently in Page {} of {})'.format(currpg, lastpg), nextpg, 'List', site.img_next)

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
    srcs = re.findall(r"video(?:_alt)?_url\d?:\s*'([^']+).+?video_(?:alt_)?url\d?_text:\s*'([^']+)", html)
    if srcs:
        vp.progress.update(50, "[CR]Video found[CR]")
        srcs = {m[1]: m[0] for m in srcs}
        surl = utils.prefquality(srcs, sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
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

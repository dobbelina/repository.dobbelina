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
import time
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('rule34video', '[COLOR hotpink]Rule34 Video[/COLOR]', 'https://rule34video.com/', 'rule34video.png', 'rule34video')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cats', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'TagMenu', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'open-popup"\s*href="([^"]+)".*?original="([^"]+)".+?alt="([^"]+)"(.*?)time">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(listhtml)

    for videopage, img, name, hd, duration in match:
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
def TagMenu(url):
    taghtml = utils.getHtml(url, site.url)
    items = re.compile(r'data-block-id="list_tags_tags_list"\s*data-parameters="section:([^"]+)">([^<]+)', re.IGNORECASE | re.DOTALL).findall(taghtml)
    for tagpage, name in items:
        tagurl = '{0}?mode=async&function=get_block&block_id=list_tags_tags_list&section={1}&from=1&_={2}'.format(
            url,
            tagpage,
            int(time.time() * 1000)
        )
        site.add_dir(name, tagurl, 'Tag', page=1)
    utils.eod()


@site.register()
def Tag(url, page=1):
    taghtml = utils.getHtml(url, site.url)
    items = re.compile(r'item">\s+<a href="([^"]+)">\s+([^<]+)\s+<span>.+?</svg>([^<]+)<', re.IGNORECASE | re.DOTALL).findall(taghtml)
    for tagpage, name, videos in items:
        name = '{} [COLOR orange]{}[/COLOR]'.format(name.strip(), videos.strip())
        site.add_dir(name, tagpage, 'List')
    if len(items) == 120:
        nextpg = url.replace('from={}'.format(page), 'from={}'.format(page + 1))
        site.add_dir('Next Page', nextpg, 'Tag', site.img_next, page=page + 1)
    utils.eod()


@site.register()
def Cats(url):
    if '?' not in url:
        url = '{0}?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_={1}'.format(
            url,
            int(time.time() * 1000)
        )
    cathtml = utils.getHtml(url, site.url)
    items = re.compile(r'item">\s*<a\s*class="th"\s*href="([^"]+).+?<img.+?src="([^"]+).+?title">([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for catpage, img, name in items:
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'List', img)

    nextp = re.compile(r'class="item\s*pager\s*next">.+?data-parameters=.+?from:(\d+)', re.DOTALL | re.IGNORECASE).search(cathtml)

    if nextp:
        currpg = re.compile(r'class="item\s*active">.+?data-parameters=.+?from:0?(\d+)', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        lastpg = re.compile(r'class="item">.+?data-parameters=.+?from:0?(\d+)">\s*Last', re.DOTALL | re.IGNORECASE).findall(cathtml)[-1]
        if '&from=' in url:
            nextpg = re.sub(r'&from=\d+', '', url)
        nextpg = re.sub(r'&_=\d+', '&from={0}&_={1}'.format(nextp.group(1), int(time.time() * 1000)), url)
        site.add_dir('Next Page... (Currently in Page {} of {})'.format(currpg, lastpg), nextpg, 'Cats', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, site.url)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)

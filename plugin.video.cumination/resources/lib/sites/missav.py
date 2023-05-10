'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
from resources.lib import utils, jsunpack
from resources.lib.adultsite import AdultSite

site = AdultSite('missav', '[COLOR hotpink]Miss AV[/COLOR]', 'https://missav.com/', 'missav.png', 'missav')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Actress List[/COLOR]', site.url + 'en/actresses', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Amateur[/COLOR]', 'Amateur', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', 'Uncensored', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Chinese AV[/COLOR]', 'Madou', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'en/search/', 'Search', site.img_search)
    List(site.url + 'en/new?page=1')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)

    match = re.compile(r'class="thumbnail.+?<img.+?data-src="([^"]+)(.+?)bottom-1\sright.+?>([^<]+).+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)
    for img, unc, duration, videopage, name in match:
        name = utils.cleantext(name)
        info = re.compile(r'bottom-1 left.+?>([^<]+)', re.DOTALL | re.IGNORECASE).search(unc)
        if info:
            name += ' [COLOR yellow]{0}[/COLOR]'.format(info.group(1).strip())
        duration = utils.cleantext(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, noDownload=True, fanart=img)
    match = re.compile(r'aria-label="Go to page \d+">\s*(\d+)\s*</a>\s*<a href="([^"]+page=(\d+))"\s+rel="next"', re.DOTALL | re.IGNORECASE).findall(html)
    if match:
        lp, npurl, np = match[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}/{1}'.format(np, lp), npurl, 'List', site.img_next)
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<li>\s*<div.+?img\s*src="([^"]+).+?href="([^"]+).+?truncate">([^<]+).+?nord10">([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for img, caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]({0})[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', img)

    match = re.compile(r'aria-label="Go to page \d+">\s*(\d+)\s*</a>\s*<a href="([^"]+page=(\d+))"\s+rel="next"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if match:
        lp, npurl, np = match[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}/{1}'.format(np, lp), npurl, 'Models', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    html = utils.getHtml(site.url + 'en/')
    section = re.compile(r'''(<span x-cloak x-show="showCollapse === '{0}'.+?</span>)'''.format(url), re.IGNORECASE | re.DOTALL).findall(html)[0]
    match = re.compile(r'href="([^"]+)[^>]+>([^<]+)', re.IGNORECASE | re.DOTALL).findall(section)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url + keyword.replace(' ', '%2B')
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    video_page = utils.getHtml(url, site.url)

    packed = re.compile(r'(eval\(function\(p,a,c,k,e,d\)[^\n]+)', re.DOTALL | re.IGNORECASE).search(video_page)
    if packed:
        packed = jsunpack.unpack(packed.group(1)).replace('\\', '')
        source = re.compile(r"source\s*=\s*'([^']+)", re.DOTALL | re.IGNORECASE).search(packed)
        if source:
            vp.play_from_direct_link('{0}|Referer={1}'.format(source.group(1), site.url))
        else:
            vp.progress.close()
            utils.notify('Oh Oh', 'No Videos found')
            return
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')
        return

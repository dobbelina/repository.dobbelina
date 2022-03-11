"""
    Cumination Site Plugin
    Copyright (C) 2018 Team Cumination

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
from resources.lib.adultsite import AdultSite

site = AdultSite('lpv', '[COLOR hotpink]Lesbian PornVideos[/COLOR]', 'https://www.lesbianpornvideos.com/', 'lpv.png', 'lpv')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/video/', 'Search', site.img_search)
    List(site.url + 'videos/lesbian/all-recent.html')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="item".+?src="([^"]+)[^>]+>(.*?)<span\s*class="time">([\d:]+).+?href=".+?-([^.-]+)\.html[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, quality, duration, videopage, name in match:
        name = utils.cleantext(name)
        if 'HD' in quality:
            quality = 'HD'
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=quality)

    np = re.compile(r'class="pagination.+?href="([^"]+)"\s*class="next"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        currpg = re.compile(r'class="pagination.+?class="active">(\d+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        lastpg = re.compile(r'class="pagination.+?class="total_pages">(\d+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        pgtxt = '(Currently in Page {0} of {1})'.format(currpg, lastpg)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Pornstars(url):
    cathtml = utils.getHtml(url, site.url)
    items = re.compile(r'class="item".+?src="([^"]+).+?href="([^"]+).+?>([^<]+).+?videos"[^\d]+([\d]+)', re.DOTALL).findall(cathtml.split('<!-- alphabetical -->')[-1])
    for img, catpage, name, count in items:
        name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    items = re.compile(r'class="item\s*video.+?src="([^"]+).+?href="([^"]+).+?>([^<]+).+?<h2>(\d+)', re.DOTALL).findall(cathtml)
    for img, catpage, name, count in items:
        name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Channels(url):
    cathtml = utils.getHtml(url, site.url)
    items = re.compile(r'class="item".+?src="([^"]+).+?href="([^"]+).+?>([^<]+).+?videos[^\d]+([\d]+)', re.DOTALL).findall(cathtml)
    for img, catpage, name, count in items:
        name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
        site.add_dir(name, catpage + 'videos/', 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml('{0}embed/{1}'.format(site.url, url), site.url)
    sources = re.compile(r'file:\s*"([^"]+)",\s*label:\s*"([^"\s]+)', re.DOTALL | re.IGNORECASE).findall(videopage)

    if sources:
        sources = {qual: surl for surl, qual in sources}
        videolink = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x[:-1]), reverse=True)
        vp.play_from_direct_link(videolink)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
    return None

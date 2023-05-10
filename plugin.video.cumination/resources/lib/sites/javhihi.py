'''
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
'''

import re
import xbmcplugin
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('jav789', '[COLOR hotpink]JAV 789[/COLOR]', 'https://jav789.com/', 'jav789.png', 'jav789')
site1 = AdultSite('javbuz', '[COLOR hotpink]JAV Buz[/COLOR]', 'https://javbuz.com/', 'javbuz.png', 'javbuz')
site2 = AdultSite('javhihi', '[COLOR hotpink]JAV HiHi[/COLOR]', 'https://javkiki.com/', 'javhihi.png', 'javhihi')
site3 = AdultSite('letfap', '[COLOR hotpink]Let FAP[/COLOR]', 'https://letfap.com/', 'letfap.png', 'letfap')


def getBaselink(url):
    if 'jav789.com' in url:
        siteurl = 'https://heyzo.jav789.com/'
    elif 'javbuz.com' in url:
        siteurl = 'https://www1.javbuz.com/'
    elif 'javkiki.com' in url:
        siteurl = 'https://javkiki.com/'
    elif 'letfap.com' in url:
        siteurl = 'https://xart.letfap.com/'
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'movie', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + 'pornstar', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'movie?q=', 'Search', site.img_search)
    List(siteurl + 'movie')
    utils.eod()


@site.register()
def List(url):
    siteurl = getBaselink(url)
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile(r'video-item".+?href="([^"]+)"\s*title="([^"]+).+?src="([^"]+).+?duration">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, name2 in match:
        name = utils.cleantext(name)
        if not img.startswith('http'):
            img = 'http:' + img
        videopage = siteurl + videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=name2)

    pgurl = None
    pagination = re.search(r'a\s*href="([^"]+)[^>]+>View\s*more', listhtml, re.DOTALL)
    if pagination:
        pgurl = siteurl + pagination.group(1)
        site.add_dir('Next Page', pgurl, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    videopage = utils.getHtml(url, '')
    videopage = re.compile(r'player-wrapper(.+?)container', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    eurl = re.compile(r'<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).search(videopage)
    if eurl:
        vp.play_from_link_to_resolve(eurl.group(1))
    else:
        sources = re.compile(r'"file":\s*"([^"]+).+?"label":\s"([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
        if sources:
            sources = {key: value for value, key in sources}
            videourl = utils.prefquality(sources, reverse=True)
            vp.play_from_direct_link(videourl)


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'col-sm-4"><a\s*href="([^"]+).+?>([^<]+)', re.DOTALL).findall(cathtml)
    for catpage, name in match:
        catpage = siteurl + catpage
        site.add_dir(name, catpage, 'List', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Pornstars(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'class="pornstar-item.+?href="([^"]+).+?src="([^"]+).+?b>(\d*).+?">([^<]+)', re.DOTALL).findall(cathtml)
    for catpage, img, name2, name in match:
        catpage = siteurl + catpage
        name = utils.cleantext(name) + ' [COLOR cyan][{} Videos][/COLOR]'.format(name2)
        if not img.startswith('http'):
            img = 'http:' + img
        site.add_dir(name, catpage, 'List', img)

    pagination = re.search(r'class="next"><a\s*href="([^"]+)', cathtml, re.DOTALL)
    if pagination:
        pgurl = siteurl + pagination.group(1)
        site.add_dir('Next Page', pgurl, 'Pornstars', site.img_next)

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

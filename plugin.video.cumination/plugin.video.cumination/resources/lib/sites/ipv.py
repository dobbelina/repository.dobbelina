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

site = AdultSite('ipv', '[COLOR hotpink]Indian Porn Videos[/COLOR]', 'https://www.indianpornvideos.com/', 'ipv.png', 'ipv')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}categories/'.format(site.url), 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}search/'.format(site.url), 'Search', site.img_search)
    List('{0}recent-page/'.format(site.url))
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<article.+?href="([^"]+).+?(?:src|poster)="([^"]+).+?tion">([^<]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name2, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=name2)

    url = re.compile("""class="pagination".+?href="([^"]+)">Next<""", re.DOTALL | re.IGNORECASE).search(listhtml)
    if url:
        currpg = re.compile(r"""class="pagination".+?class="current">(\d+)""", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        lastpg = re.compile(r"""class="pagination".+?(\d+)/'>Last<""", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        pgtxt = 'Currently in Page ({0} of {1})'.format(currpg, lastpg)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), url.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')
    if 'class="ipe-vplayer"' in videopage:
        videolink = re.compile(r'ipe-vplayer".+?data-url="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        vp.play_from_site_link(videolink)
    elif 'source src=' in videopage:
        videolink = re.compile(r'source\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        vp.play_from_direct_link(videolink)
    elif 'type="video/mp4"' in videopage:
        videolink = re.compile(r'type="video/mp4"\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        vp.play_from_direct_link(videolink)
    elif 'class="wps-player"' in videopage:
        videodiv = re.compile(r'wps-player"(.+?)</div', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        videolink = re.compile(r'<iframe\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videodiv)[0]
        vp.play_from_link_to_resolve(videolink)
    elif 'class="video-player"' in videopage:
        videodiv = re.compile(r'video-player"(.+?)</div', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        if 'itemprop="contentURL"' in videodiv:
            videolink = re.compile(r'itemprop="contentURL"\s*content="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videodiv)[0]
            vp.play_from_direct_link(videolink)
        else:
            videolink = re.compile(r'<iframe\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videodiv)[0]
            vp.play_from_link_to_resolve(videolink)
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
        return None


@site.register()
def Categories(url):
    for pg in range(1, 4):
        if pg > 1:
            purl = url + 'page/{0}/'.format(pg)
        else:
            purl = url
        cathtml = utils.getHtml(purl, '')
        match = re.compile(r'<article.+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL).findall(cathtml)
        for catpage, img, name in match:
            name = utils.cleantext(name)
            site.add_dir(name, catpage, 'List', img)

    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
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

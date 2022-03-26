"""
    Cumination
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
"""

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hentaihavenc', '[COLOR hotpink]Hentaihaven Co[/COLOR]', 'https://hentaihaven.co/', 'https://hentaihaven.co/wp-content/uploads/2021/09/hh1.png', 'hentaihavenco')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat, section='Genre')
    site.add_dir('[COLOR hotpink]Year[/COLOR]', site.url, 'Categories', site.img_cat, section='Years')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    if url == site.url:
        listhtml = listhtml.split('id="wdgt_home_post')[1]
    match = re.compile(r'<article.+?"title[^>]+>([^<]+).+?src="([^"]+).+?href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, img, videopage in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    page = re.compile(r'class="pagination.+?href="([^"]+)[^>]+>\s*<span\s*class="dn[^\d]+(\d+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if page:
        site.add_dir('[COLOR hotpink]Next Page[/COLOR] ({0})'.format(page.group(2)), page.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    surl = re.compile(r'class="video.+?src="([^"]*)', re.DOTALL | re.IGNORECASE).findall(videopage)
    if surl:
        if surl[0]:
            vp.play_from_link_to_resolve(surl[0])
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
    return None


@site.register()
def Categories(url, section):
    cathtml = utils.getHtml(url, '')
    if section == 'Genre':
        match = re.compile(r'menu-item-object-genre.+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    else:
        match = re.compile(r'menu-item-object-dtyear.+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
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

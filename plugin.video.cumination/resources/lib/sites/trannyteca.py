'''
    Cumination
    Copyright (C) 2022 Team Cumination

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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("trannyteca", "[COLOR hotpink]Trannyteca[/COLOR]", "https://www.trannyteca.com/", "trannyteca.png", 'trannyteca')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    items = re.compile(r'<article.+?src="([^"]+).+?href="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, vurl, name in items:
        name = utils.cleantext(name)
        site.add_download_link(name, vurl, 'Playvid', img, name)
    nextp = re.search(r'class="next\s*page-numbers"\s*href="([^"]+)', listhtml, re.DOTALL)
    if nextp:
        nextp = nextp.group(1)
        curr_pg = re.findall(r'class="page-numbers current"[^\d]+(\d+)', listhtml)[0]
        last_pg = re.findall(r'class="page-numbers"[^\d]+(\d+)', listhtml)[-1]
        site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(curr_pg, last_pg), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url)
    links = re.findall(r"px_repros\[.+?=\s*'([^']+)", html)
    if not links:
        utils.notify('Oh oh', 'No playable video found')
        vp.progress.close()
        return
    pattern = r'''<iframe.+?src=['"]([^'"]+)'''
    links = [
        re.findall(pattern, utils._bdecode(x), re.DOTALL | re.IGNORECASE)[0]
        for x in links
    ]
    vp.play_from_link_list(links)


@site.register()
def Categories(url):
    cathtml = utils._getHtml(url, site.url)
    cats = re.compile(r'id="menu-item-[467]\d\d?".+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in cats:
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

# -*- coding: utf-8 -*-
"""
    Cumination
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 Fr33m1nd
    Copyright (C) 2020 Team Cumination

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

site = AdultSite('pelisxporno', '[COLOR hotpink]PelisxPorno[/COLOR]', "https://www.pelisxporno.net/", "pelisxporno.png",
                 'pelisxporno')

progress = utils.progress


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pelicula En Español[/COLOR]', site.url + 'pelicula-xxx-espanol/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Incesto[/COLOR]', site.url + 'incesto-online/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Madres[/COLOR]', site.url + 'tag/madres/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Parodia[/COLOR]', site.url + 'parodia-xxx/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Brazzers En Español[/COLOR]', site.url + 'brazzers-en-espanol-gratis/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Videos Españoles[/COLOR]', site.url + 'videos-espanoles/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?order=date')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'class="post">.*?src="([^"]+).*?href="([^"]+)[^>]+>([^<]+).+?tion"[^\d]+([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, videopage, name, duration in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    nextp = re.compile(r'<a\s*class="nextpostslink"\s*rel="next"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'List', site.img_next)

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
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<li\s*class="cat-item.+?href="([^"]+)[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=r'''(?i)<iframe.+?src=['"]([^'"]+)''')
    vp.play_from_site_link(url, site.url)

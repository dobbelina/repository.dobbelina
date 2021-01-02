'''
    Cumination
    Copyright (C) 2015 Whitecream

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

site = AdultSite('k18', '[COLOR hotpink]K18[/COLOR]', 'https://k18.co/', 'k18.png', 'k18')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Porn Stars[/COLOR]', site.url + 'actors/', 'Cat2', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+).+?data-src="([^"]+).+?duration">([^<]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, duration, name in match:
        name = utils.cleantext(name)
        name = name + " [COLOR deeppink]" + duration + "[/COLOR]"
        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile('href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page...', np.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def CList(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile(r'''class='pagination-nav'><a\s*href="([^"]+)''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page...', np.group(1), 'CList', site.img_next)

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
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name in match:
        site.add_dir(name.strip(), catpage, 'CList', img)

    np = re.compile(r'''class='pagination-nav'><a\s*href="([^"]+)''', re.DOTALL | re.IGNORECASE).search(cathtml)
    if np:
        site.add_dir('Next Page...', np.group(1), 'Cat', site.img_next)

    utils.eod()


@site.register()
def Cat2(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name in match:
        site.add_dir(name.strip(), catpage, 'List', img)

    np = re.compile(r'''class='pagination-nav'><a\s*href="([^"]+)''', re.DOTALL | re.IGNORECASE).search(cathtml)
    if np:
        site.add_dir('Next Page...', np.group(1), 'Cat', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, r'itemprop="embedURL"\s*content="([^"]+)')
    vp.play_from_site_link(url, site.url)

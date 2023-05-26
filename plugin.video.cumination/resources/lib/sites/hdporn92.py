'''
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
'''

import re
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hdporn92', '[COLOR hotpink]Hdporn92[/COLOR]', 'https://hdporn92.com/', 'hdporn92.png', 'hdporn92')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', site.url + 'actors/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?(?:poster|data-src)="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, img in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('hdporn92.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    np = re.compile(r'class="pagination".+?class="current">\d+</a></li><li><a\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)


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
    listhtml = utils.getHtml(url)
    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?(?:poster|src)="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip())
        site.add_dir(name, catpage + '?filter=latest', 'List', img)


    np = re.compile(r'class="pagination".+?class="current">\d+</a></li><li><a\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'Categories', site.img_next)

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('com/(tag/[^"]+)".*?aria-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name.strip())
        site.add_dir(name, site.url + tagpage + '?filter=latest', 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'(category/[^"]+)"\s*?class="label"\s*?title="([^"]+)"', ''),
        ("Model", r'(actor/[^"]+)"\s*?title="([^"]+)"', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'hdporn92.List', lookup_list)
    lookupinfo.getinfo()
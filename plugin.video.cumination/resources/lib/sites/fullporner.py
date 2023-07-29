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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('fullporner', '[COLOR hotpink]Fullporner[/COLOR]', 'https://fullporner.org/', 'https://fullporner.org/wp-content/uploads/2023/04/logo-1.png', 'fullporner')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'actors/', 'Actors', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Actors', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '1b/latest-videos/page/1/?filter=latest')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?(?:poster|data-src)="([^"]+)"[^>]+>.*?</i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)

        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

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
        site.search_dir(searchUrl, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile('<article.+?href="([^&]+)&.+?src="([^"]+)"[^>]+>.*?cat-title">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip())
        site.add_dir(name, catpage + '&filter=latest', 'List', img)
    utils.eod()


@site.register()
def Actors(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?src="([^"]+)"[^>]+>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip())
        site.add_dir(name, catpage, 'List', img)

    np = re.compile(r'class="pagination".+?class="current">\d+</a></li><li><a\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'Categories', site.img_next)

    utils.eod()

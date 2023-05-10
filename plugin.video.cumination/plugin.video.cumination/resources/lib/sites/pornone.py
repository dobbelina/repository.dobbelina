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

site = AdultSite('pornone', '[COLOR hotpink]Porn One[/COLOR]', 'https://pornone.com/', 'pornone.png', 'pornone')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?q=', 'Search', site.img_search)
    List(site.url + 'newest/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a\s*href="([^"]+)"\s*class="\s*relative.+?<span\s*class="text(.*?)>([\d:]+).+?img\s*src="([^"]+).+?"block[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, hd, duration, img, name in match:
        name = utils.cleantext(name)
        hd = 'HD' if 'HD Video' in hd else ''
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)
    np = re.compile(r'<a\s*href="([^"]+)"\s*title="Next\s*Page"').search(listhtml)
    if np:
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np.group(1).split('/')[-2]), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    sources = re.compile(r'''<source\s*src="([^"]+)".+?label="([^"]+)''', re.DOTALL | re.IGNORECASE).findall(html)
    sources = {quality: videourl for videourl, quality in sources}
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x[:-1]), reverse=True)
    if videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        return


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a\s*href="([^"]+)"\s*class="relative[^>]+>\s*<img.*?data-src="([^"]+)[^>]+>\s*<p[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, image, name in match:
        name = utils.cleantext(name)
        if image.startswith('/'):
            image = site.url[:-1] + image
        site.add_dir(name, site.url[:-1] + catpage, 'List', image)
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

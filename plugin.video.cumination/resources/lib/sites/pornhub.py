'''
    Cumination
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 anton40
    Copyright (C) 2015 Team Cumination

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

site = AdultSite('pornhub', '[COLOR hotpink]PornHub[/COLOR]', 'https://www.pornhub.com/', 'pornhub.png', 'pornhub')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'video/search?o=mr&search=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories?o=al', 'Categories', site.img_cat)
    List(site.url + 'video?o=cm')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    main_block = re.compile(r'videos\s*search-video-thumbs">(.*?)<div\s*class="reset">', re.DOTALL).findall(listhtml)[0]
    match = re.compile(r'class="pcVideoListItem.+?data-thumb_url\s*=\s*"([^"]+).+?tion">([^<]+)(.*?)</div.+?href="([^"]+).+?>\s*(.+?)\s*<', re.DOTALL).findall(main_block)
    for img, duration, hd, videopage, name in match:
        if 'HD' in hd:
            hd = " [COLOR orange]HD[/COLOR] "
        else:
            hd = " "
        name = utils.cleantext(name)
        name = name + hd + "[COLOR deeppink]" + duration + "[/COLOR]"
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name)

    np = re.compile(r'<li\s*class="page_next"><a\s*href="([^"]+)"\s*class="orangeButton">Next', re.DOTALL).search(listhtml)
    if np:
        site.add_dir('Next Page', site.url[:-1] + np.group(1).replace('&amp;', '&'), 'List', site.img_next)

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
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div class="category-wrapper.*?<a href="([^"]+)"\s*?alt="([^"]+)"[^>]+>\s*?<img\s+src=".*?"\s+data-thumb_url="([^"]+)"', re.DOTALL).findall(cathtml)
    for catpage, name, img in match:
        site.add_dir(name, site.url[:-1] + catpage + "&o=cm" if '?' in catpage else "?o=cm", 'List', img, '')

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_link_to_resolve(url)

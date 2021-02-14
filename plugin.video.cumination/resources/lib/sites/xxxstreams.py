'''
    Cumination
    Copyright (C) 2016 Whitecream
    Copyright (C) 2016 anton40

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

site = AdultSite('xxxstreams', '[COLOR hotpink]XXX Streams (eu)[/COLOR]', 'https://xxxstreams.eu/', 'xxxstreams.png', 'xxxstreams')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    match = re.compile(r'data-id="\d+"\s*title="([^"]+)"\s*href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for name, videopage, img in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    nextp = re.compile(r"""'pages'>([^<]+).+?link"?\s*rel="next"\s*href="([^"]+)""", re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        site.add_dir('Next Page... (Currently in {0})'.format(nextp.group(1)), nextp.group(2), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<li.+?class=".+?menu-item-object-post_tag.+?"><a href="(.+?)">(.+?)</a></li>').findall(cathtml)
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

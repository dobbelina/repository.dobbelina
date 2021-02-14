'''
    Cumination
    Copyright (C) 2015 Whitecream
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
'''

import re

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('justporn', '[COLOR hotpink]JustPorn[/COLOR]', 'http://justporn.to/', 'justporn.png', 'justporn')

progress = utils.progress


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]HD-Filme[/COLOR]', site.url + 'category/hd-filme/', 'List', '', '')
    site.add_dir('[COLOR hotpink]Deutsche Filme[/COLOR]', site.url + 'category/deutsche-filme/', 'List', '', '')
    List(site.url + 'category/dvdrips-full-movies/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'class="postbox.+?href="([^"]+).+?title="([^"]+).+?Src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, '')

    nextp = re.compile(r"<span\s*class='current'>[0-9]+</span><a\s*href='(.+?)'", re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        site.add_dir('Next Page', nextp, 'List', site.img_next)

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
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)

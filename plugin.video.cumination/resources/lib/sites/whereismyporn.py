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

site = AdultSite('wimp', '[COLOR hotpink]WhereIsMyPorn[/COLOR]', 'https://whereismyporn.com/', '', 'wimp')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Movies[/COLOR]', site.url + 'archives/tag/movie', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile('src="([^"]+)"[^>]+>.*?post-title"><a href="([^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, videopage, name in match:
        name = utils.cleantext(name)

        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile(r'next\s*page-numbers"\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        nextpage = re.search('page/(\d+)', np).group(1)
        site.add_dir('Next Page... ({0})'.format(nextpage), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Tags(url):
    taghtml = utils.getHtml(url, site.url)
    match = re.compile(r'tag-item"><a\s+href="([^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(taghtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = tagpage + '/page/1?filter=latest'
        site.add_dir(name, tagpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)

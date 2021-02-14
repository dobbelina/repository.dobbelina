"""
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
"""

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xxxsorg', '[COLOR hotpink]XXX Streams (org)[/COLOR]', 'https://xxxstreams.org/', 'xxxsorg.png', 'xxxsorg')

progress = utils.progress


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    match = re.compile(r'<div\s*class="entry-content">.*?lazy-src="([^"]+)".*?<a href="([^"]+)"\s*class="more-link">.+?<span\s*class="screen-reader-text">([^"]+)</span>', re.DOTALL | re.IGNORECASE).findall(html)
    for img, videopage, name in match:
        if 'ubiqfile' in name.lower():
            continue
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    nextp = re.compile(r'<a\s*class="next.*?href="(.+?)">', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def ListSearch(url):
    html = utils.getHtml(url, '').replace('\n', '')
    match = re.compile('bookmark">([^<]+)</a></h1>.*?<img src="([^"]+)".*?href="([^"]+)"').findall(html)
    for name, img, videopage in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, '')

    nextp = re.compile('<link rel="next" href="(.+?)" />', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'ListSearch', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    video_page = utils.getHtml(url, '')
    entry_content = re.compile('entry-content">(.*?)</div>', re.DOTALL | re.IGNORECASE).search(video_page).group(1)
    vp.play_from_html(entry_content)


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
        ListSearch(searchUrl)

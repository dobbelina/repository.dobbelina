"""
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
"""

import re
import base64
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('pornhive', '[COLOR hotpink]PornHive[/COLOR]', 'http://www.pornhive.tv/', 'ph.png', 'pornhive')

progress = utils.progress


@site.register(default_mode=True)
def PHMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'en/categories', 'PHCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'en/search?keyword=', 'PHSearch', site.img_search)
    PHList(site.url + 'en/page/')
    utils.eod()


@site.register()
def PHList(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'anel-img">\s+<a href="([^"]+)">\s+<img.*?data-src="([^"]+)".*?alt="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'PHVideo', img, '')

    nextp = re.compile('<a href="([^"]+)"[^>]+>Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'PHList', site.img_next)

    utils.eod()


@site.register()
def PHSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'PHSearch')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        PHList(searchUrl)


@site.register()
def PHCat(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<li><a\s*href="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'PHList', '')
    utils.eod()


@site.register()
def PHVideo(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=r'"video".+?href="([^"]+)')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    if 'extra_urls' in videopage:
        baseurls = re.compile(r"extra_urls\[\d\]='([^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)
        for burl in baseurls:
            videopage = '"video" href="{0}"\n'.format(base64.b64decode(burl.encode('ascii')).decode('ascii')) + videopage
    vp.play_from_html(videopage)

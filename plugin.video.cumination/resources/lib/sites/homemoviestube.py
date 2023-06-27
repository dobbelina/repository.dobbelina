'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('homemoviestube', '[COLOR hotpink]HomeMovies Tube[/COLOR]', 'https://www.homemoviestube.com/', 'https://www.homemoviestube.com/images/logo.png', 'homemoviestube')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'channels/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'most-recent/')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)

    match = re.compile(r'class="vidItem">.+?data-src="([^"]+).+?time">([^<]+).+?href="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)
    for img, duration, videopage, name in match:
        name = utils.cleantext(name)
        if videopage.startswith('//'):
            videopage = 'https:' + videopage
        if img.startswith('//'):
            img = 'https:' + img.replace(' ', '%20')
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    nextp = re.compile(r"class='next'><a\s*href='([^']+)'>Next", re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        np = urllib_parse.urljoin(url, nextp.group(1))
        curr_pg = re.findall(r"class='current'>([^<]+)", html)[0]
        last_pg = re.findall(r"class='pagination.+?href.+?>([^<]+)", html)[0]
        site.add_dir('[COLOR hotpink]Next Page[/COLOR] (Currently in Page {0} of {1})'.format(curr_pg, last_pg), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="category-item\s.+?data-src="([^"]+).+?href="([^"]+).+?>([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    match = list(set(match))
    match.sort(key=lambda x: x[2])
    for img, caturl, name in match:
        name = utils.cleantext(name)
        if caturl.startswith('//'):
            caturl = 'https:' + caturl
        if img.startswith('//'):
            img = 'https:' + img
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url + keyword.replace(' ', '-') + '/page1.html'
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    video_page = utils.getHtml(url, site.url)

    source = re.compile(r'<source.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).search(video_page)
    if source:
        vp.play_from_direct_link(source.group(1) + '|verifypeer=false')
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')
        return

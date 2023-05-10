"""
    Cumination
    Copyright (C) 2023 Whitecream

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

site = AdultSite('vaginanl', '[COLOR hotpink]Vagina.nl[/COLOR] [COLOR orange](Dutch)[/COLOR]', 'https://vagina.nl/', 'https://m5y8c3q4.ssl.hwcdn.net/img/logo-default.png', 'vaginanl')


@site.register(default_mode=True)
def main(url):
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'sexfilms/search?q=', 'Search', site.img_search)
    List(url + 'sexfilms/newest')


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    if "Geen zoekresultaten gevonden" in html or "Nothing found" in html:
        return
    match = re.compile(r'class="card".+?href="([^"]+)" class="thumbnail-link" title="([^"]+)".+?data-src="([^"]+)".+?>\s*([\d:]+)\s*<', re.DOTALL | re.IGNORECASE).findall(html)
    for videourl, name, img, duration in match:
        videourl = videourl if videourl.startswith('http') else site.url[:-1] + videourl
        name = utils.cleantext(name)
        site.add_download_link(name, videourl, 'Playvid', img, name, duration=duration)
    nextp = re.compile(r'>(\d+)<[^"]+class="next"><a href="([^"]+)"\s+rel="next"', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        lp = '/' + nextp.group(1)
        nextp = nextp.group(2)
        np = re.findall(r'\d+', nextp)[-1]
        nextp = nextp if nextp.startswith('http') else site.url + nextp
        site.add_dir('Next Page (' + np + lp + ')', nextp, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_site_link(url)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        utils.kodilog(searchUrl)
        List(searchUrl)


@site.register()
def Categories(url):
    html = utils.getHtml(url, '')
    tags = re.compile(r'class="card">.+?href="([^"]+)".+?data-src="([^"]+)".+?alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for caturl, catimg, catname in tags:
        caturl = caturl if caturl.startswith('http') else site.url + caturl
        site.add_dir(catname, caturl, 'List', catimg)
    utils.eod()

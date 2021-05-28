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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('freepornstreams', '[COLOR hotpink]Free Porn Streams[/COLOR]', 'https://freepornstreams.org/', 'freepornstreams.png', 'freepornstreams')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Popular Paysites[/COLOR]', 'Popular Paysites', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', 'premium on filehosts', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Clips[/COLOR]', '{0}videos/'.format(site.url), 'List', '')
    site.add_dir('[COLOR hotpink]Movies[/COLOR]', '{0}free-full-porn-movies/'.format(site.url), 'List', '')
    site.add_dir('[COLOR hotpink]Femdom[/COLOR]', '{0}femdom/'.format(site.url), 'List', '')
    site.add_dir('[COLOR hotpink]HD[/COLOR]', '{0}tag/high-def-porn-video/'.format(site.url), 'List', '')
    site.add_dir('[COLOR hotpink]Shemale[/COLOR]', '{0}shemale/'.format(site.url), 'List', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}?s='.format(site.url), 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('<article.+?href="([^"]+).+?>([^<]+).+?data-lazy-src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)
    nextp = re.compile('class="sfwppa-pages.+?next".+?href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        site.add_dir('Next Page ({0})'.format(nextp.split('/')[-2]), nextp, 'List', site.img_next)
    else:
        nextp = re.compile(r'<div\s*class="nav-previous".+?href="([^"]+)"\s*><span class="meta-nav">', re.DOTALL | re.IGNORECASE).search(listhtml)
        if nextp:
            nextp = nextp.group(1)
            site.add_dir('Next Page ({0})'.format(nextp.split('/')[-2]), nextp, 'List', site.img_next)
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
def Cat(url):
    listhtml = utils.getHtml(site.url, '')
    listhtml = re.compile(r'{0}(.+?)</aside>'.format(url), re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile(r'href="([^"]+)"\s*class="tag.+?aria-label="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'List', '', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=r'href="([^"]+)"(?:\s*target="_blank")?\s*rel="nofollow', direct_regex=None)
    vp.play_from_site_link(url, url)

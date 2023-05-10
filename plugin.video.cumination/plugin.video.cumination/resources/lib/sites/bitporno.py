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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('bitporno', '[COLOR hotpink]Bitporno[/COLOR]', 'https://www.bitporno.com/', 'https://www.bitporno.com/images/logobt.png', 'bitporno')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?q=', 'Search', site.img_search)
    List(site.url + 'search/all/sort-recent/time-someday/cat-/page-')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    videos = listhtml.split('class="entry')
    videos.pop(0)
    for video in videos:
        hd = 'HD' if '>HD<' in video else ''
        match = re.compile(r'href="([^"]+)"><img src="([^"]+)".+?>([^<]+)</div>', re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            videourl, img, name = match[0]
            name = utils.cleantext(name)
            site.add_download_link(name, site.url[:-1] + videourl, 'Play', img, name, quality=hd)

    if videos:
        match = re.compile(r'href="([^"]+-(\d+))"\s*class="pages">Next<', re.DOTALL | re.IGNORECASE).findall(videos[-1])
        if match:
            npage, np = match[0]
            site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np), site.url[:-1] + npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    cathtml = cathtml.split('>Categories<')[-1].split('class="clear"')[0]
    match = re.compile(r'a href="([^"]+)">([^<]+)</a> -', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url[:-1] + caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=None, direct_regex=r'file:\s*"([^"]+)')
    vp.play_from_site_link(url, site.url)

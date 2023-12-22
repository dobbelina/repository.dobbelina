"""
    Cumination
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
"""

import re

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('cumlouder', '[COLOR hotpink]Cum Louder[/COLOR]', 'https://www.cumlouder.com/', 'cumlouder.jpg', 'cumlouder')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Series[/COLOR]', site.url + 'series/', 'Series', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'girls/', 'Girls', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?q=', 'Search', site.img_search)
    List(site.url + 'porn/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    trim = re.compile(r'class="listado-escenas"(.+?)class="(?:smt-bottom|related)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile(r'class="muestra-escena"\s*href="([^"]+).+?data-src="([^"]+).+?/span>\s*([^<]+).+?minutos\s*sprite"></span>\s*([^<]+)(.*?)</a>', re.DOTALL | re.IGNORECASE).findall(trim)
    for videopage, img, name, duration, hd in match:
        hd = 'HD' if 'hd sprite' in hd else ''
        duration = duration.split(' ')[0] if 'm' in duration else duration.split(' ')[0] + ':00'
        name = utils.cleantext(name)
        videopage = urllib_parse.urljoin(site.url, videopage)
        if img.startswith('//'):
            img = 'https:' + img
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    nextp = re.compile(r'class="btn-pagination"\s*itemprop="name"\s*href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        np = nextp.group(1)
        site.add_dir('Next Page... ({})'.format(np.split('/')[-2]), site.url[:-1] + np, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, site.url)
    match = re.compile(r'''<iframe\s*src=["']([^"']+)''', re.DOTALL | re.IGNORECASE).findall(vpage)
    if match:
        videourl = match[-1]
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_link_to_resolve(videourl)


@site.register()
def Categories(url):
    nextpg = True
    match = []
    while nextpg:
        cathtml = utils.getHtml(url, site.url)
        match += re.compile(r'tag-url.+?href="([^"]+).+?data-src="([^"]+).+?goria">\s*(.*?)\s*<.+?dad">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
        np = re.compile(r'class="btn-pagination"\s*itemprop="name"\s*href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(cathtml)
        if np:
            url = site.url[:-1] + np.group(1)
        else:
            nextpg = False
    match = sorted(match, key=lambda x: x[2])
    for catpage, img, name, videos in match:
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        if img.startswith('//'):
            img = 'https:' + img
        name = name + " [COLOR deeppink]" + videos + " Videos[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Channels(url):
    nextpg = True
    match = []
    while nextpg:
        cathtml = utils.getHtml(url, site.url)
        match += re.compile(r'channel-url.+?href="([^"]+).+?data-src="([^"]+).+?alt="([^"]+).+?videos\s.+?\s([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
        np = re.compile(r'class="btn-pagination"\s*itemprop="name"\s*href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(cathtml)
        if np:
            url = site.url[:-1] + np.group(1)
        else:
            nextpg = False
    match = sorted(match, key=lambda x: x[2])
    for catpage, img, name, videos in match:
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        if img.startswith('//'):
            img = 'https:' + img
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Series(url):
    nextpg = True
    match = []
    while nextpg:
        cathtml = utils.getHtml(url, site.url)
        match += re.compile(r'<div\s*itemprop.+?href="([^"]+).+?data-src="([^"]+).+?name">([^<]+).+?p>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
        np = re.compile(r'class="btn-pagination"\s*itemprop="name"\s*href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(cathtml)
        if np:
            url = site.url[:-1] + np.group(1)
        else:
            nextpg = False
    match = sorted(match, key=lambda x: x[2])
    for catpage, img, name, videos in match:
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        if img.startswith('//'):
            img = 'https:' + img
        name = name.title() + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Girls(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'girl-url.+?href="([^"]+).+?data-src="([^"]+).+?alt="([^"]+).+?videos\s.+?\s([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, videos in match:
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        if img.startswith('//'):
            img = 'https:' + img
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)

    np = re.compile(r'class="btn-pagination"\s*itemprop="name"\s*href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(cathtml)
    if np:
        site.add_dir('Next Page', site.url[:-1] + np.group(1), 'Girls', site.img_next)

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

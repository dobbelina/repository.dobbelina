"""
    Cumination Site Plugin
    Copyright (C) 2018 Team Cumination

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
import string
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('javmoe', '[COLOR hotpink]JAV Moe[/COLOR]', 'https://javmama.me/', 'javmoe.png', 'javmoe')

enames = {'FS': 'FileStar',
          'sm': 'Streamango',
          'openload': 'Openload',
          'r': 'RapidVideo'}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Genres[/COLOR]', site.url + 'genres/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Letters', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s={}&post_type=post', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    items = 0
    while items < 36 and url:
        try:
            listhtml = utils.getHtml(url, '')
        except:
            return None
        match = re.compile(r'class="epshen".+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
        for videopage, img, name in match:
            name = utils.cleantext(name)
            img = urllib_parse.quote(img, safe=':/')
            videopage = urllib_parse.quote(videopage, safe=':/')
            site.add_download_link(name, videopage, 'Playvid', img, name)
            items += 1
        try:
            url = re.compile(r'class="next\s*page-numbers"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        except:
            url = None
    if url:
        site.add_dir('Next Page', url, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl.format(title)
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<li><a\s*href="([^"]+)"\s*>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', site.img_cat)
    utils.eod()


@site.register()
def Letters(url):
    site.add_dir('#', r'\d', 'Pornstars', site.img_cat)
    for name in string.ascii_uppercase:
        site.add_dir(name, name, 'Pornstars', site.img_cat)
    utils.eod()


@site.register()
def Pornstars(url):
    caturl = site.url + 'pornstars/'
    cathtml = utils.getHtml(caturl, '')
    match = re.compile(r'<li><a\s*href="([^"]+)"\s*>({}[^<]+)'.format(url), re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage.strip(), 'List')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')

    eurls = re.compile(r'<li><a\s*href="([^"]+)"\s*>\s*([^<]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    sources = {}
    for eurl, ename in eurls:
        if eurl != '?server=1':
            videopage = utils.getHtml(url + eurl, '')
        embedurl = re.compile('<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        if 'filestar.club' in embedurl:
            embedurl = utils.getVideoLink(embedurl, url)
        if '//' in embedurl:
            sources[enames[ename]] = embedurl
    videourl = utils.selector('Select Hoster', sources)
    if not videourl:
        vp.progress.close()
        return
    if 'motonews' in videourl:
        if videourl.startswith('//'):
            videourl = 'https:' + videourl
        epage = utils.getHtml(videourl, url)
        surl = re.search(r'file":"([^"]+)', epage)
        if surl:
            surl = surl.group(1)
            if surl.startswith('//'):
                surl = 'https:' + surl
            vp.play_from_direct_link(surl + '|Referer={0}'.format(videourl))
        else:
            vp.progress.close()
            return
    else:
        vp.play_from_link_to_resolve(videourl)

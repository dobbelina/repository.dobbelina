# -*- coding: utf-8 -*-
'''
    Cumination
    Copyright (C) 2018 Whitecream, Fr33m1nd, holisticdioxide

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

site = AdultSite('xvideospanish', '[COLOR hotpink]XvideoSpanish[/COLOR]', 'https://www.xn--xvideos-espaol-1nb.com/', 'xvideospanish.png', 'xvideospanish')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', '', '')
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'videos-pornos-por-productora-gratis/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', site.url + 'actors/', 'Categories', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    main = re.compile('<main.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile(r'<article.+?href="([^"]+)" title="([^"]+)"(.*?)duration">([^<]+)', re.DOTALL | re.IGNORECASE).findall(main)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        videopage = videopage.replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        if 'data-src' in img:
            img = re.compile('data-src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(img)[0]
        elif 'poster' in img:
            img = re.compile('poster="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(img)[0]
        img = img.replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = re.compile(r'class="pagination".+?current".+?href="([^"]+).+?>(\d+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        npage = np.group(1).replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        site.add_dir('Next Page (' + np.group(2) + ')', npage, 'List', site.img_next)

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
def Tags(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a\s*href="([^"]+)"\s*class="tag.+?\(([^\)]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, items, name in match:
        name = utils.cleantext(name) + " [COLOR deeppink]{0}[/COLOR]".format(items)
        catpage = catpage.replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        site.add_dir(name, catpage, 'List')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    cathtml = re.compile('<main.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<article.+?href="([^"]+)".+?src="([^"]+)".+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name in match:
        catpage = catpage.replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        img = img.replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        site.add_dir(name, catpage, 'List', img)

    np = re.compile(r'class="pagination".+?current".+?href="([^"]+).+?>(\d+)', re.DOTALL | re.IGNORECASE).search(cathtml)
    if np:
        npage = np.group(1).replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        site.add_dir('Next Page (' + np.group(2) + ')', npage, 'Categories', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    embedurl = re.compile(r'iframe\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    if '?id=' in embedurl:
        vid = re.compile('id=([^&]+)', re.DOTALL | re.IGNORECASE).findall(embedurl)[0]
        embedurl = re.sub('id=([^&]+)', 'ir={}'.format(vid[::-1]), embedurl, 0, re.MULTILINE)
        embedurl = utils.getVideoLink(embedurl, url)
    elif 'xvideos-español' in embedurl:
        embedurl = embedurl.replace('xvideos-español', 'xn--xvideos-espaol-1nb')
        videopage = utils.getHtml(embedurl, site.url)
        r = re.compile(r'source\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).search(videopage)
        if r:
            vp.play_from_direct_link(utils.cleantext(r.group(1)))
        else:
            embedurl = re.compile(r'iframe\s*src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
            vp.play_from_link_to_resolve(embedurl)
    else:
        vp.play_from_link_to_resolve(embedurl)

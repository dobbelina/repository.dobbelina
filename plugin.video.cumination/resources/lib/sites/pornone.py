'''
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
'''

import re

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('vporn', '[COLOR hotpink]Porn One[/COLOR]', 'https://pornone.com/', 'pornone.png', 'pornone')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?q=', 'Search', site.img_search)
    List(site.url + 'newest/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'class="video">.+?href="([^"]+)".+?"time">([^<]+).+?class="hd([^<]+)</span>.+?src="([^"]+)"\s*alt="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, duration, hd, img, name in match:
        name = utils.cleantext(name)
        hd = 'HD' if hd.find('is-hd') > 0 else ''
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)
    np = re.compile('<link rel="next" href="(.+?)">').search(listhtml)
    if np:
        site.add_dir('Next Page', np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    sources = re.compile(r'''<source\s*src="([^"]+)".+?label="([^"]+)''', re.DOTALL | re.IGNORECASE).findall(html)
    sources = {quality: videourl for videourl, quality in sources}
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x[:-1]), reverse=True)
    if videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        return


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    cat_block = re.compile(r'class="heading-1">All(.+?)</div>\s*</div>\s*</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile(r'<a\s*href="([^"]+)".+?src="([^"]+).+?title">([^<]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cat_block)
    for cat, image, name, videos in match[1:]:
        name = "{0} [COLOR deeppink]{1} Videos[/COLOR]".format(utils.cleantext(name), videos)
        catpage = site.url[:-1] + cat
        site.add_dir(name, catpage, 'List', image)

    np = re.compile(r'class="next\s*".+?href="([^"]+)').search(cathtml)
    if np:
        site.add_dir('Next Page', np.group(1), 'Categories', site.img_next)
    utils.eod()
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '_')
        searchUrl = searchUrl + title
        List(searchUrl)

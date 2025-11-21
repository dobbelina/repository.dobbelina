'''
    Cumination
    Copyright (C) 2025 Team Cumination

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

site = AdultSite('tokyomotion', '[COLOR hotpink]TokyoMotion[/COLOR]', 'https://www.tokyomotion.net/', 'https://cdn.tokyo-motion.net/img/logo.gif', 'tokyomotion')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?search_query={}&search_type=videos', 'Search', site.img_search)
    List(site.url + 'videos?type=public&o=mr&page=1')
    utils.eod()


@site.register()
def List(url):
    utils.kodilog('tokyomotion List: {}'.format(url))
    listhtml = utils.getHtml(url, '')
    if 'No Videos Found' in listhtml:
        utils.notify(msg='Nothing found')
        utils.eod()
        return
    match = re.compile(r'well well-sm[^"]*?">\s*<a href="/([^"]+)".*?src="([^"]+)"\s*title="([^"]+)"(.*?)duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, name, hd, duration in match:
        name = utils.cleantext(name)
        duration = utils.cleantext(duration)
        hd = 'HD' if 'HD' in hd else ''
        videopage = site.url + videopage
        img = img + '|Referer=' + site.url
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    np = re.compile('<li><a href="([^"]+)" class="prevnext', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        npage = np.group(1).replace('&amp;', '&')
        npage_nr = re.compile(r'page=(\d+)').search(npage)
        npage_nr = '({})'.format(npage_nr.group(1)) if npage_nr else ''
        site.add_dir('Next Page {}'.format(npage_nr), npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'source src="([^"]+)"[^"]+title="[^"]+"', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if match:
        vp.play_from_direct_link(match[-1] + '|Referer={}'.format(site.url))


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url.format(keyword.replace(' ', '+')))


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'<div class="col-sm-6.+?<a href="/([^"]+)">.*?src="([^"]+)"\s*title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name in match:
        site.add_dir(name, site.url + catpage + '?type=public&o=mr', 'List', img)
    utils.eod()

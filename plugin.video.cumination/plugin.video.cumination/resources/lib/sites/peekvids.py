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

site = AdultSite('peekvids', '[COLOR hotpink]PeekVids[/COLOR]', 'https://www.peekvids.com/', 'https://www.peekvids.com/img/logo.png', 'peekvids')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'videos?q=', 'Search', site.img_search)
    List(site.url + 'Trending-Porn')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'''class="card\s*(?:video|not_show).+?src="([^"]+).+?>(.+?)info">([^<]+).+?href="([^"]+)">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, hd, duration, video, name in match:
        name = utils.cleantext(name)
        hd = 'HD' if '>HD<' in hd else ''
        site.add_download_link(name, site.url[:-1] + video, 'Play', img, name, duration=duration, quality=hd)

    np = re.compile(r'''class="pagination">.+?class="next"\s*href="([^"]+)''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = site.url[:-1] + np.group(1)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np.split('=')[-1]), np, 'List', site.img_next)

    utils.eod()


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'''li>\s*<a\s*href="([^"]+)">([^<]+)</a>\s*<span>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, vids in match:
        name += ' [COLOR hotpink]{0} Videos[/COLOR]'.format(vids)
        site.add_dir(name, site.url[:-1] + catpage, 'List', '')
    utils.eod()


@site.register()
def Channels(url):
    listhtml = utils.getHtml(url, site.url)
    listhtml = re.compile(r'''popular_channels">(.+?)</main>''', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile(r'''class="card".+?channel">(.+?)href="([^"]+)">([^<]+).+?videos">[^\d]+([\d,]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for imgs, chpage, name, vids in match:
        name += ' [COLOR hotpink]{0} Videos[/COLOR]'.format(vids)
        img = ''
        if "img-responsive" in imgs:
            img = re.findall(r'<img.+?src="([^"]+)', imgs)[0]
        site.add_dir(name, site.url[:-1] + chpage, 'List', img)

    np = re.compile(r'''class="pagination".+?class="next"\s*href="([^=]+=(\d+))''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nextpg = site.url[:-1] + np.group(1)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np.group(2)), nextpg, 'Channels', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    videopage = utils.getHtml(url, site.url)
    sources = re.compile(r'data-hls-src(\d+)="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    if sources:
        sources = {key: value for key, value in sources}
        videourl = utils.prefquality(sources, reverse=True)
        vp.play_from_direct_link(videourl.replace('&amp;', '&'))

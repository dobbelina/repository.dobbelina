"""
    Cumination
    Copyright (C) 2022 Team Cumination

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

site = AdultSite("playvids", "[COLOR hotpink]PlayVids[/COLOR]", "https://www.playvids.com/", "playvids.png", 'playvids')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels?page=1', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars?page=1', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Trending[/COLOR]', site.url + 'Trending-Porn', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'videos?q=', 'Search', site.img_search)
    List(site.url + '?page=1')

    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    listhtml = re.sub(r'(?is)<!-- item-carousel -->.+?<!-- /item-carousel -->', '', listhtml)
    items = re.compile(r'class="card\s.+?<img.+?src="([^"]+).+?info">(.+?)"duration">([^<]+).+?title">([^<]+).+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, info, duration, n1, videopage, n2 in items:
        name = utils.cleantext(n1) or utils.cleantext(n2)
        hd = 'HD' if '>HD<' in info else ''
        videopage = site.url[:-1] + videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, noDownload=True, duration=duration, quality=hd)

    nextp = re.search(r'''<li><a\s*class="next"\s*href="([^"]+)">Next''', listhtml, re.DOTALL)
    if nextp:
        nextp = site.url[:-1] + nextp.group(1)
        site.add_dir('Next Page... ({0})'.format(nextp.split("=")[-1]), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def PList(url):
    listhtml = utils.getHtml(url, site.url)
    listhtml = re.sub(r'(?is)<!-- item-carousel -->.+?<!-- /item-carousel -->', '', listhtml)
    items = re.compile(r'class="card\sthumbs.+?<img.+?src="([^"]+).+?info">(.+?)"duration">([^<]+).+?title">([^<]+).+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, info, duration, n1, videopage, n2 in items:
        name = utils.cleantext(n1) or utils.cleantext(n2)
        hd = 'HD' if '>HD<' in info else ''
        videopage = site.url[:-1] + videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, noDownload=True, duration=duration, quality=hd)

    nextp = re.search(r'''<li><a\s*class="next"\s*href="([^"]+)">Next''', listhtml, re.DOTALL)
    if nextp:
        nextp = site.url[:-1] + nextp.group(1)
        site.add_dir('Next Page... ({0})'.format(nextp.split("=")[-1]), nextp, 'PList', site.img_next)

    utils.eod()


@site.register()
def CList(url, page=1):
    listhtml = utils.getHtml(url + '?page={0}'.format(page), site.url)
    items = re.compile(r'id="row_item.+?src="([^"]+).+?info">(.+?)"duration">([^<]+).+?title">([^<]+).+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, info, duration, n1, videopage, n2 in items:
        name = utils.cleantext(n1) or utils.cleantext(n2)
        hd = 'HD' if '>HD<' in info else ''
        videopage = site.url[:-1] + videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, noDownload=True, duration=duration, quality=hd)

    nextp = re.search(r'''id="channel_show_more".+?</div''', listhtml, re.DOTALL)
    if nextp:
        page = page + 1
        site.add_dir('Next Page... ({0})'.format(page), url, 'CList', site.img_next, page=page)

    utils.eod()


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'''<li>\s*<a\s*href="([^"]+)">\s*(.+?)\s*<''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name in match:
        site.add_dir(name, site.url[:-1] + catpage, 'List', '')
    utils.eod()


@site.register()
def Channels(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="card">.+?channel">.+?src="([^"]+).+?title">.+?href="([^"]+)">([^<]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, chpage, name, vids in match:
        name = utils.cleantext(name)
        name += ' [COLOR hotpink]{0}[/COLOR]'.format(vids)
        site.add_dir(name, site.url[:-1] + chpage, 'CList', img, page=1)

    nextp = re.search(r'''<li><a\s*class="next"\s*href="([^"]+)">Next''', listhtml, re.DOTALL)
    if nextp:
        nextp = site.url[:-1] + nextp.group(1)
        site.add_dir('Next Page... ({0})'.format(nextp.split("=")[-1]), nextp, 'Channels', site.img_next)

    utils.eod()


@site.register()
def Pornstars(url):
    listhtml = utils.getHtml(url, site.url)
    items = re.compile(r'class="overflow(.+?)</li', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for item in items:
        if '<img' in item:
            chpage, img, name = re.compile(r'''href="([^"]+).+?src=['"]([^'"]+)'>"\s*>?\s*(.+?)\s*</a''', re.DOTALL | re.IGNORECASE).findall(item)[0]
        else:
            img = ''
            chpage, name = re.compile(r'''href="([^"]+)"\s*>\s*(.+?)\s*</a''', re.DOTALL | re.IGNORECASE).findall(item)[0]
        name = utils.cleantext(name)
        site.add_dir(name, site.url[:-1] + chpage, 'PList', img)

    nextp = re.search(r'''<li><a\s*class="next"\s*href="([^"]+)">Next''', listhtml, re.DOTALL)
    if nextp:
        nextp = site.url[:-1] + nextp.group(1)
        site.add_dir('Next Page... ({0})'.format(nextp.split("=")[-1]), nextp, 'Pornstars', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    sources = re.compile(r'data-hls-src(\d+)="([^"]+)').findall(videohtml)
    if sources:
        sources = {key: value for key, value in sources}
        vidurl = utils.prefquality(sources, reverse=True)
        vp.play_from_direct_link(vidurl.replace('&amp;', '&'))
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')

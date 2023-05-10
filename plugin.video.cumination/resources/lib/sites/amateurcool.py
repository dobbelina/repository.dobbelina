'''
    Cumination
    Copyright (C) 2015 Whitecream
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

site = AdultSite("amateurcool", "[COLOR hotpink]Amateur Cool[/COLOR]", "https://www.amateurcool.com/", "amateurcool.png", 'amateurcool')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}/channels/'.format(site.url), 'Categories', site.img_cat)
    List('{0}most-recent/'.format(site.url))
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    videos = listhtml.split('item__inner')
    videos.pop(0)
    for video in videos:
        if '>Photos<' in video:
            continue
        match = re.compile(r'href="([^"]+)"\s*title="([^"]+)".+?duration.+?item__stat-label">([\d:]+)<(.+?)img src="([^""]+)"', re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            videopage, name, duration, hd, img = match[0]
            hd = 'HD' if '>HD<' in hd else ''
            name = utils.cleantext(name)
            videopage = 'https:' + videopage if videopage.startswith('//') else videopage
            site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)
    nextp = re.search(r"title='Next' href='([^']+)'", videos[-1], re.DOTALL)
    if nextp:
        site.add_dir('Next Page', url[:url.rfind('/') + 1] + nextp.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url)


@site.register()
def Categories(url):
    cathtml = utils._getHtml(site.url + 'filter/videos', url)
    cats = cathtml.split('citem__link')
    cats.pop(0)
    cats.pop(0)
    for cat in cats:
        match = re.compile('href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cat)
        if match:
            catpage, catimg, name = match[0]
            catpage = 'https:' + catpage if catpage.startswith('//') else catpage
            catimg = 'https:' + catimg if catimg.startswith('//') else catimg
            site.add_dir(name, catpage, 'List', catimg)
    utils.eod()

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

site = AdultSite("amateurcool", "[COLOR hotpink]Amateur Cool[/COLOR]", "https://www.amateurcool.com",
                 "amateurcool.png", 'amateurcool')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}/channels/'.format(site.url), 'Categories', site.img_cat)
    List('{0}/most-recent/'.format(site.url))
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'data-video="([^"]+).+?img\s*src="([^"]+)"\s*alt="(.+?)".+?<span>(.+?)\s*Video</span>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, duration in match:
        name = utils.cleantext(name + ' [COLOR deeppink]' + duration + '[/COLOR]')
        site.add_download_link(name, videopage, 'Playvid', img, '')

    nextp = re.search(r'''class="pagination.+?href='([^']+)'\s*class="next">''', listhtml, re.DOTALL)
    if nextp:
        site.add_dir('Next Page', url[:url.rfind('/') + 1] + nextp.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('class="item nb".+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, catimg, name in match:
        site.add_dir(name, catpage, 'List', catimg)
    utils.eod()

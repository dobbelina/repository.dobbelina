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

site = AdultSite('luxuretv', '[COLOR hotpink]LuxureTV[/COLOR]', 'https://luxuretv.com/', 'https://luxuretv.com/images/logo.png', 'luxuretv')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'channels/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'searchgate/videos/', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''content">.+?href="([^"]+).+?title="([^"]+).+?src="([^"]+).+?time">(?:<b>)?([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, name, img, duration in match:
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'Play', img, name, duration=duration)

    np = re.compile(r'''pagination">.+?href='([^']+)'>Suivante''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = url.split('page')[0] + np.group(1)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np.split('page')[-1].split('.')[0]), np, 'List', site.img_next)

    utils.eod()


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''content-channel">.+?src="([^"]+).+?href='([^']+)'>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, catpage, name in match:
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=None, direct_regex=r'<source\s*src="([^"]+)')
    vp.play_from_site_link(url, url)

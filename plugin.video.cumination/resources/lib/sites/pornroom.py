'''
    Cumination
    Copyright (C) 2018 Whitecream

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

site = AdultSite('pornroom', '[COLOR hotpink]ThePornRoom[/COLOR]', 'https://thepornroom.com/', 'pornroom.jpg', 'pornroom')


@site.register(default_mode=True)
def pornroom_main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'pornroom_cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    pornroom_list(site.url + '?filter=latest')


@site.register()
def pornroom_list(url):
    listhtml = utils.getHtml(url)
    if '0 videos found' in listhtml:
        utils.notify('No videos found', 'No videos found on this page')
        utils.eod()
        return

    match = re.compile(r'data-post-id=".+?(?:poster|data-src)="([^"]+).+?class="duration">([^<]+)<.+?href="([^"]+)"\s*title="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, duration, video, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'pornroom_play', img, name, duration=duration)

    np = re.compile(r'class="page-link current".+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'pornroom_list', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = url + keyword.replace(' ', '+')
        pornroom_list(searchUrl)


@site.register()
def pornroom_cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="thumb" href="([^"]+)" title="([^"]+)".+?data-src="([^"]+)".+?class="video-datas">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img, videos in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip())
        name += ' [COLOR hotpink](' + videos.strip() + ')[/COLOR]'
        site.add_dir(name, catpage + '?filter=latest', 'pornroom_list', img)
    utils.eod()


@site.register()
def pornroom_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=r'<iframe.+?src="([^"]+)"', direct_regex=None)
    vp.play_from_site_link(url)

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

site = AdultSite('pornvibe', '[COLOR hotpink]Pornvibe[/COLOR]', 'https://pornvibe.org/', 'pornvibe.png', 'pornvibe')


@site.register(default_mode=True)
def pornvibe_main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'pornvibe_cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'pornvibe_search', site.img_search)
    pornvibe_list(site.url + 'all-videos/')


@site.register()
def pornvibe_list(url):
    listhtml = utils.getHtml(url, site.url)
    r = re.compile(r'''<section\s*class="content(.+?)<!--tabs-panel-->''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if r:
        listhtml = r.group(1)
    match = re.compile(r'''class="item\s*large.+?img.+?src="([^"]+).+?left">(.+?)<span>(.+?)des">.+?href="([^"]+)">\s*(.*?)\s*<''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, hd, duration, video, name in match:
        hd = '[COLOR orange] HD[/COLOR]' if 'HD' in hd else ''
        d = re.search(r'<span>([\d:]+)</span>', duration)
        duration = d.group(1) if d else ''
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'pornvibe_play', img, name, duration=duration, quality=hd)

    np = re.compile(r'class="pagination".+?current"[^!]+?href="([^"]+).+?>(\d+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page (' + np.group(2) + ')', np.group(1), 'pornvibe_list', site.img_next)

    utils.eod()


@site.register()
def pornvibe_cat(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'''<img src="([^"]+)" alt="([^"]+)">\s+<a href="([^"]+)".*?</h5>\s+<p>([^&]+)&''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, catpage, count in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip()) + " [COLOR deeppink]" + count.strip() + " videos[/COLOR]"
        site.add_dir(name, catpage, 'pornvibe_list', img, 1)
    utils.eod()


@site.register()
def pornvibe_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'pornvibe_search')
    else:
        title = keyword.replace(' ', '+')
        url += title
        pornvibe_list(url)


@site.register()
def pornvibe_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=None, direct_regex=r'''<video.+?<source\s*src="([^"]+)''')
    vp.play_from_site_link(url, site.url)

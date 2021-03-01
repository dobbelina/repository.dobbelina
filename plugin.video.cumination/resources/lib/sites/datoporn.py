'''
    Cumination
    Copyright (C) 2018 holisticdioxide, Team Cumination

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

site = AdultSite('datoporn', '[COLOR hotpink]DatoPorn[/COLOR]', 'https://dato.porn/', 'datoporn.png', 'datoporn')


@site.register(default_mode=True)
def datoporn_main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}categories/'.format(site.url), 'datoporn_cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', 'search', 'datoporn_search', site.img_search)
    datoporn_list('{0}latest-updates/1/'.format(site.url))


@site.register()
def datoporn_list(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''class="item.+?href="([^"]+).+?al="([^"]+)(.+?)le">([^<]+).+?on">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, hd, name, duration in match:
        duration = duration.strip()
        hd = 'HD' if '>HD<' in hd else ''
        name = utils.cleantext(name.strip())
        site.add_download_link(name, video, 'datoporn_play', img, name, duration=duration, quality=hd)

    r = re.compile(r'''class="pagination.+?class="next"><a\s*href="([^"]+)[^\n]+(\d+)">''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if r:
        if 'search' in r.group(1):
            next_page = url.replace(url.split('=')[-1], r.group(2))
        elif r.group(1).startswith('#'):
            next_page = url.replace(url.split('/')[-2], r.group(2))
        else:
            next_page = site.url[:-1] + r.group(1)
        site.add_dir('Next Page (' + r.group(2) + ')', next_page, 'datoporn_list', site.img_next)

    utils.eod()


@site.register()
def datoporn_cat(url):
    listhtml = utils.getHtml(url)
    cats = []
    items = re.compile(r'(<a\s*class="item".+?</a>)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for item in items:
        catpage = re.findall('href="([^"]+)', item)[0] + '1/'
        img = re.findall('src="([^"]+)', item)[0] if 'no-thumb' not in item else ''
        count = re.findall('videos">([^<]+)', item)[0].strip()
        name = re.findall('title">([^<]+)', item)[0].strip()
        cats.append((catpage, img, count, name))

    for catpage, img, count, name in sorted(cats, key=lambda x: x[3].lower()):
        name = utils.cleantext(name) + " [COLOR deeppink]" + count + "[/COLOR]"
        site.add_dir(name, catpage, 'datoporn_list', img, 1)
    utils.eod()


@site.register()
def datoporn_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'datoporn_search')
    else:
        title = keyword.replace(' ', '+')
        url = "{0}/search/{1}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={1}&category_ids=&sort_by=&from_videos=1".format(site.url, title)
        datoporn_list(url)


@site.register()
def datoporn_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    vp.play_from_link_to_resolve(url)

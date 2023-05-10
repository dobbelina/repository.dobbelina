'''
    Cumination
    Copyright (C) 2020 Whitecream

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite("erome", "[COLOR hotpink]Erome[/COLOR]", "https://www.erome.com/", "https://www.erome.com/img/logo-erome-horizontal.png", "erome")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?o=new&q=', 'Search', site.img_search)
    List(site.url + 'explore/new')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'''<div[^<]+id="album-.+?data-src="([^"]+).+?right">(.+?)</div.+?title"\s*href="([^"]+)">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, content, iurl, name in match:
        name = utils.cleantext(name)
        img += '|Referer={0}'.format(site.url)
        pics = False
        vids = False
        if '"album-videos"' in content:
            items = re.findall(r'class="album-videos"[^\d]+(\d+)', content)[0]
            name += '[COLOR hotpink][I] {0} vids[/I][/COLOR]'.format(items)
            vids = True
        if '"album-images"' in content:
            items = re.findall(r'class="album-images"[^\d]+(\d+)', content)[0]
            name += '[COLOR orange][I] {0} pics[/I][/COLOR]'.format(items)
            pics = True
        if pics and vids:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='both')
        elif pics:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='pics')
        elif vids:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='vids')

    np = re.compile(r'class="pagination.+?href="([^"]+)"\s*rel="next">', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nurl = urllib_parse.urljoin(url, np.group(1)).replace('&amp;', '&')
        currpg = re.findall(r'class="pagination.+?"active"[^\d]+(\d+)', listhtml, re.DOTALL)[0]
        lastpg = re.findall(r'class="pagination.+?(\d+)</a></li>\s*<li><a\s*href="[^"]+"\s*rel="next"', listhtml, re.DOTALL)[0]
        site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(currpg, lastpg), nurl, 'List', site.img_next)

    utils.eod()


@site.register()
def List2(url, section):
    if section == 'both':
        site.add_dir('Photos', url, 'List2', '', section='pics')
        site.add_dir('Videos', url, 'List2', '', section='vids')
    else:
        listhtml = utils.getHtml(url, site.url)
        items = listhtml.split('<div class="media-group')
        if len(items) > 1:
            items.pop(0)
            itemcount = 0
            for item in items:
                item = item.split('class="clearfix"')[0]
                if 'class="video"' in item and section == 'vids':
                    itemcount += 1
                    img, surl, hd = re.findall(r'''poster="([^"]+).+?source\s*src="([^"]+).+?label='([^']+)''', item, re.DOTALL)[0]
                    img += '|Referer={0}'.format(site.url)
                    surl += '|Referer={0}'.format(site.url)
                    site.add_download_link('Video {0}'.format(itemcount), surl, 'Playvid', img, quality=hd)
                elif 'class="video"' not in item and section == 'pics':
                    img = re.search(r'class="img-front(?:\s*lasyload)?"\s*(?:data-)?src="([^"]+)', item, re.DOTALL)
                    if img:
                        itemcount += 1
                        img = img.group(1) + '|Referer={0}'.format(site.url)
                        site.add_img_link('Photo {0}'.format(itemcount), img, 'Showpic')

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        url += title
        List(url)


@site.register()
def Showpic(url, name):
    utils.showimage(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(url)

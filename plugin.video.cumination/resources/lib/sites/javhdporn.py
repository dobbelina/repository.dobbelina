'''
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
'''

import re
import base64
import six
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('javhdporn', '[COLOR hotpink]JavHD Porn[/COLOR]', 'https://www2.javhdporn.net/', 'https://img.pornfhd.com/logo.png', 'javhdporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Actress[/COLOR]', site.url + 'pornstars/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List('https://www2.javhdporn.net/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''<article.+?href="([^"]+)"\s*title="([^"]+).+?(?:data-lazy-)?src="(http[^"]+).+?/div>(.+?)duration"[^\d]+([\d:]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, name, img, hd, duration in match:
        name = utils.cleantext(name)
        hd = 'HD' if '>HD<' in hd else ''
        site.add_download_link(name, video, 'Play', img, name, duration=duration, quality=hd)

    match = re.compile(r'''class="pagination".+?href="([^"]+)">Next''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if match:
        npage = match.group(1)
        currpg = re.compile(r'''class="pagination".+?current">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        lastpg = re.compile(r'''class="pagination".+?href=['"].+?([\d]+)/['"]>Last''', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (Currently in Page {0} of {1})'.format(currpg, lastpg), npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<article.+?href="([^"]+).+?lazy-src="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, img, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', img)
    match = re.compile(r'''class="pagination".+?href="([^"]+)">Next''', re.DOTALL | re.IGNORECASE).search(cathtml)
    if match:
        npage = match.group(1)
        currpg = re.compile(r'''class="pagination".+?current">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        lastpg = re.compile(r'''class="pagination".+?href=['"].+?([\d]+)/['"]>Last''', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (Currently in Page {0} of {1})'.format(currpg, lastpg), npage, 'Cat', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    m = re.compile(r'video-id="([^"]+).+?(?:mpu-data|data-mpu)="([^"]+).+?data-ver="([^"]+)', re.DOTALL | re.IGNORECASE).search(videohtml)
    if m:
        pdata = {'sources': dex(m.group(1), m.group(2), m.group(3), True),
                 'ver': 2}
        vp.progress.update(50, "[CR]Loading video page[CR]")
        hdr = utils.base_hdrs
        hdr.update({'Origin': site.url[:-1],
                    'Referer': site.url})
        r = utils.postHtml('https://video.javhdporn.net/api/play/', form_data=pdata, headers=hdr)
        eurl = json.loads(r).get('data')
        eurl = dex(m.group(1), eurl, '2')
        eurl = 'https:' + eurl if eurl.startswith('//') else eurl
        hdr.pop('Origin')
        vp.progress.update(75, "[CR]Loading embed page[CR]")
        r = utils.getHtml(eurl, headers=hdr)
        match = re.compile(r"f8_0x5add\('([^']+)", re.DOTALL | re.IGNORECASE).search(r)
        if match:
            link = dex('cGxheWVyaWQ9cFhI', match.group(1), '2', mtype=0)
            vp.play_from_link_to_resolve(link)
            return
    vp.progress.close()
    utils.notify('Oh oh', 'No video found')
    return


def dex(key, data, dver, use_alt=False, mtype=1):
    part = '_0x583715' if mtype == 0 else '_0x58fe15'
    if dver == '1' and use_alt:
        part = 'QxLUF1bgIAdeQX'

    mid = base64.b64encode(six.b(key + part))[::-1]
    x = 0
    ct = ''
    y = list(range(256))

    for r in range(256):
        x = (x + y[r] + (mid[r % len(mid)] if isinstance(mid[r % len(mid)], int) else ord(mid[r % len(mid)]))) % 256
        y[r], y[x] = y[x], y[r]

    s = 0
    x = 0
    ddata = base64.b64decode(data)
    for r in range(len(ddata)):
        s = (s + 1) % 256
        x = (x + y[s]) % 256
        y[s], y[x] = y[x], y[s]
        ct += chr((ddata[r] if isinstance(ddata[r], int) else ord(ddata[r])) ^ y[(y[s] + y[x]) % 256])
    return six.ensure_str(base64.b64decode(ct))

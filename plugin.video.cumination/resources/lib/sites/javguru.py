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
import base64
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('javguru', '[COLOR hotpink]Jav Guru[/COLOR]', 'https://jav.guru/', 'https://cdn.javsts.com/wp-content/uploads/2018/12/logofinal6.png', 'javguru')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'wp-json/wp/v2/categories/', 'Catjson', site.img_cat)
    site.add_dir('[COLOR hotpink]Actress[/COLOR]', site.url + 'jav-actress-list/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'jav-studio-list/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', site.url + 'category/jav-uncensored/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''class="inside-article".+?href='([^']+)'><img src='([^']+)'.+?<a title="([^"]+)"''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'Play', img, name)

    match = re.compile(r'''class='current'.+?href="([^"]+)">(\d+)<''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        npage, np = match[0]
        lp = re.compile(r''' href="[^"]+page/(\d+)/[^"]*">Last''', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}{1})'.format(np, lp), npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Catjson(url):
    listjson = utils.getHtml(url)
    jdata = json.loads(listjson)
    for cat in jdata:
        name = '{0} ({1})'.format(cat["name"], cat["count"])
        site.add_dir(name, cat["link"], 'List', '')
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="cat-item.+?href="([^"]+)">([^<]+)</a>\s*\((\d+)\)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name, count in match:
        name = '{0} ({1})'.format(utils.cleantext(name), count)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    match = re.compile(r'data-localize="([^"]+)".+?">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(videohtml)
    streams = {}
    if match:
        for m in match:
            (data, stream) = m
            streams[stream] = data
    else:
        return
    vp.progress.update(50, "[CR]Loading video page[CR]")

    streamdata = utils.selector('Select', streams)
    if not streamdata:
        return

    match = re.compile(r'var ' + streamdata + r'.+?"iframe_url":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if match:
        link = base64.b64decode(match[0]).decode('utf-8')
    else:
        return
    vp.progress.update(75, "[CR]Loading video page[CR]")
    streamhtml = utils.getHtml(link, url, error='raise')
    match = re.compile(r'''var OLID = '([^']+)'.+?src="([^']+)''', re.DOTALL | re.IGNORECASE).findall(streamhtml)
    if match:
        (olid, vurl) = match[0]
        olid = olid[::-1]
    else:
        return
    src = vurl + olid
    src = utils.getVideoLink(src, link)
    vp.play_from_link_to_resolve(src)

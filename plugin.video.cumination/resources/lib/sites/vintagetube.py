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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import json

site = AdultSite('vintagetube', '[COLOR hotpink]Vintagetube[/COLOR]', 'https://vintagetube.xxx/', 'https://vintagetube.xxx/images/logo-retina.png', 'vintagetube')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', 'https://api.vintagetube.xxx/api/v1/categories?sort=most-videos&c=500&min_videos=10&offset=0', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', 'https://api.vintagetube.xxx/api/v1/search?sort=latest&size=100&from=0&min=0&max=40&query=', 'Search', site.img_search)
    List('https://api.vintagetube.xxx/api/v1/videos?sort=latest&tf=all-time&c=100&offset=0')
    utils.eod()


@site.register()
def List(url):
    listjson = utils.getHtml(url, site.url)
    jdata = json.loads(listjson)
    if "data" in jdata.keys():
        videos = jdata["data"]
    else:
        videos = jdata["videos"]["data"]
    for video in videos:
        name = utils.cleantext(video["title"])
        videopage = video["video_page"]
        img = video["thumb"]
        duration = int(video["duration"])
        m, s = divmod(duration, 60)
        duration = '{:d}:{:02d}'.format(m, s)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    videocount = jdata["total"]
    vpp = 100
    if 'offset=' in url:
        off = 'offset'
    elif 'from=' in url:
        off = 'from'
    offset = int(re.sub(r'^.+{}=(\d+).*'.format(off), r'\1', url))
    if vpp + offset < videocount:
        np = offset // vpp + 1
        lp = '/' + str(videocount // vpp)
        np_url = re.sub(r'{}=\d+'.format(off), r'{}={}'.format(off, vpp + offset), url)
        site.add_dir('Next Page ({}{})'.format(np, lp), np_url, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    listjson = utils.getHtml(url, site.url)
    jdata = json.loads(listjson)
    cats = jdata["data"]
    for cat in cats:
        count = cat["videos"]
        name = cat["title"] if utils.PY3 else cat["title"].encode('utf8')
        name = utils.cleantext(name) + '[COLOR lightpink] ({})[/COLOR]'.format(count)
        caturl = 'https://api.vintagetube.xxx/api/v1/categories/{}?sort=latest&c=100&offset=0'.format(cat["slug"])
        img = cat["thumb"]
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=None, direct_regex='"mp4":{"link":"([^"]+)"')
    vp.play_from_site_link(url)

'''
    Cumination Site Plugin
    Copyright (C) 2018 Team Cumination

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('wcs', '[COLOR hotpink]Webcam Shows[/COLOR]', 'https://www.webcamshows.org/', 'wcs.png', 'wcs')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Female Webcam Shows[/COLOR]', site.url + 'sex/female/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Couple Webcam Shows[/COLOR]', site.url + 'sex/couple/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Transgender Webcam Shows[/COLOR]', site.url + 'sex/trans/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Bonga Webcam Shows[/COLOR]', site.url + 'sources/bongacams/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Chaturbate Webcam Shows[/COLOR]', site.url + 'sources/chaturbate/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Cam4 Webcam Shows[/COLOR]', site.url + 'sources/cam4/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Camsoda Webcam Shows[/COLOR]', site.url + 'sources/camsoda/', 'List', site.img_cat)
    # site.add_dir('[COLOR hotpink]MyFreeCams Webcam Shows[/COLOR]', site.url + 'sources/myfreecams/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search Model[/COLOR]', 'https://www.webcamshows.org/search/?s=', 'Search', site.img_search)
    # List('https://www.webcamshows.org/')
    utils.eod()


@site.register()
def List(url):
    items = 0
    while items < 40 and url:
        listhtml = utils.getHtml(url, '')
        match = re.compile(r'<article.+?href=([^>]+).+?src=([^\s]+).+?h3>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
        for videopage, img, name in match:
            name = utils.cleantext(name)
            site.add_download_link(name, videopage, 'Playvid', img, name)
            items += 1
        r = re.search(r'next"\s*href=(.+?)>Next', listhtml)
        if r:
            url = site.url[:-1] + r.group(1)
        else:
            url = None
    if url:
        site.add_dir('Next Page', url, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    # vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')
    if '<iframe' in videopage:
        videolink = re.compile(r'''<iframe.+?src=["']?([^'"\s]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        videolink = base64.b64decode(urllib_parse.unquote(videolink.split('embed/?')[-1]))
        videolink = videolink.decode('utf-8') if utils.PY3 else videolink
        vp.play_from_link_to_resolve(videolink)
    else:
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
        return None


@site.register()
def ListSearch(title):
    models = json.loads(utils.getHtml(site.url + 'index.json', ''))
    for model in models:
        name = model.get('title')
        if title in name:
            site.add_dir(name, model.get('permalink'), 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        ListSearch(title)

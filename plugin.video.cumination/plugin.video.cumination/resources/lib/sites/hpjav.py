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
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hpjav', '[COLOR hotpink]HPJav[/COLOR]', 'https://hpjav.tv/', 'https://hpjav.tv/images/HP.png', 'hpjav')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'allcategories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Censored[/COLOR]', site.url + 'category/censored', 'List', site.img_search)
    site.add_dir('[COLOR hotpink]Unensored[/COLOR]', site.url + 'category/uncensored', 'List', site.img_search)
    site.add_dir('[COLOR hotpink]Amateur[/COLOR]', site.url + 'category/amateur-jav', 'List', site.img_search)
    site.add_dir('[COLOR hotpink]Chinese Subtitles[/COLOR]', site.url + 'category/chinese-subtitles', 'List', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)

    List(site.url + 'hot/')


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'class="video-item".+?href="([^"]+).+?original="([^"]+).+?href.+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        img = img + '|Referer=' + url
        name = utils.cleantext(name)
        if videopage.startswith('/'):
            videopage = urllib_parse.urljoin(site.url, videopage)
        site.add_download_link(name, videopage, 'Playvid', img, name)
    try:
        next_page = re.compile(r'''href=['"]?([^'">]+)['"]?><span[^>]+>&raquo;''').findall(listhtml)[0]
        last_page = re.compile(r"href='([^']+).+?>\s*Last").findall(listhtml)
        if last_page:
            last = re.findall(r'\d+', last_page[0])[-1]
        page_nr = re.findall(r'\d+', next_page)[-1]
        if next_page.startswith('/'):
            next_page = urllib_parse.urljoin(site.url, next_page)
        site.add_dir('Next Page (' + page_nr + ('/' + last if last_page else '') + ')', next_page, 'List', site.img_next)
    except:
        pass
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'title="[^"]+"\s*href="([^"]+)">([^<]+).+?(\([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        if catpage.startswith('/'):
            catpage = urllib_parse.urljoin(site.url, catpage)
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)

    eurls = re.compile(r'var\s*vser\s*=[^"]+"([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    eurls = json.loads(base64.b64decode(eurls).decode())
    sources = {}
    for eurl in eurls:
        eurl = hpjav_decode(eurl)
        if vp.resolveurl.HostedMediaFile(eurl):
            sources.update({eurl.split('/')[2]: eurl})
    videourl = utils.selector('Select Hoster', sources)

    vp.play_from_link_to_resolve(videourl)


def hpjav_decode(a1):
    def c(c1, c4, c5):
        c6 = ''
        for i in range(len(c1)):
            k = i % c4
            c6 += chr(ord(c1[i]) ^ ord(c5[k]))
        return c6

    a1 = base64.b64decode(a1).decode()
    a5 = 'f41g(*^opPklaPk6w3*K5q1la&'
    a6 = c(a1, len(a5), a5)
    return a6

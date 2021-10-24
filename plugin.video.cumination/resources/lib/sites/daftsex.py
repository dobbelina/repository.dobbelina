"""
    Cumination
    Copyright (C) 2016 Whitecream, hdgdl
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
"""

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('daftsex', '[COLOR hotpink]DaftSex[/COLOR]', 'https://daftsex.com/', 'daftsex.png', 'daftsex')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'video/', 'Search', site.img_search)
    List('{0}hot'.format(site.url))
    utils.eod()


@site.register()
def List(url, page=0):
    try:
        postRequest = {'page': str(page)}
        response = utils.postHtml(url, form_data=postRequest, headers={}, compression=False)
    except:
        return None
    videos = response.split('class="video-item')
    videos.pop(0)
    for video in videos:
        match = re.compile(r'video([^"]+)".+?thumb="([^"]+)".+?video-time">([^<]+)<.+?video-title.+?">([^<]*)<', re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            videourl, img, length, name = match[0]
            videourl = site.url + 'watch/' + videourl
            name = utils.cleantext(name)
            shortname = re.sub(r'\[[^\]]+\]', '', name)
            shortname = re.sub(r'\([^\)]+\)', '', shortname)
            shortname = re.sub(r'\[[^\]]+$', '', shortname)
            shortname = re.sub(r' - \w+ \d+, \d+.*$', '', shortname)
            shortname = shortname if shortname else name
            site.add_download_link(shortname, videourl, 'Playvid', img, name, duration=length)
    npage = page + 1
    site.add_dir('Next Page (' + str(npage + 1) + ')', url, 'List', site.img_next, npage)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vidsite = utils.getHtml(url, site.url)
    v = re.compile(r'video">.+?src="([^"]+)').search(vidsite)
    if v:
        video = v.group(1)
    else:
        v = re.compile(r'hash:\s*"([^"]+)').findall(vidsite)[0]
        video = 'https://daxab.com/player/{0}'.format(v)
    video = '{0}$${1}'.format(video, url) if 'daxab' in video else video
    vp.play_from_link_to_resolve(video)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    response = utils.getHtml(url, site.url)
    match = re.compile(r'<div\s*class="video-item">.+?href="([^"]+)".+?thumb="([^"]+).+?title">([^<]+)', re.DOTALL | re.IGNORECASE).findall(response)
    for caturl, img, name in sorted(match, key=lambda x: x[2]):
        caturl = site.url[:-1] + caturl
        img = site.url[:-1] + img
        site.add_dir(name, caturl, 'List', img, 0)
    utils.eod()

'''
    Cumination
    Copyright (C) 2023 Team Cumination

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
import json
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('americass', '[COLOR hotpink]Americass[/COLOR]', 'https://americass.net/', '', 'americass')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'actor/', 'ActorABC', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tag/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'video/search/', 'Search', site.img_search)
    List(site.url + 'video?page=1')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'wrapper">\s<a href="/([^"]+)".*?data-src="([^"]+)".*?duration-overlay">([^<]+)<.*?mb-0">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, duration, name in match:
        name = utils.cleantext(name)
        img = 'https:' + img if img.startswith('//') else img
        videopage = site.url + videopage

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('americass.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

    nextp = re.compile(r'rel="next"\s*href="/([^"]+)">', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        np = site.url + np
        site.add_dir('Next Page...', np, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    url = url + '/resolve'
    videopage = utils.getHtml(url, site.url)

    videourl = re.compile(r"src=\\u0022([^ ]+)\\u0022", re.DOTALL | re.IGNORECASE).findall(videopage)[0]

    videourl = videourl.replace('\/', '/')
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(videourl)


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
def Tags(url):
    listhtml = utils.getHtml(url)
    tags = re.compile('/(tag[^"]+)"[^>]+>([^<]+)<[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, tag, videos in tags:
        tag = utils.cleantext(tag.strip())
        tag = '{} - Videos {}'.format(tag, videos)
        site.add_dir(tag, site.url + tagpage, 'List', '')

    utils.eod()


@site.register()
def ActorABC(url):
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for letter in letters:
        actorpage = url + '?l=' + letter.lower()
        site.add_dir(letter, actorpage, 'Actor', '')
    utils.eod()


@site.register()
def Actor(url):
    listhtml = utils.getHtml(url)
    actors = re.compile('a href="/(actor/[^"]+)".*?src="([^"]+)".*?label">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for actorpage, img, name in actors:
        name = utils.cleantext(name.strip())
        img = site.url + img
        site.add_dir(name, site.url + actorpage, 'List', img)
        
    nextp = re.compile(r'rel="next"\s*href="/([^"]+)">', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        np = np.replace('&amp;', '&')
        np = site.url + np
        site.add_dir('Next Page...', np, 'Actor', site.img_next)
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actor", '/(actor/[^"]+)".*?name">([^<]+)<', ''),
        ("Tag", '/(tag/[^"]+)".*?badge">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'americass.List', lookup_list)
    lookupinfo.getinfo()
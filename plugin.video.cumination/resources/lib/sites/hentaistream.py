"""
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
"""

import re
import xbmc
import xbmcvfs
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("hentaistream", "[COLOR hotpink]HentaiStream[/COLOR]", 'https://hstream.moe/', "https://hstream.moe/images/hs_banner.png", "hentaistream")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url, 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?s=', 'Search', site.img_search)
    List(site.url + 'hentai/search?order=latest&page=1', False)


@site.register()
def List(url, episodes=True):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile('<article.*?href="/([^"]+)".*?typez[^>]+>([^<]+)<.*?src="/([^"]+)".*?<h2[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, hd, img, name in match:
        name = utils.cleantext(name)
        hd = " [COLOR orange]{0}[/COLOR]".format(hd.upper())
        videopage = site.url + videopage
        img = site.url + img
        contexturl = (utils.addon_sys
                      + "?mode=" + str('hentaistream.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu = ('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')
        if episodes:
            name = name + hd
            site.add_dir(name, videopage, 'Episodes', img)
        else:
            site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, quality=hd)
    nextregex = 'rel="next"' if episodes else 'nextPage'
    np = re.compile(nextregex, re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        pagelookup = re.search(r"page=(\d+)", url).group(1)
        if pagelookup:
            np = int(pagelookup) + 1
            url = url.replace("page={0}".format(pagelookup), "page={0}".format(np))
            site.add_dir('Next Page ({0})'.format(np), url, 'List', site.img_next)
    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('/(tags[^"]+)" title[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = site.url + tagpage + '?page=1'
        site.add_dir(name, tagpage, 'List', '', name)
    utils.eod()


@site.register()
def Episodes(url):
    listhtml = utils.getHtml(url)

    img = ''
    imgmatch = re.search('<img src="/([^"]+)" class', listhtml, re.IGNORECASE | re.DOTALL)
    if imgmatch:
        img = site.url + imgmatch.group(1)

    match = re.compile(r'data-index="\d+">\s+?<a href="/([^"]+)".*?title">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for seriepage, name in match:
        name = utils.cleantext(name)
        seriepage = site.url + seriepage
        site.add_download_link(name, seriepage, 'Playvid', img, name)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        url = url + title
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    vpage = utils.getHtml(url, site.url)

    videourl = None
    sources = {}
    videos = re.compile("src: '([^']+(?:mpd|mp4|webm))'", re.DOTALL | re.IGNORECASE).findall(vpage)

    for video in videos:
        quali = re.search(r"(\d+)(?:(?:/manifest\.mpd)|(?:p\.mp4)|(?:p\.webm))", video)
        if quali:
            sources.update({quali.group(1): video})
        else:
            sources.update({'00': video})
            
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x), reverse=True)
    if not videourl:
        vp.progress.close()
        return

    if any(x in videourl for x in ['.mp4', '.webm']):
        videourl = videourl + '|User-Agent={0}&Referer={1}'.format(utils.USER_AGENT, site.url)

    sub = re.search("subUrl: '([^']+)'", vpage, re.IGNORECASE | re.DOTALL)
    if videourl:
        if sub:
            subtitle = sub.group(1)
            subtitle = subtitle + '|User-Agent={0}&Referer={1}&Origin={2}'.format(utils.USER_AGENT, site.url, site.url[:-1])
            utils.playvid(videourl, name, subtitle=subtitle)
        else:
            vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')


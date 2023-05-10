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
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('pornez', '[COLOR hotpink]PornEZ[/COLOR]', 'https://pornez.net/', 'pornez.png', 'pornez')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    videos = listhtml.split('data-post-id="')
    videos.pop(0)
    for video in videos:
        match = re.compile(r'data-src="([^"]+)".+?href="([^"]+)"\s*title="([^"]+).+?"duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            img, videourl, name, duration = match[0]
            name = utils.cleantext(name)
            if name == 'Live Cams':
                continue
            cm_related = (utils.addon_sys + "?mode=" + str('pornez.ContextRelated') + "&url=" + urllib_parse.quote_plus(videourl))
            cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]

            site.add_download_link(name, videourl, 'Play', img, name, duration=duration, contextm=cm)

    match = re.compile(r'href="([^"]+page/(\d+)[^"]*)">&raquo;<', re.DOTALL | re.IGNORECASE).findall(videos[-1])
    if match:
        npage, np = match[0]
        matchlp = re.compile(r'"page-link"\s*href="[^"]+">([\d,]+)<', re.DOTALL | re.IGNORECASE).findall(videos[-1])
        lp = ''
        if matchlp:
            lp = '/' + matchlp[-1]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}{1})'.format(np, lp), npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="btn btn-grey" href="([^"]+)"\s*title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url[:-1] + caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def ContextRelated(url):
    contexturl = (utils.addon_sys
                  + "?mode=" + str('pornez.List')
                  + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    videohtml = utils.getHtml(url)
    match = re.compile(r'<iframe[^>]+src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if not match:
        return
    playerurl = match[0]
    playerhtml = utils.getHtml(playerurl, url)
    match = re.compile(r'src="([^"]+)" title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(playerhtml)
    videos = {}
    for m in match:
        videos[m[1]] = m[0]
    videourl = utils.prefquality(videos, sort_by=lambda x: int(x[:-1]), reverse=True)
    if videourl:
        vp.play_from_direct_link(videourl)

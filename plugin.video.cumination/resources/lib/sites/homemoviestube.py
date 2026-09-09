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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('homemoviestube', '[COLOR hotpink]HomeMovies Tube[/COLOR]', 'https://www.homemoviestube.com/', 'https://www.homemoviestube.com/images/logo.png', 'homemoviestube')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'channels/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'most-recent/')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)

    # match = re.compile(r'class="vidItem">.+?data-src="([^"]+).+?time">([^<]+).+?href="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)
    match = re.compile(r'class="media-card video-card".+?href="([^"]+)".+?title="([^"]+).+?src="([^"]+)".+?duration-badge">([^>]+)<', re.DOTALL | re.IGNORECASE).findall(html)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        if videopage.startswith('//'):
            videopage = 'https:' + videopage
        if img.startswith('//'):
            img = 'https:' + img.replace(' ', '%20')
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    re_npurl = r'prev-next-item"(?!.*aria-disabled="true").+?href="([^"]+)'
    re_npnr  = r'prev-next-item"(?!.*aria-disabled="true").+?href=".+page=(\d+)"\srel'
    re_lpnr  = r'prev-next-item"(?!.*aria-disabled="true").+?href=".+page=(\d+)"\stitle'

    utils.next_page(
        site, '{}.List'.format(site.name), html,
        re_npurl, re_npnr, re_lpnr=re_lpnr,
        contextm='{}.GotoPage'.format(site.name)
    )

    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="channel-card".+?href="([^"]+).+?src="([^"]+).+?badge">([^<]+).+?channel-name">([^>]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    match = list(set(match))
    match.sort(key=lambda x: x[2])
    for caturl, img, cnt, name in match:
        name = utils.cleantext(name + ' [COLOR blue][{}][/COLOR]'.format(cnt))
        if caturl.startswith('//'):
            caturl = 'https:' + caturl
        if img.startswith('//'):
            img = 'https:' + img
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url + keyword.replace(' ', '-') + '/page1.html'
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "{}[CR]Loading video page[CR]".format(name))
    video_page = utils.getHtml(url, site.url)

    source = re.compile(r'<source.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).search(video_page)
    if source:
        videourl = urllib_parse.quote(source.group(1))
        videourl = (site.url).rstrip('/') + videourl if videourl.startswith('/') else videourl
        vp.play_from_direct_link(videourl + '|verifypeer=false')
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')
        return

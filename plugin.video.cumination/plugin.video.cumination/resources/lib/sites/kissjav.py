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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('kissjav', '[COLOR hotpink]Kiss JAV[/COLOR]', 'https://kissjav.li/', 'https://kissjav.li/templates/bula/images/logo.png', 'kissjav')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'videos/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR]', site.url + 'playlists/recent/', 'Playlists', site.img_cat)
    site.add_dir('[COLOR hotpink]Movies[/COLOR]', site.url + 'videos/asian-porn-movies/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/video/?s=', 'Search', site.img_search)
    List(site.url + 'videos/')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)

    match = re.compile(r'id="video-(\d+).+?data-src="([^"]+).+?div(.+?)clock"[^\d]+([\d:]+).+?title="[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)
    for video_id, img, quality, duration, name in match:
        name = utils.cleantext(name)
        quality = 'HD' if '>HD<' in quality else ''
        videopage = '{0}{1}/'.format(site.url, video_id)
        site.add_download_link(name, videopage, 'Playvid', site.url[:-1] + img, name, duration=duration, quality=quality)

    nextp = re.compile(r'<a href="([^"]+)"\s*class="pagination-next">', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        np = nextp.group(1)
        if np.startswith('/'):
            np = site.url[:-1] + np
        curr_pg = re.findall(r'class="pagination-link\s*is-current[^>]+>([^<]+)', html)[0]
        last_pg = re.findall(r'class="pagination-link[^>]+>([^<]+)', html)[-1]
        site.add_dir('[COLOR hotpink]Next Page[/COLOR] (Currently in Page {0} of {1})'.format(curr_pg, last_pg), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<li><a\s*href="([^"]+)">([^<]+)<span\s*class="is-pulled-right">([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]({0} videos)[/COLOR]'.format(count)
        site.add_dir(name, site.url[:-1] + caturl, 'List', '')
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div\s*id="model-\d+.+?data-src="([^"]+).+?href="([^"]+)">([^<]+).+?video"[^\d]+(\d+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for img, caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]({0} videos)[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', site.url[:-1] + img)

    nextp = re.compile(r'<a href="([^"]+)"\s*class="pagination-next">', re.DOTALL | re.IGNORECASE).search(cathtml)
    if nextp:
        np = nextp.group(1)
        if np.startswith('/'):
            np = site.url[:-1] + np
        curr_pg = re.findall(r'class="pagination-link\s*is-current[^>]+>([^<]+)', cathtml)[0]
        last_pg = re.findall(r'class="pagination-link[^>]+>([^<]+)', cathtml)[-1]
        site.add_dir('[COLOR hotpink]Next Page[/COLOR] (Currently in Page {0} of {1})'.format(curr_pg, last_pg), np, 'Models', site.img_next)
    utils.eod()


@site.register()
def Playlists(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div\s*id="playlist-\d+.+?data-src="([^"]+).+?href="([^"]+)[^>]+>([^<]+).+?video"[^\d]+(\d+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for img, caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]({0} videos)[/COLOR]'.format(count)
        if caturl.startswith('/'):
            caturl = site.url[:-1] + caturl
        site.add_dir(name, caturl, 'List', site.url[:-1] + img)

    nextp = re.compile(r'<a href="([^"]+)"\s*class="pagination-next">', re.DOTALL | re.IGNORECASE).search(cathtml)
    if nextp:
        np = nextp.group(1)
        if np.startswith('/'):
            np = site.url[:-1] + np
        curr_pg = re.findall(r'class="pagination-link\s*is-current[^>]+>([^<]+)', cathtml)[0]
        last_pg = re.findall(r'class="pagination-link[^>]+>([^<]+)', cathtml)[-1]
        site.add_dir('[COLOR hotpink]Next Page[/COLOR] (Currently in Page {0} of {1})'.format(curr_pg, last_pg), np, 'Playlists', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url + keyword.replace(' ', '+')
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    video_page = utils.getHtml(url, site.url)

    sources = re.compile(r'<source.+?src="([^"]+).+?title="([^"]+)', re.DOTALL | re.IGNORECASE).findall(video_page)
    if sources:
        sources = {qual: surl for surl, qual in sources}
        source = utils.prefquality(sources, sort_by=lambda x: int(x[:-1]), reverse=True)
        if source:
            source = utils.getVideoLink(source)
            vp.play_from_direct_link(source)
        else:
            vp.progress.close()
            return

    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')
        return

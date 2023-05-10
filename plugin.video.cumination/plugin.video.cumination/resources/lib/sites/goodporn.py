"""
    Cumination site scraper
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
"""

import re
import xbmcplugin
import xbmc
from random import randint
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode


site = AdultSite('goodporn', '[COLOR hotpink]Goodporn[/COLOR]', 'https://goodporn.to/', 'goodporn.png', 'goodporn')


@site.register(default_mode=True)
def Main():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    gpsortorder = utils.addon.getSetting('gpsortorder') if utils.addon.getSetting('gpsortorder') else 'last_content_date'
    sortname = list(sort_orders.keys())[list(sort_orders.values()).index(gpsortorder)]

    context = (utils.addon_sys + "?mode=" + str('goodporn.PLContextMenu'))
    contextmenu = [('[COLOR orange]Sort order[/COLOR]', 'RunPlugin(' + context + ')')]

    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR] [COLOR orange]{}[/COLOR]'.format(sortname), site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by={}&from=01'.format(gpsortorder), 'Playlists', site.img_cat, contextm=contextmenu)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '/search/{0}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={0}&category_ids=&sort_by=&from_videos=1', 'Search', site.img_search)

    List(site.url + 'latest-updates/', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    hdr = dict(utils.base_hdrs)
    listhtml = utils.getHtml(url, site.url, headers=hdr)

    if "There is no data in this list." in listhtml.split('class="list-albums"')[0]:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    videos = listhtml.split('class="item ')
    for video in videos:
        match = re.compile(r'^([^"]+)".+?href="([^"]+)".+?title="([^"]+).+?(?:original|"cover"\s*src)="([^"]+)(.+?)class="duration">([\d:]+)', re.DOTALL | re.IGNORECASE).findall(video)
        for private, videopage, name, img, hd, name2 in match:
            hd = 'HD' if '>HD<' in hd else ''
            name = utils.cleantext(name)
            if 'private' in private.lower():
                private = "[COLOR blue] [PV][/COLOR] "
            else:
                private = ""
            name = private + name
            img = 'https:' + img if img.startswith('//') else img
            site.add_download_link(name, videopage, 'Playvid', img, name, duration=name2, quality=hd)

    if re.search(r'<li\s*class="next"><a', listhtml, re.DOTALL | re.IGNORECASE):
        lastp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lastp = '/{}'.format(lastp[0]) if lastp else ''

        page = 1 if not page else page
        npage = page + 1
        if '?' in url:
            nurl = re.sub(r'([&?])from([^=]*)=(\d+)', r'\1from\2={0:02d}', url).format(npage)
        else:
            nurl = url.replace('/{}/'.format(page), '/{}/'.format(npage)) if '/{}/'.format(page) in url else '{}{}/'.format(url, npage)

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, npage)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    vpage = utils.getHtml(url, site.url)

    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(vpage)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
        for surl, qual in items:
            qual = '00' if qual == 'preview' else qual
            surl = kvs_decode(surl, license)
            sources.update({qual: surl})
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'"item"\s*href="([^"]+)"\s*title="([^"]+)">\n\s*<div.+?src="([^"]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan][{}][/COLOR]'.format(name2)
        img = 'https:' + img if img.startswith('//') else img
        site.add_dir(name, catpage, 'List', img, 1)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playlists(url, page=1):
    cathtml = utils.getHtml(url, site.url)
    img = str(randint(1, 4))
    match = re.compile(r'class="item\s*".+?href="([^"]+)"\s*title="([^"]+)".+?class="thumb video' + img + '.+?data-original="([^"]+)".+?class="videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan][{}][/COLOR]'.format(name2)
        img = 'https:' + img if img.startswith('//') else img
        catpage += '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=added2fav_date&from=1'
        site.add_dir(name, catpage, 'ListPL', img, 1)
    if re.search(r'<li\s*class="next"><a', cathtml, re.DOTALL | re.IGNORECASE):
        lastp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(cathtml)
        lastp = '/{}'.format(lastp[0]) if lastp else ''

        page = 1 if not page else page
        npage = page + 1
        nurl = re.sub(r'from([^=]*)=(\d+)', r'from\1={0:02d}', url).format(npage)

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'Playlists', site.img_next, npage)
    utils.eod()


@site.register()
def ListPL(url, page=1):
    listhtml = utils.getHtml(url, site.url)

    if "There is no data in this list." in listhtml.split('class="list-albums"')[0]:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    match = re.compile(r'class="title">([^<]+)<.+?href="([^"]+)".+?data-original="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, videopage, img in match:
        name = utils.cleantext(name)
        img = 'https:' + img if img.startswith('//') else img
        site.add_download_link(name, videopage, 'Playvid', img, name)

    if re.search(r'<li\s*class="next"><a', listhtml, re.DOTALL | re.IGNORECASE):
        lastp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lastp = '/{}'.format(lastp[0]) if lastp else ''

        page = 1 if not page else page
        npage = page + 1
        if '?' in url:
            nurl = re.sub(r'([&?])from([^=]*)=(\d+)', r'\1from\2={}', url).format(npage)
        else:
            nurl = url.replace('/{}/'.format(page), '/{}/'.format(npage)) if '/{}/'.format(page) in url else '{}{}/'.format(url, npage)

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'ListPL', site.img_next, npage)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl.format(title)
        List(searchUrl)


@site.register()
def PLContextMenu():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    order = utils.selector('Select order', sort_orders)
    if order:
        utils.addon.setSetting('gpsortorder', order)
        xbmc.executebuiltin('Container.Refresh')

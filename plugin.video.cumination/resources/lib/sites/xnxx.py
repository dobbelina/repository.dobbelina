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
import json
import xbmcplugin
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xnxx', '[COLOR hotpink]XNXX[/COLOR]', 'https://www.xnxx.com/', 'xnxx.png', 'xnxx')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'todays-selection')
    utils.eod()


@site.register()
def List(url):
    hdr = utils.base_hdrs
    hdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'
    listhtml = utils.getHtml(url, site.url, headers=hdr)
    match = re.compile(r'<div\s*id="video.+?href="([^"]+).+?data-src="([^"]+).+?title.+?>([^<]+).+?(\d+(?:min|sec)).+?(\d+p)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, duration, quality in match:
        name = utils.cleantext(name)
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, duration=duration, quality=quality, noDownload=True)

    np = re.compile(r'class="pagination.+?class="active".+?href="([^"]+)"\s*class="no', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        currpg = re.compile(r'class="pagination.+?class="active".+?>(\d+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        lpg = re.compile(r'class="pagination.+?class="last-page">(\d+)', re.DOTALL | re.IGNORECASE).search(listhtml)
        if lpg:
            lastpg = lpg.group(1)
        else:
            lastpg = re.compile(r'class="pagination\s*".+?>(\d+)</a></li><li><a\shref="[^"]+"\s*class="no-page', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        pgtxt = '(Currently in Page {0} of {1})'.format(currpg, lastpg)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), site.url[:-1] + np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def List2(url, page=0):
    jlist = utils.getHtml(url + '/videos/best/{0}'.format(page), site.url)
    jlist = json.loads(jlist)
    items = jlist.get('videos')
    for item in items:
        name = utils.cleantext(item.get('tf'))
        img = item.get('i')
        vidpage = site.url[:-1] + item.get('u')
        quality = '480p'
        if item.get('hm') == 0:
            quality = '360p'
        elif item.get('h') == 1:
            if item.get('fk') == 1:
                quality = '4K'
            elif item.get('td') == 1:
                quality = '1440p'
            elif item.get('hp') == 1:
                quality = '1080p'
            else:
                quality = '720p'
        site.add_download_link(name, vidpage, 'Playvid', img, name, duration=item.get('d'), quality=quality, noDownload=True)

    page = page + 1
    lastpg = -1 * (-(jlist.get('nb_videos')) // jlist.get('nb_per_page'))
    if page < lastpg:
        pgtxt = '(Currently in Page {0} of {1})'.format(page, lastpg)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), url, 'List2', site.img_next, page=page)

    utils.eod()


@site.register()
def Pornstars(url):
    cathtml = utils.getHtml(url, site.url)
    items = re.compile(r'<div id="profile.+?src="([^"]+).+?href="([^"]+)">([^<]+).+?title="([^"]+)', re.DOTALL).findall(cathtml)
    for img, catpage, name, count in items:
        name = utils.cleantext(name) + ' [COLOR orange][I]{0}[/I][/COLOR]'.format(count)
        site.add_dir(name, site.url[:-1] + catpage, 'List2', img, page=0)

    np = re.compile(r'class="pagination.+?href="([^"]+)"\s*class="no', re.DOTALL | re.IGNORECASE).search(cathtml)
    if np:
        currpg = re.compile(r'class="pagination.+?class="active".+?>(\d+)', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        lastpg = re.compile(r'class="pagination.+?class="last-page">(\d+)', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        pgtxt = '(Currently in Page {0} of {1})'.format(currpg, lastpg)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), site.url[:-1] + np.group(1), 'Pornstars', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, '')

    if 'html5player.setVideoHLS' in videopage:
        videolink = re.compile(r"html5player.setVideoHLS\('([^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        vp.play_from_direct_link(videolink)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
    return None


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    items = re.compile(r'cats.write_thumb_block_list\(([^]]+])', re.DOTALL).findall(cathtml)[0]
    items = json.loads(items)
    for item in items:
        name = item.get('tf') if utils.PY3 else item.get('tf').encode('utf-8')
        img = item.get('i')
        catpage = site.url[:-1] + item.get('u')
        site.add_dir(name, catpage, 'List', img)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
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

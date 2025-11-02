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

site = AdultSite('xnxx', '[COLOR hotpink]XNXX[/COLOR]', 'https://www.xnxx.com/', 'https://static-cdn77.xnxx-cdn.com/v3/img/skins/xnxx/logo-xnxx.png', 'xnxx')


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
    hdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0'
    listhtml = utils.getHtml(url, site.url, headers=hdr)
    soup = utils.parse_html(listhtml)

    video_items = soup.select('.mozaique .thumb-block')
    for item in video_items:
        classes = item.get('class', [])
        if any(cls.startswith('thumb-cat') for cls in classes):
            continue

        link = item.select_one('.thumb a, .thumb-under a')
        if not link:
            continue
        videopage = utils.safe_get_attr(link, 'href')
        if not videopage:
            continue

        title_link = item.select_one('.thumb-under a') or link
        name = utils.cleantext(utils.safe_get_text(title_link))

        img_tag = link.select_one('img')
        img = utils.safe_get_attr(img_tag, 'data-src', ['data-sfwthumb', 'src'])
        if not img:
            continue

        duration = ''
        metadata = item.select_one('.thumb-under .metadata')
        if metadata:
            for piece in metadata.stripped_strings:
                txt = piece.strip()
                if txt.endswith(('min', 'sec', 'hour', 'hours')):
                    duration = txt
                    break

        quality = ''
        quality_tag = item.select_one('.thumb-under .video-hd, .thumb-under .video-uhd, .thumb-under .video-4k, .thumb-under .video-quality, .thumb-under .video-uhd-mark')
        if quality_tag:
            quality = utils.safe_get_text(quality_tag)
        if not quality and metadata:
            for piece in metadata.stripped_strings:
                txt = piece.strip()
                if txt.upper() in ('HD', '4K') or (txt.lower().endswith('p') and any(ch.isdigit() for ch in txt)):
                    quality = txt
                    break

        if not videopage.startswith('http'):
            videopage = site.url[:-1] + videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=quality, noDownload=True)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('a.no-page.next, a.no-page.next-page')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_href = next_href.replace('&amp;', '&')
                page_segment = next_href.rstrip('/').split('/')[-1]
                np = ''
                if page_segment.isdigit():
                    np = str(int(page_segment) + 1)
                pages = [utils.safe_get_text(a) for a in pagination.select('a') if utils.safe_get_text(a).isdigit()]
                lp = '/' + pages[-1] if pages else ''
                if not next_href.startswith('http'):
                    next_href = site.url[:-1] + next_href
                label = 'Next Page'
                if np:
                    label += ' ({}{})'.format(np, lp)
                site.add_dir(label, next_href, 'List', site.img_next)
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
        quality = '4K' if item.get('h') and item.get('fk') else \
                  '1440p' if item.get('h') and item.get('td') else \
                  '1080p' if item.get('h') and item.get('hp') else \
                  '720p' if item.get('h') else \
                  '360p' if item.get('hm') == 0 else '480p'
        site.add_download_link(name, vidpage, 'Playvid', img, name, duration=item.get('d'), quality=quality, noDownload=True)

    page += 1
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
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))

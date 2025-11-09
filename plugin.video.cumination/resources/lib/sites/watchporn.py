'''
    Cumination
    Copyright (C) 2024 Cumination

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
import time

import xbmc
import xbmcgui
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode


site = AdultSite('watchporn', '[COLOR hotpink]WatchPorn[/COLOR]', 'https://watchporn.to/', 'https://watchporn.to/contents/djifbwwmsrbs/theme/logo.png', 'watchporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    if '?' not in url and '/categories/' in url:
        tm = int(time.time() * 1000)
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&_=' + str(tm)
    listhtml = utils.getHtml(url)

    soup = utils.parse_html(listhtml)

    video_items = soup.select('div.item, div.item.item-video, div.video-item')

    items_added = 0
    for item in video_items:
        try:
            link = item.select_one('a[href]')
            if not link:
                continue

            videopage = utils.safe_get_attr(link, 'href')
            if not videopage:
                continue
            videopage = urllib_parse.urljoin(site.url, videopage)

            title = utils.safe_get_attr(link, 'title')
            if not title:
                title_tag = item.select_one('.item__title, .title, a.title')
                title = utils.safe_get_text(title_tag)
            title = utils.cleantext(title)
            if not title:
                continue

            img_tag = item.select_one('img')
            thumb = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'data-lazy', 'src'])
            if thumb:
                thumb = utils.fix_url(thumb, site.url)

            duration_tag = item.select_one('.duration, .item__time, .time, .item__meta .meta__time')
            duration = utils.safe_get_text(duration_tag)

            quality_tag = item.select_one('.is-hd, .is-4k, .is-1080p, .is-720p, .is-480p, .quality, .item__quality')
            quality = utils.safe_get_text(quality_tag)

            quoted_videopage = urllib_parse.quote_plus(videopage)
            context_menu = [
                ('[COLOR deeppink]Lookup info[/COLOR]',
                 f'RunPlugin({utils.addon_sys}?mode=watchporn.Lookupinfo&url={quoted_videopage})'),
                ('[COLOR deeppink]Related videos[/COLOR]',
                 f'RunPlugin({utils.addon_sys}?mode=watchporn.Related&url={quoted_videopage})')
            ]

            site.add_download_link(title, videopage, 'Playvid', thumb, title, duration=duration, quality=quality,
                                   contextm=context_menu)
            items_added += 1
        except Exception as exc:
            utils.kodilog('Error parsing WatchPorn video item: {}'.format(exc))
            continue

    if not items_added:
        utils.notify(msg='Nothing found')

    next_link = None
    for candidate in soup.select('a.next, a[data-block-id]'):
        text = utils.safe_get_text(candidate).lower()
        classes = candidate.get('class', [])
        if 'next' in text or 'page-next' in classes:
            next_link = candidate
            break
    if next_link:
        current_span = soup.select_one('.page-current span, span.page-current, li.active span')
        try:
            current_page = int(utils.safe_get_text(current_span, '0'))
        except ValueError:
            current_page = 0

        next_page_num = current_page + 1 if current_page > 0 else 2
        next_page_url = None

        block_id = next_link.get('data-block-id')
        params = next_link.get('data-parameters')
        if block_id and params:
            params = params.replace(';', '&').replace(':', '=')
            tm = int(time.time() * 1000)
            base_url = url.split('?')[0]
            nurl = (f'{base_url}?mode=async&function=get_block&block_id={block_id}&{params}&_={tm}')
            nurl = nurl.replace('+from_albums', '')
            next_page_url = re.sub(r'&from([^=]*)=\d+', rf'&from\1={next_page_num}', nurl)
        else:
            href = utils.safe_get_attr(next_link, 'href')
            if href:
                next_page_url = urllib_parse.urljoin(site.url, href)

        if next_page_url:
            cm_page_url = (f"{utils.addon_sys}?mode=watchporn.GotoPage&url="
                           f"{urllib_parse.quote_plus(next_page_url)}&np={next_page_num}&listmode=watchporn.List")
            cm = [('[COLOR violet]Goto Page #[/COLOR]', f'RunPlugin({cm_page_url})')]
            label = f'[COLOR hotpink]Next Page...[/COLOR] ({next_page_num})'
            site.add_dir(label, next_page_url, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(url, np, listmode):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + listmode + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = '{}{}/'.format(searchUrl, keyword.replace(' ', '-'))
        List(searchUrl)


@site.register()
def Categories(url):
    tm = int(time.time() * 1000)
    url = url + str(tm)
    cathtml = utils.getHtml(url)

    soup = utils.parse_html(cathtml)

    for anchor in soup.select('a.item[href], a.categories-list__item[href]'):
        catpage = utils.safe_get_attr(anchor, 'href')
        if not catpage:
            continue
        catpage = urllib_parse.urljoin(site.url, catpage)

        name = utils.safe_get_attr(anchor, 'title')
        if not name:
            name = utils.safe_get_text(anchor.select_one('.title, .item__title'))
        name = utils.cleantext(name)
        if not name:
            continue

        img_tag = anchor.select_one('img')
        img = None
        if img_tag:
            thumb_url = utils.safe_get_attr(img_tag, 'src', ['data-original', 'data-src', 'data-lazy'])
            if thumb_url:
                img = utils.fix_url(thumb_url, site.url)

        videos_tag = anchor.select_one('.videos, .item__videos, .meta__videos')
        videos = utils.safe_get_text(videos_tag)
        label = name
        if videos:
            label = f"{name} [COLOR deeppink]{videos}[/COLOR]"

        site.add_dir(label, catpage, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)

    match = re.compile(r"video(?:_|_alt_)url\d*: '([^']+)'.+?video(?:_|_alt_)url\d*_text: '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)

    sources = {}
    if match:
        for video in match:
            sources[video[1]] = video[0]
    vp.progress.update(75, "[CR]Video found[CR]")

    videourl = utils.prefquality(sources, sort_by=lambda x: int(x.replace(' 4k', '')[:-1]), reverse=True)
    if videourl:
        if videourl.startswith('function'):
            license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
            videourl = kvs_decode(videourl, license)

        vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Category", r'<a href="https://watchporn.to/(categories[^"]+)">([^<]+)<', ''),
        ("Tag", r'<a href="https://watchporn.to/(tags[^"]+)">([^<]+)<', ''),
        ("Model", r'<a href="https://watchporn.to/(models[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'watchporn.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('watchporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

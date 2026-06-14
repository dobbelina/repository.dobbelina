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

from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.decrypters import txxx
import xbmcaddon
import xbmcvfs
import os

addon = xbmcaddon.Addon()
addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
fallback_img = os.path.join(addon_path, 'resources', 'images', 'cum-nophoto.png')

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

site = AdultSite('camgirlfap', '[COLOR hotpink]CamGirlFap[/COLOR]', 'https://camgirlfap.com/', 'camgirlfap.png', 'camgirlfap')

addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?from=1', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/?sort_by=total_videos&from=1', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)

    List(site.url + 'latest-updates/?from=1')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="thumb thumb_rel item  ".*?href="([^"]+)" title="([^"]+)".*?data-(?:original|src|lazy-load)="([^"]+)".*?time">([^>]+)<'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('CamGirlFap', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name)    # + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    container = re.compile(r'<div class="pagination"(.+?)</div>', re.DOTALL | re.IGNORECASE).search(listhtml)
    if container:
        # NEXT PAGE
        m = re.search(r'''a class=['"]next['"].*?[?:;from\:|from_videos\+from_albums\:](\d+)"''', container.group(1), re.IGNORECASE)
        if m:
            next_page = m.group(1) if m else None

            # LAST PAGE
            pages = re.findall(r'[?:from\:|from_albums](\d+)"[^>]*>\s*(\d+)\s*</a>', container.group(1), re.IGNORECASE)
            last_page = pages[-1][0] if pages else None       
            if '/search/' in url:
                q = re.search(r'[?&]q=([^&]+)', url).group(1) if re.search(r'[?&]q=([^&]+)', url) else ''
                nplink = urljoin(url.split('?')[0], '?q=' + q + '&from_videos=' + next_page + '&from_albums=' + next_page) if next_page else None
            else:
                nplink = urljoin(url.split('?')[0] if '?' in url else url, '?from=' + next_page) if next_page else None
            site.add_dir('Next Page... ({0} of {1})'.format(next_page, last_page), nplink, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<div\s+class="thumb item"[\s\S]*?href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?'   #(?:<img[^>]+src="([^"]+)")[\s\S]*?</a>',
        , re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    listhtml = utils.getHtml(site.url + 'categories/?from=2')
    pattern = re.compile(
        r'<div\s+class="thumb item"[\s\S]*?href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?'   #(?:<img[^>]+src="([^"]+)")[\s\S]*?</a>',
        , re.IGNORECASE
    )
    matches = matches + pattern.findall(listhtml)

    if not matches:
        utils.notify('CamGirlFap', 'No Categories found.')
        return
    for videopage, name in matches:
        name = re.sub(r'[^A-Za-z0-9]', '', name)
        name = '[COLOR yellow]' + utils.cleantext(name) + '[/COLOR]'    # [COLOR hotpink][{0} clips][/COLOR] [COLOR white][{1} likes][/COLOR]'.format(clips, likes)
        site.add_dir(name, videopage, 'List', '')
        
    utils.eod()

@site.register()
def Models(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="thumb item"[\s\S]*?href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?(?:src="([^"]+)"|<span class="no-thumb">)[\s\S]*?icon-play[\s\S]*?<\/i>\s*([\d.K]+)'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('CamGirlFap', 'No Models found.')
        return
    for videopage, name, img, videos in matches:
        img = img if img else fallback_img
        videos = videos.replace('\n', '').strip()
        name = re.sub(r'[^A-Za-z0-9 ]', '', name)
        name = '[COLOR yellow]' + utils.cleantext(name) + '[/COLOR] [COLOR hotpink][{0}][/COLOR]'.format(videos)
        site.add_dir(name, videopage, 'List', img)
    if 'Load more' in listhtml:
        next_page = re.search(r'''a class="btn".*?;from:(\d+)"''', listhtml, re.IGNORECASE).group(1)
        if next_page:
            nplink = urljoin(url.split('?')[0], '?sort_by=total_videos&from=' + next_page) if next_page else None

            site.add_dir('Next Page... {0}'.format(next_page), nplink, 'Models', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '-') + '/?q=' + keyword.replace(' ', '+') + '&from_videos=1&from_albums=1'
        List(url)



@site.register()
def Playvid(url, name, download=None):
    html = utils.getHtml(url, site.url)
    sources = {}
    try:
        license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(html)[0]
    except IndexError:
        utils.notify('CamGirlFap', 'Video you are looking for is not found. It may have been removed from the site.')
        return
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    patterns = [
                r"video_url:\s*'([^']+)'.*?(?:video_url_text:\s*'([^']+)')?",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(html)
        for surl, qual in items:
            qual = '00' if (qual or '480p') == 'preview' else (qual or '480p')
            qual = qual.replace(' HD', '')
            surl = kvs_decode(surl, license)
            sources[qual] = surl
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl + '|referer=' + url)



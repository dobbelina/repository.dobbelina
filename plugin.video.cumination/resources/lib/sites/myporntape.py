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

site = AdultSite('myporntape', '[COLOR hotpink]MyPornTape[/COLOR]', 'https://myporntape.com/', 'myporntape.png', 'myporntape')

addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?sort_by=avg_videos_rating&from=1', 'Categories', site.img_cat)
    # site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/?sort_by=total_videos&from=1', 'Models', site.img_cat)
    # site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)

    List(site.url + 'latest-updates/?sort_by=post_date&from=1')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item  ".*?href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?time">([^>]+)<'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('MyPornTape', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name)    # + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    container = re.compile(r'<div class="pagination"(.+?)</section>', re.DOTALL | re.IGNORECASE).search(listhtml)
    if container:
        # NEXT PAGE
        m = re.search(r'''<div class="item pager next">[\s\S]*?from:(\d+)"''', container.group(1), re.IGNORECASE)
        if m:
            next_page = m.group(1) if m else None

            # LAST PAGE
            pages = re.findall(r'[?:from\:|from_albums](\d+)"[^>]*>\s*(\d+)\s*</a>', container.group(1), re.IGNORECASE)
            last_page = pages[-1][0] if pages else None       
            if '/search/' in url:
                q = re.search(r'[?&]q=([^&]+)', url).group(1) if re.search(r'[?&]q=([^&]+)', url) else ''
                nplink = urljoin(url.split('?')[0], '?q=' + q + '&from_videos=' + next_page + '&from_albums=' + next_page) if next_page else None
            else:
                nplink = urljoin(url.split('?')[0] if '?' in url else url, '?sort_by=post_date&from=' + next_page) if next_page else None
            site.add_dir('Next Page... ({0} of {1})'.format(next_page, last_page), nplink, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    last_page = max(map(int, re.findall(r'<div class="item">\s*<a[^>]+from:(\d+)"', listhtml)))
    matches = []
    for page in range(1, last_page + 1):
        listhtml = utils.getHtml(site.url + 'categories/?sort_by=avg_videos_rating&from=' + str(page))
        pattern = re.compile(
            r'<a\s+href="([^"]+)"[^>]*title="([^"]+)"[^>]*>.*?'
            r'<img[^>]+src="([^"]+)"[^>]*>.*?'
            r'class="text">\s*([^<]+)',
            re.DOTALL
        )
        matches += pattern.findall(listhtml)
    unique = list({item[0]: item for item in matches}.values())
    unique_sorted = sorted(unique, key=lambda x: x[1].lower())
    if not unique_sorted:
        utils.notify('MyPornTape', 'No Categories found.')
        return
    for videopage, name, img, videos in unique_sorted:
        name = re.sub(r'[^A-Za-z0-9]', '', name)
        name = '[COLOR yellow]' + utils.cleantext(name) + '[/COLOR] [COLOR hotpink][{0} clips][/COLOR]'.format(videos)
        site.add_dir(name, videopage, 'List', img)
     
    utils.eod()

@site.register()
def Search(url, keyword=None):
    return
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
        utils.notify('MyPornTape', 'Video you are looking for is not found. It may have been removed from the site.')
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



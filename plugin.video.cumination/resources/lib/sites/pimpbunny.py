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
import xbmc

from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


site = AdultSite('pimpbunny', '[COLOR hotpink]PimpBunny[/COLOR]', 'https://pimpbunny.com/', 'pimpbunny.png', 'pimpbunny')
addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]OnlyFans Creators[/COLOR]', site.url + 'onlyfans-creators/', 'Creators', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)

    List(site.url + 'videos/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<div class="col">.*?b6m-video">.*?href="([^"]+)".*?data-webp="([^"]+)".*?alt="([^"]+)".*?duration.*?">"?([^"<]+)"?<'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('PimpBunny', 'No videos found.')
        return
    for videopage, img, name, duration in matches:
        name = utils.cleantext(name)    # + ' [COLOR hotpink][{0}][/COLOR]'.format(duration)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    container = re.compile(r'<div class="includes-pagination-wrapper_.*?>(.*?)</div>', re.DOTALL | re.IGNORECASE).search(listhtml)
    if '/search/' in url:
        np = re.compile(r'class="next".*?data-parameters="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
        if np and ('from_videos' in np.group(1)):
            nplink = np.group(1).replace(':', '=').replace(';', '&').replace('+from_albums', '')
            nplink = urljoin(url.split('?')[0] if '?' in url else url, '?' + nplink)
            site.add_dir('Next Page...', nplink, 'List', site.img_next)
    elif '/onlyfans-creators/' in url:
        np = re.compile(r'class="includes-pagination-.*?href="([^"]*?(\d+)\/)"', re.DOTALL | re.IGNORECASE).search(listhtml)
        if np:
            nplink = urljoin(site.url, np.group(1))
            site.add_dir('Next Page...' + np.group(2), nplink, 'List', site.img_next)
    else:
        np = re.compile(r'''[?:result|list]_pagination.*?>\.\.\.<.*?">(\d*)<.*?pagination-arrow.*?href=['"]([^"]*?(\d+)\/)['"]>''', re.DOTALL | re.IGNORECASE).search(container.group(1) if container else '')

        if np:
            nplink = urljoin(site.url, np.group(2))
            nextpage = np.group(3)
            lastpage = np.group(1)
            # if nextpage < lastpage:
            site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'List', site.img_next)
        
    utils.eod()


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<div class="ui-card-root_.*?href="([^"]+)".*?class="ui-card-thumbnail_.*?'
        r'data-(?:original|src|lazy)="([^"]+)".*?'
        # r'<span>([^<]+)</span>.*?'
        # r'class="text-truncate">([^>]+)</div>.*?'
        r'alt="([^"]+)".*?'
        r'class="ui-card-info_.*?>([^>]+videos)'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('PimpBunny', 'No videos found.')
        return
    for videopage, img, name, videos in matches:
        name = re.sub(r'[^A-Za-z0-9]', '', name)
        name = '[COLOR yellow]' + utils.cleantext(name) + '[/COLOR] [COLOR hotpink][{0}][/COLOR]'.format(videos)
        site.add_dir(name, videopage, 'List', img)
        
    utils.eod()

@site.register()
def Creators(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        # r'<div class="ui-card-root_.*?href="(https://pimpbunny.com[^"]+).*?'
        r'<div class="ui-card-root_.*?href="([^"]+).*?'
        r'data-(?:original|src|lazy-load)="([^"]+)".*?'
        # r'lazy-load="([^"]+)".*?'
        r'ui-card-title_.*?<span>([^<]+)</span>'
        # r'<span>([^<]+)</span>'
        r'<div class="text-truncate">([^>]+)</div>.*?'
        # r'class="ui-card-info_.*?>([^<]*?)(?:\s*videos)?</div>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    
    if not matches:
        utils.notify('PimpBunny', 'No videos found.')
        return
    for videopage, img, number,name in matches:
        if 'https://pimpbunny.com' not in videopage:
            continue
        name = re.sub(r'[^A-Za-z0-9 ]', '', name)
        name = '[COLOR hotpink]'+ number + '[/COLOR] [COLOR yellow]' + utils.cleantext(name) + '[/COLOR]'   # [COLOR hotpink][{0}][/COLOR]'.format(videos)
        site.add_dir(name, videopage, 'List', img.replace(' ', '%20'))
        
    utils.eod()

@site.register()
def Models(url):
    listhtml = utils.getHtml(url)
    allmodels = re.compile(r'includes-pagination-count_.*?>(\d+)').findall(listhtml)
    url = 'https://pimpbunny.com/models/?models_per_page={}&model_type=verified'.format(allmodels[0] if allmodels else 1000)
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'ui-card-model_.*?href="([^"]+)".*?data-(?:original|src|lazy-load)="([^"]+)".*?text-truncate">([^>]+)<.*?<div>(.*?)</div>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('PimpBunny', 'No videos found.')
        return
    for videopage, img, name, videos in matches:
        if 'https://pimpbunny.com' not in videopage:
            continue
        if '0 videos' == videos:
            continue
        name = re.sub(r'[^A-Za-z0-9 ]', '', name)
        name = '[COLOR yellow]' + utils.cleantext(name) + '[/COLOR] [COLOR hotpink][{0}][/COLOR]'.format(videos)
        site.add_dir(name, videopage, 'List', img.replace(' ', '%20'))
        
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '-') + '/' + '?from_videos=1&ipp=32&page_type=&items_per_page=32&videos_per_page=32'
        # https://pimpbunny.com/search/xxx/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&from_videos=2&ipp=30&page_type=&items_per_page=30&videos_per_page=17&_=1780924158372
        # https://pimpbunny.com/search/xxx/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&from_videos=1&ipp=17&page_type=&items_per_page=17&videos_per_page=17&_=1780924158373
        List(url)



@site.register()
def Playvid(url, name, download=None):
    utils.kodilog('porntn Playvid: ' + url)
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(html)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(html)
        for surl, qual in items:
            qual = '00' if qual == 'preview' else qual
            qual = qual.replace(' HD', '')
            surl = kvs_decode(surl, license)
            sources[qual] = surl
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl + '|referer=' + url)



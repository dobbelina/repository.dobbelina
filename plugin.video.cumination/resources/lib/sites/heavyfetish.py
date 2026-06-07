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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite('heavyfetish', '[COLOR hotpink]HeavyFetish[/COLOR]', 'https://heavyfetish.com/', 'heavyfetish.png', 'heavyfetish')

addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'fetish-models/1/?models_per_page=32&sort_by=avg_videos_rating', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)

    List(site.url + '1/?&sort_by=post_date')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if 'categories/' in url:
        container = re.search(
            r'<div class="margin-fix" id="vt_videos_videos_list_vt_common_videos_list_items">(.*?)<div class="footer-margin">',
            listhtml,
            re.DOTALL | re.IGNORECASE
        )
    elif 'fetish-models' in url:
        container = re.search(
            r'<div class="margin-fix" id="vt_videos_videos_list_vt_common_videos_list_items">(.*?)<div class="footer-margin">',
            listhtml,
            re.DOTALL | re.IGNORECASE
        )
   
    else:
        container = re.search(
            r'<div class="margin-fix" id="vt_index_latest_videos_list_vt_most_recent_videos_items">(.*?)<div class="footer-margin">',
            listhtml,
            re.DOTALL | re.IGNORECASE
        )
    block = container.group(1) if container else ""
    pattern = re.compile(
        r'<div\s.*?b6m-video.*?href="([^"]+)".*?'
        r'title="([^"]+)".+?'
        r'data-webp="([^"]+)".*?'
        r'duration">([^>]+)<',
        re.DOTALL | re.IGNORECASE
    )

    matches = pattern.findall(block)
    if not matches:
        utils.notify('HeavyFetish', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + duration.strip() + '][/COLOR]'
        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile(r'<li[^>]*class="next"[^>]*>.*?href="([^"]*?(\d+)[^"]*)"'
        , re.DOTALL | re.IGNORECASE).search(listhtml)

    if np:
        href = re.sub(r'\s+', '', np.group(1))
        nextpage = np.group(2)
        nplink = href if href.startswith('http') else site.url[:-1] + href
        site.add_dir('Next Page... ({0})'.format(nextpage), nplink, 'List', site.img_next)
    utils.eod()


@site.register()
def ListSearch(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<div\s.*?b6m-video.*?href="([^"]+)".*?'
        r'title="([^"]+)".+?'
        r'data-webp="([^"]+)".*?'
        r'duration">([^>]+)<',
        re.DOTALL | re.IGNORECASE
    )

    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('HeavyFetish', 'No videos found.')
        return
    for videopage, name, img, duration in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + duration.strip() + '][/COLOR]'
        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile(r'class="last".+?;from_videos\+from_albums:([^:]+)">Last.+?;from_videos\+from_albums:([^:]+)">Next'
        , re.DOTALL | re.IGNORECASE).search(listhtml)

    if np:
        nplink = url.split('?')[0] + '?&from_videos=' + np.group(2) + '&from_albums=' + np.group(2)
        nextpage = np.group(2)
        lastpage = np.group(1)
        site.add_dir('Next Page... ({0} from {1})'.format(nextpage, lastpage), nplink, 'ListSearch', site.img_next)
    utils.eod()

@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<a class="item" href="([^"]+)"'
        r'\stitle="([^"]+)".+?'
        r'src="([^"]+)".+?' 
        r'videos">([^>]+)</div>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    for videopage, name, img, videos in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + videos.strip() + '][/COLOR]'
        videopage = videopage + '?&sort_by=post_date'                            # '1/?&sort_by=post_date'
        site.add_dir(name, videopage, 'List', img)

    np = re.compile(r'class="next\spager".*?href="([^"]+)".*?'
        r';from:([^:]*\d)">.*?'
        r';from:([^:]*\d)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        lastpage = np.group(3)
        site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'Categories', site.img_next)
    utils.eod()


@site.register()
def Models(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item b6m-model" href="([^"]+)" title="([^"]+)">.*?'
        r'src="([^"]+).*?'
        r'videos">([^>]+)</div>'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    for videopage, name, img, videos in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + videos.strip() + '][/COLOR]'
        site.add_dir(name, videopage, 'List', img)

    np = re.compile(r'class="last".*?href="/fetish-models/([^/]+)/.*?'
        r'class="next".*?href="([^"]+/(\d+)/+)'
        , re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(2) if np.group(2).startswith('http') else site.url[:-1] + np.group(2)
        nplink = nplink.split('?')[0] + '?models_per_page=32&sort_by=avg_videos_rating'
        nextpage = np.group(3)
        lastpage = np.group(1)
        site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'Models', site.img_next)
    utils.eod()

@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+') + '/?&from_videos=1&from_albums=1'
        ListSearch(url)

@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url)
    
    license = re.search(r"license_code:\s*'(\$\d+)",html, flags=re.DOTALL | re.IGNORECASE)
    video_url = re.search(r"video_url:\s*'([^']+)",html, flags=re.DOTALL | re.IGNORECASE)
    
    if license and video_url:
        lc = license.group(1)
        vu = video_url.group(1)
        
        final_url = kvs_decode(vu, lc)
   
        final_url += '|User-Agent={0}&Referer={1}'.format(utils.USER_AGENT, url)
        vp.play_from_direct_link(final_url)
    else:
        vp.play_from_site_link(url + ('/' if not url.endswith('/') else ''))


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

site = AdultSite('porn4fans', '[COLOR hotpink]Porn4Fans[/COLOR]', 'https://www.porn4fans.com/', 'porn4fans.png', 'porn4fans')

addon = utils.addon

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Most viewed[/COLOR]', site.url + 'onlyfans-videos/?p=video_viewed', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'onlyfans-videos/?p=rating', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Longest[/COLOR]', site.url + 'onlyfans-videos/?p=duration', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    
    List(site.url + 'onlyfans-videos/1/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item .+?\s* href="([^"]+)".*?'
        r'title="([^"]+)".+?'
        r'duration">([^>]+)<.+?'
        r'srcset="([^"]+)".+?'
        r'data-fav-video-id="([^"]+)"'
            , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    if not matches:
        utils.notify('Porn4Fans', 'No videos found.')
        return
    for videopage, name, duration, img, videoid in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + duration.strip() + '][/COLOR]'
        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile(r'class="next\spager".*?href="([^"]+)".*?'
        r';from:([^:]*\d)">.*?'
        r';from:([^:]*\d)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        lastpage = np.group(3)
        site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'List', site.img_next)
    utils.eod()

@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="item".*?href="([^"]+)".*?'
        r'title="([^"]+)".*?'
        r'src="([^"]+).*?'
        r'model-info-first">([^>]+)<.*?'
        r'model-info-first">([^>]+)<'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    for videopage, name, img, videos, views in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + videos.strip() + ' videos][/COLOR]' + ' [COLOR hotpink][' + views.strip() + ' views][/COLOR]'
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
        r'class="model-item".*?href="([^"]+)".*?'
        r'title="([^"]+)".*?'
        r'src="([^"]+).*?'
        r'model-info-first">([^>]+)<.*?'
        r'model-info-first">.*?<.*?'
        r'model-info-first">.*?<.*?'
        r'model-info-first">([^>]+)<'
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    for videopage, name, img, videos, views in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + videos.strip() + ' videos][/COLOR]' + ' [COLOR hotpink][' + views.strip() + ' views][/COLOR]'
        site.add_dir(name, videopage, 'List', img)

    np = re.compile(r'class="next\spager".*?href="([^"]+)".*?'
        r';from:([^:]*\d)">.*?'
        r';from:([^:]*\d)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        lastpage = np.group(3)
        site.add_dir('Next Page... ({0} of {1})'.format(nextpage, lastpage), nplink, 'Models', site.img_next)
    utils.eod()

@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+') + '/'
        List(url)


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


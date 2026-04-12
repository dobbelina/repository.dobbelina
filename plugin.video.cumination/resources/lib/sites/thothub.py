'''
    Cumination
    Copyright (C) 2026 Team Cumination

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
from resources.lib import utils
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite

site = AdultSite('thothub', '[COLOR hotpink]thothub[/COLOR]', 'https://thothub.tube/', 'https://thothub.tube/static/images/logo1colo2r.png', 'thothub')

# ListSites
# https://thothub.tube
# https://thothub.to
# https://thothub.lol
# https://thothub.mx

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?q=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Latest Updates[/COLOR]', site.url + 'latest-updates/', 'List', site.img_next)
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/', 'List', site.img_next)
    site.add_dir('[COLOR hotpink]Most Popular[/COLOR]', site.url + 'most-popular/', 'List', site.img_next)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_cat)
    
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    
    delimiter = 'class="item'
    re_videopage = 'href="([^"]+/videos/\d+/[^"]+/)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = 'class="views-counter2"[^>]*>([^<]+)'
    skip = 'ico-private'

    utils.videos_list(site, 'thothub.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, skip=skip)

    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', html, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        ts = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, ts)
        lpnr, lastp = 0, ''
        match = re.search(r':(\d+)">Last', html, re.DOTALL | re.IGNORECASE)
        if match:
            lpnr = match.group(1)
            lastp = '/{}'.format(lpnr)
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)
        site.add_dir('Next Page >> (' + str(npage) + lastp + ')', nurl, 'List', site.img_next)

    utils.eod()


@site.register()
def Categories(url):
    html = utils.getHtml(url, site.url)

    match = re.compile(r'<a class="item" href="([^"]+/categories/[^"]+/)" title="([^"]+)">', re.DOTALL).findall(html)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', site.img_cat, '')
    utils.eod()


@site.register()
def Models(url):
    html = utils.getHtml(url, site.url)
 
    delimiter = 'class="item'
    re_modelpage = 'href="([^"]+/models/[^"]+/)"'
    re_name = 'title="([^"]+)"'
    re_img = 'class="thumb" src="([^"]+)"'

    modellist = re.split(delimiter, html)
    if modellist:
        modellist.pop(0)
        for model in modellist:
            match_url = re.search(re_modelpage, model, flags=re.DOTALL | re.IGNORECASE)
            match_name = re.search(re_name, model, flags=re.DOTALL | re.IGNORECASE)
            match_img = re.search(re_img, model, flags=re.DOTALL | re.IGNORECASE)
            
            if match_url and match_name:
                img = match_img.group(1) if match_img else site.img_cat
                site.add_dir(match_name.group(1), match_url.group(1), 'List', img, '')
     
    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', html, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        ts = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, ts)
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)
        site.add_dir('Next Page >> (' + str(npage) + ')', nurl, 'Models', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = url + keyword.replace(' ', '+')
        List(searchUrl)


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

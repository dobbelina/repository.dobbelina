"""
    Cumination site scraper
    Copyright (C) 2020 Team Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite('javbangers', '[COLOR hotpink]JAV Bangers[/COLOR]', 'https://www.javbangers.com/', 'javbangers.png', 'javbangers')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    List(site.url + 'latest-updates/', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'class="video-item.+?href="([^"]+)"\s*title="([^"]+).+?original="([^"]+).+?clock[^\d]+([\d:]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan]({})[/COLOR]'.format(name2)
        site.add_download_link(name, videopage, 'Playvid', img, '')
    if re.search(r'<li\s*class="next"><a', listhtml, re.DOTALL | re.IGNORECASE):
        npage = page + 1
        if '/categories/' in url:
            if '/{}/'.format(page) in url:
                nurl = url.replace(str(page), str(npage))
            else:
                nurl = url + '{}/'.format(npage)
        elif '/search/' in url:
            if 'from_videos={0:02d}'.format(page) in url:
                nurl = url.replace('from_videos={0:02d}'.format(page), 'from_videos={0:02d}'.format(npage))
            else:
                nurl = url + '?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q=school+girl&category_ids=&sort_by=&from_videos={0:02d}'.format(npage)
        else:
            nurl = site.url[:-1] + re.compile(r'next"><a\s*href="(/[^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'List', site.img_next, npage)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name)
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
        site.add_dir(name, catpage, 'List', img, 1)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl.format(title)
        List(searchUrl)

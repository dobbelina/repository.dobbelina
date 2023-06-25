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

site = AdultSite('porncaper', '[COLOR hotpink]Porn Caper[/COLOR]', 'https://www.porncaper.com/', 'https://www.porncaper.com/contents/rqvkuiijephu/theme/logo.png', 'porncaper')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=rating&from=1', 'List', site.img_cat, page=1)
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'most-popular/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=video_viewed&from=1', 'List', site.img_cat, page=1)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/?mode=async&function=get_block&block_id=list_videos_latest_videos_list&sort_by=post_date&from=1', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, '')
    except Exception:
        return None

    match = re.compile(r'href="https://www\.porncaper\.com/([^"]+)"\s+title="([^"]+)".*?data-original="([^"]+)"(.*?)duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, hd, duration in match:
        name = utils.cleantext(name)
        videopage = site.url + videopage
        hd = 'HD' if 'hd' in hd.lower() else ''

        contexturl = (utils.addon_sys
                      + "?mode=porncaper.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu = [('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')]

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration, quality=hd)

    np = re.compile(r'class="next">.*?;from[^\d]*:(\d+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = int(np.group(1))
        if 'from_videos=' in url:
            nextp = url.replace('from_videos={}'.format(page), 'from_videos={}'.format(np))
        else:
            nextp = url.replace('from={}'.format(page), 'from={}'.format(np))
        site.add_dir('Next Page ({})'.format(np), nextp, 'List', site.img_next, page=np)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    surl = re.search(r"video_url:\s*'([^']+)'", html)
    if surl:
        surl = surl.group(1)
        if surl.startswith('function/'):
            license = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, license)
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(surl)


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except Exception:
        return None
    match = re.compile(r'item"\s+>?href="([^"]+)"\s+?title="([^"]+)">.*?src="([^"]+)".*?videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name) + ' [COLOR hotpink]({})[/COLOR]'.format(videos)
        catpage = catpage + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, catpage, 'List', img, page=1)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        url = url + title + '?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&sort_by=post_date&from_videos=1'
        List(url, 1)


@site.register()
def Lookupinfo(url):
    class TabootubeLookup(utils.LookupInfo):
        def url_constructor(self, url):
            ajaxpart = '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
            return site.url + url + ajaxpart

    lookup_list = [
        ("Cat", r'<a href="https://www\.porncaper\.com/(categories/[^"]+)">([^<]+)<', ''),
    ]

    lookupinfo = TabootubeLookup(site.url, url, 'porncaper.List', lookup_list)
    lookupinfo.getinfo()

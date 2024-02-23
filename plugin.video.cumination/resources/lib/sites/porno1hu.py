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

site = AdultSite('porno1hu', '[COLOR hotpink]Porno1.hu[/COLOR]', 'https://porno1.hu/', 'https://porno1.hu/static/images/logo.png')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'kategoriak/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'kereses/', 'Search', site.img_search)
    List(site.url + 'friss-porno/?mode=async&function=get_block&block_id=list_videos_latest_videos_list&sort_by=post_date&from=1', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, '')
    except Exception:
        return None

    match = re.compile(r'class="item p1ppnd.+?href="([^"]+)"\s+title="([^"]+)".+?.+?data-original="([^"]+)".+?.+?class="duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=porno1hu.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

    np = re.compile(r'\D(\d+)">Utols.+?class="next">.*?sort_by:[^;]*?;from[^\d]+(\d+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        lp = '/' + np.group(1)
        np = np.group(2)
        nextp = url
        for p in ['from', 'from_videos']:
            nextp = nextp.replace('{}={}'.format(p, str(page)), '{}={}'.format(p, np))
        site.add_dir('Next Page ({}{})'.format(np, lp), nextp, 'List', site.img_next, page=np)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    embedurl = re.compile(r'embedURL" content="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)[0]
    embedhtml = utils.getHtml(embedurl, url)
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(embedhtml)[0]
    videourl = re.compile(r"video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(embedhtml)[0]
    videourl = kvs_decode(videourl, license)
    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl + '|referer=' + url)


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except Exception:
        return None
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)".*?videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name)
        name = name + ' [COLOR hotpink](' + videos + ')[/COLOR]'
        catpage = catpage + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, catpage, 'List', '', page=1)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(searchUrl, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title + '?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&category_ids=&sort_by=&from_videos=1'
        List(searchUrl, 1)


@site.register()
def Lookupinfo(url):
    class porno1huLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if 'kategoriak/' in url or 'cimke/' in url:
                return url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'

    lookup_list = [
        ("Cat", r'<a href="(https://porno1.hu/kategoriak/[^"]+)">([^<]+)<', ''),
        ("Tag", r'<a href="(https://porno1.hu/cimke/[^"]+)">([^<]+)<', ''),
    ]

    lookupinfo = porno1huLookup('', url, 'porno1hu.List', lookup_list)
    lookupinfo.getinfo()

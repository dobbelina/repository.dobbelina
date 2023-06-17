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

site = AdultSite('theyarehuge', '[COLOR hotpink]They Are Huge[/COLOR]', 'https://www.theyarehuge.com/', 'https://www.theyarehuge.com/static/images/tah-logo-m.png', 'theyarehuge')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Most Popular[/COLOR]', site.url + 'popular.porn-video/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=video_viewed&from=1', 'List', site.img_cat, page=1)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'porn-video.tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/?mode=async&function=get_block&block_id=list_videos_latest_videos_list&sort_by=post_date&from=1', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile(r'href="https://www\.theyarehuge\.com/([^"]+)"\s+title="Big\s+Boobs\s+Porn\s+Video\s+([^"]+)".*?src="([^"]+)".*?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        videopage = site.url + videopage

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('theyarehuge.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

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
    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(html)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(html)
        for surl, qual in items:
            if '?login' in surl:
                continue
            qual = '00' if qual == 'preview' else qual
            surl = kvs_decode(surl, license)
            sources.update({qual: surl})
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl + '|referer=' + url)


@site.register()
def Tags(url):
    try:
        taghtml = utils.getHtml(url, '')
    except:
        return None
    htmlmatch = re.compile('list-tags">(.*?)footer', re.DOTALL | re.IGNORECASE).findall(taghtml)
    match = re.compile(r'/(porn-video\.tags/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(htmlmatch[0])
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = site.url + tagpage + '/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, tagpage, 'List', '', page=1)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title + '/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&sort_by=post_date&from_videos=1'
        List(searchUrl, 1)


@site.register()
def Lookupinfo(url):
    class TabootubeLookup(utils.LookupInfo):
        def url_constructor(self, url):
            ajaxpart = '/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
            return site.url + url + ajaxpart

    lookup_list = [
        ("Tag", r'/(porn-video\.tags/[^"]+)">([^<]+)\s<', ''),
        ("Model", r'tag-pornstar"\s+href="https://www\.theyarehuge\.com/([^"]+)">([^<]+)</a>', ''),
    ]

    lookupinfo = TabootubeLookup(site.url, url, 'theyarehuge.List', lookup_list)
    lookupinfo.getinfo()

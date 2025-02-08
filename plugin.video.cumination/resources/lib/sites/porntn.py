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

site = AdultSite('porntn', '[COLOR hotpink]PornTN[/COLOR]', 'https://porntn.com/', 'https://porntn.com/static/images/logo.png')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'new/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + '?mode=async&function=get_block&block_id=list_videos_most_recent_videos&sort_by=post_date&from=1', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, '')
    except Exception:
        return None

    match = re.compile(r'class="item\s*?">\s+<a href="https://porntn\.com/([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        videopage = site.url + videopage
        img = img if img.startswith('http') else site.url + img if not img.startswith('//') else 'https:' + img

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=porntn.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

    np = re.compile(r'class="next">.*?sort_by:[^;]*?;from[^\d]+(\d+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        nextp = url
        for p in ['from', 'from_videos']:
            nextp = nextp.replace('{}={}'.format(p, str(page)), '{}={}'.format(p, np))
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
            qual = '00' if qual == 'preview' else qual
            qual = qual.replace(' HD', '')
            surl = kvs_decode(surl, license)
            sources[qual] = surl
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

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
def Tags(url):
    try:
        taghtml = utils.getHtml(url, '')
    except Exception:
        return None
    match = re.compile('/(tags/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(taghtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = site.url + tagpage + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, tagpage, 'List', '', page=1)
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
    class porntnLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if 'categories/' in url:
                return url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'

    lookup_list = [
        ("Cat", r'<a href="(https://porntn\.com/categories/[^"]+)">([^<]+)<', ''),
    ]

    lookupinfo = porntnLookup(site.url, url, 'porntn.List', lookup_list)
    lookupinfo.getinfo()

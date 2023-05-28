"""
    Cumination
    Copyright (C) 2023 Team Cumin   

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
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite("hentai-moon", "[COLOR hotpink]Hentai Moon[/COLOR]", 'https://hentai-moon.com/', "hentai-moon.png", "hentai-moon")

ajaxlist = '?mode=async&function=get_block&block_id=list_videos_latest_videos_list&sort_by=post_date&from=1'
ajaxcommon = '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
ajaxtop = '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=rating&from=1'
ajaxmost = '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=video_viewed&from=1'


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Series[/COLOR]', site.url + 'series/?mode=async&function=get_block&block_id=list_dvds_channels_list&sort_by=title&from=1', 'Series', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/' + ajaxtop, 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'most-popular/' + ajaxmost, 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/' + ajaxlist)


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'href="([^"]+)"\s+?title="([^"]+)".*?data-original="([^"]+)"[^>]+(.*?)</div>.*?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, hd, duration in match:
        name = utils.cleantext(name)
        hd = " [COLOR orange]HD[/COLOR]" if 'is_hd' in hd else ''
        contexturl = (utils.addon_sys
                      + "?mode=" + str('hentai-moon.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu = ('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')
        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration, quality=hd)
    np = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        pagelookup = re.search(r"(from(?:_videos)?)=(\d+)", url)
        if pagelookup:
            page = pagelookup.group(2)
            fromtxt = pagelookup.group(1)
            url = url.replace("{0}={1}".format(fromtxt, page), "{0}={1}".format(fromtxt, np))
            site.add_dir('Next Page ({0})'.format(np), url, 'List', site.img_next)

    utils.eod()


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'item"\s+?href="([^"]+)"\s?title="([^"]+)".*?src="([^"]+)".*?videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos.strip() + "[/COLOR]"
        catpage = catpage + ajaxcommon
        site.add_dir(name, catpage, 'List', img, name)
    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('/(tags/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = site.url + tagpage + ajaxcommon
        site.add_dir(name, tagpage, 'List', '')
    utils.eod()


@site.register()
def Series(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'href="([^"]+)"\s+?title="([^"]+)".*?data-original="([^"]+)".*?videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for seriepage, name, img, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos.strip() + "[/COLOR]"
        seriepage = seriepage + ajaxcommon
        site.add_dir(name, seriepage, 'List', img, name)
    np = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        pagelookup = re.search(r"(from(?:_videos)?)=(\d+)", url)
        if pagelookup:
            page = pagelookup.group(2)
            fromtxt = pagelookup.group(1)
            url = url.replace("{0}={1}".format(fromtxt, page), "{0}={1}".format(fromtxt, np))
            site.add_dir('Next Page ({0})'.format(np), url, 'Series', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchq = keyword.replace(' ', '+')
        url = "{0}{1}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={2}&cat_ids=&sort_by=&from_videos=1".format(url, title, searchq)
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    vpage = utils.getHtml(url, site.url)

    videourl = None
    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(vpage)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url\d*?:\s*'([^']+)[^;]+?video_alt_url\d*?_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
        for surl, qual in items:
            qual = '00' if qual == 'preview' else qual
            surl = kvs_decode(surl, license)
            sources.update({qual: surl})

    if len(sources) > 0:
        videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
        if not videourl:
            vp.progress.close()
            return
    else:
        match = re.search(r'Download:\s*?<a href="([^"]+)"', vpage, re.IGNORECASE | re.DOTALL)
        if match:
            videourl = match.group(1)

    if videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", '/(categories/[^"]+)">([^<]+)<', ''),
        ("Tag", '/(tags[^"]+)">([^<]+)<', ''),
        ("Serie", '/(series/[^"]+)">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'hentai-moon.List', lookup_list)
    lookupinfo.getinfo()
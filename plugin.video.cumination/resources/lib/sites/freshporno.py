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

site = AdultSite('freshporno', '[COLOR hotpink]FreshPorno[/COLOR]', 'https://freshporno.net/', 'freshporno.jpg', 'freshporno')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'thumbs-inner">.*?href="([^"]+)"\s*title="([^"]+)".*?data-original="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, img in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('freshporno.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    np = re.compile(r'next"><a\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', site.url + np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    vpage = utils.getHtml(url, site.url)

    videourl = None
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

    if len(sources) > 0:
        videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
        if not videourl:
            vp.progress.close()
            return
    else:
        match = re.search(r'href="([^"]+)"\s*class="btn-download"', vpage, re.IGNORECASE | re.DOTALL)
        if match:
            videourl = match.group(1)

    if videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('/(tags/[^"]+)+"><i class="fa fa-tag"></i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name.strip())
        site.add_dir(name, site.url + tagpage, 'List', '')

    utils.eod()


@site.register()
def Channels(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'content-wrapper">.*?title="([^"]+)"\s*href="([^"]+)"(.*?)</i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, channelpage, img, videos in match:
        name = "{} - {}".format(utils.cleantext(name.strip()), videos)

        if 'no image' in img:
            img = ''
        elif 'data-original' in img:
            img = re.search('data-original="([^"]+)"', img, re.IGNORECASE | re.DOTALL).group(1)

        site.add_dir(name, channelpage, 'List', img)

    utils.eod()


@site.register()
def Models(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'content-wrapper">.*?title="([^"]+)"\s*href="([^"]+)"(.*?)</i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, modelpage, img, videos in match:
        name = "{} - {}".format(utils.cleantext(name.strip()), videos)

        if 'no image' in img:
            img = ''
        elif 'data-original' in img:
            img = re.search('data-original="([^"]+)"', img, re.IGNORECASE | re.DOTALL).group(1)

        site.add_dir(name, modelpage, 'List', img)

    np = re.compile(r'next"><a\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', site.url + np.group(1), 'Models', site.img_next)

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Channel", '/(channels/[^"]+)">([^<]+)<', ''),
        ("Tag", '/(tags[^"]+)">[^<]+<[^<]+</i>([^<]+)<', ''),
        ("Actor", '/(models/[^"]+)">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'freshporno.List', lookup_list)
    lookupinfo.getinfo()
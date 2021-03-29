'''
    Cumination
    Copyright (C) 2020 Whitecream

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


site = AdultSite("cpv", "[COLOR hotpink]Cartoon Porn Videos[/COLOR]", "https://www.cartoonpornvideos.com/", "cpv.png", "cpv")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}categories/'.format(site.url), 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Characters[/COLOR]', '{0}characters/'.format(site.url), 'Char', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}search/video/'.format(site.url), 'Search', site.img_search)
    List('{0}videos/straight/all-recent.html'.format(site.url))


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    # match = re.compile(r'''class="item".+?src="([^"]+)[^>]+>(.*?)time">([^<]+).+?playME\('([^']+).+?video-title[^>]+>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    match = re.compile(r'''class="item".+?src="([^"]+)[^>]+>(.*?)time">([^<]+).+?playME\('([^']+).+?href="([^"]+)[^>]+>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    # for img, hd, duration, vid, name in match:
    for img, hd, duration, vid, vidurl, name in match:
        hd = 'HD' if 'HD' in hd else ''
        name = utils.cleantext(name)
        # vidurl = '{0}embed/{1}'.format(site.url, vid)
        site.add_download_link(name, vidurl, 'Playvid', img, name, duration=duration, quality=hd)

    np = re.compile(r'class="pagination\s*_767p.+?class="active">\d+</a>&nbsp;<a\shref="([^"]+)">(\d+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page... ({0})'.format(np.group(2)), np.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="item\svideo.+?src="([^"]+).+?href="([^"]+)"[^>]+>([^<]+).+?stats">[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for img, catpage, name, videos in match:
        name = "{0} [COLOR deeppink]({1})[/COLOR]".format(utils.cleantext(name), videos)
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Char(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'class="item".+?src="([^"]+).+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for img, charpage, name in match:
        name = utils.cleantext(name)
        img = re.sub(r'\s', '', img)
        site.add_dir(name, charpage.strip(), 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        url += title
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    videopage = utils.getHtml(url, site.url)
    # sources = re.compile(r'file:\s*"([^"]+)",\s*label:\s*"([^\s]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    # if sources:
    #     sources = {label: source for source, label in sources}
    #     videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x[:-1]), reverse=True)
    #     if videourl:
    #         vp.play_from_direct_link(videourl)
    # else:
    #     return
    source = re.compile(r'file:\s*"([^"]+)",\s*type:\s*"([^"\s]+)', re.DOTALL | re.IGNORECASE).search(videopage)
    if source:
        vp.play_from_direct_link(source.group(1))
    else:
        return

'''
    Cumination
    Copyright (C) 2018 Whitecream

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

site = AdultSite('xfreehd', '[COLOR hotpink]XFreeHD[/COLOR]', 'https://www.xfreehd.com/', 'xfreehd.png', 'xfreehd')


@site.register(default_mode=True)
def xfreehd_main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'xfreehd_cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?search_query=', 'xfreehd_search', site.img_search)
    xfreehd_list(site.url + 'videos?o=mr')


@site.register()
def xfreehd_list(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''class="well\s*well-sm.+?href="([^"]+).+?src="(.+?).\s*title[^>]+>(.+?)duration-new">\s*([^\s]+).+?title-new.+?>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, hd, duration, name in match:
        hd = 'HD' if '>HD<' in hd else ''
        if 'data-src' in img:
            img = img.split('data-src="')[1]
        else:
            img = site.url[:-1] + img
        name = utils.cleantext(name)
        site.add_download_link(name, site.url[:-1] + video, 'xfreehd_play', img, name, duration=duration, quality=hd)

    np = re.compile(r'''<li><a\s*href="([^"]+)"\s*class="prevnext"''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        next_page = np.group(1)
        page_number = ''.join([nr for nr in next_page.split('=')[-1] if nr.isdigit()])
        site.add_dir('Next Page (' + page_number + ')', next_page, 'xfreehd_list', site.img_next)

    utils.eod()


@site.register()
def xfreehd_cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''class="col-xs-6\s*col-sm-4\scol.+?href="([^"]+).+?data-src="([^"]+)"\s*title="([^"]+).+?badge">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name, videos in match:
        name = utils.cleantext(name.strip()) + " [COLOR hotpink]%s Videos[/COLOR]" % videos
        site.add_dir(name, site.url[:-1] + catpage, 'xfreehd_list', site.url[:-1] + img)
    utils.eod()


@site.register()
def xfreehd_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'xfreehd_search')
    else:
        title = keyword.replace(' ', '+')
        url = url + title + '&search_type=videos&o=mr'
        xfreehd_list(url)


@site.register()
def xfreehd_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, '')
    sources = {}
    srcs = re.compile(r'''src="([^"]+)"\s*title="(SD|HD)"''', re.DOTALL | re.IGNORECASE).findall(html)
    if srcs:
        for videourl, quality in srcs:
            sources[quality] = videourl
        videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: x)
        vp.play_from_direct_link(videourl)

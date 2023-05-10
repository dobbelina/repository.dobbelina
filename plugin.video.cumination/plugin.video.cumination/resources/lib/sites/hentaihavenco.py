"""
    Cumination
    Copyright (C) 20222 Team Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hentaihavenc', '[COLOR hotpink]Hentaihaven[/COLOR]', 'https://hentaihaven.co/', 'hh.png', 'hentaihavenco')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'genres/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Series[/COLOR]', site.url + 'series/', 'Series', site.img_cat, section='Home')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a\s*href="([^"]+)">\s*<figure.+?img.+?src="([^"]+).+?<h2[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    page = re.compile(r'<a\s*href="([^"]+/(\d+)/)">Next<', re.DOTALL | re.IGNORECASE).search(listhtml)
    if page:
        site.add_dir('[COLOR hotpink]Next Page[/COLOR] ({0})'.format(page.group(2)), page.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    surl = re.compile(r'<iframe.+?src="([^"]*)', re.DOTALL | re.IGNORECASE).search(videopage)
    if surl:
        surl = surl.group(1)
        if 'nhplayer.com' in surl:
            videopage = utils.getHtml(surl, site.url)
            surl = re.compile(r'<li data-id="([^"]+)').search(videopage)
            if surl:
                surl = surl.group(1)
                if surl.startswith('/'):
                    surl = 'https://nhplayer.com' + surl
                    videohtml = utils.getHtml(surl, site.url)
                    vp.direct_regex = r'file:\s*"([^"]+)"'
                    vp.play_from_html(videohtml)
                    vp.progress.close()
                    return
            else:
                vp.progress.close()
                utils.notify('Oh oh', 'Couldn\'t find a playable link')
        vp.play_from_link_to_resolve(surl)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'Couldn\'t find a playable link')
    return


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a\s*class="bg-tr"\s*href="([^"]+).+?img.+?src="([^"]+).+?<h2.+?>([^<]+).+?text-sm">(?:<p>)?([^<]*).+?white">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, image, name, desc, count in match:
        name = utils.cleantext(name)
        if count:
            name += " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
        site.add_dir(name, catpage, 'List', image, desc=desc)
    utils.eod()


@site.register()
def Series(url, section):
    cathtml = utils.getHtml(url, site.url)
    if section == 'Home':
        match = re.compile(r'<a\s*class="c-htr3[^>]+?href="#l-.*?">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
        for alpha in match:
            site.add_dir(alpha, url, 'Series', '', section=alpha)
    else:
        section = r'\d' if section == "#" else section
        match = re.compile(r'<a\s*class="c-htr3[^>]+?href="(http[^"]+)">({0}[^<]+)'.format(section), re.DOTALL | re.IGNORECASE).findall(cathtml)
        for spage, name in match:
            site.add_dir(name, spage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)

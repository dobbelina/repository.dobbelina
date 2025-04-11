'''
    Cumination Site Plugin
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
'''

import re
import pickle
import binascii
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('aagmaalpro', '[COLOR hotpink]Aag Maal Pro[/COLOR]', 'https://aagmaal.boo/', 'logo.png', 'aagmaalpro')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<article.+?href="([^"]+).+?src="([^"]+).+?duration">(?:<i.+?/i>)?([\d:]*)<.+?header.+?span>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, duration, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = re.compile(r'''class="pagination.+?class="current.+?href="([^"]+)">Next''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        currpg = re.findall(r'class="pagination.+?class="current">([^<]+)', listhtml, re.DOTALL)[0]
        lastpg = re.findall(r'''class="pagination.+?href=['"]([^'"]+)['"]>Last''', listhtml, re.DOTALL)[0].split('/')[-2]
        pgtxt = 'Currently in Page {0} of {1}'.format(currpg, lastpg)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(pgtxt), np.group(1), 'List', site.img_next)
    else:
        np = re.compile(r'''class="pagination".+?class="current">.+?href="([^"]+)"\s*class="inactive''', re.DOTALL | re.IGNORECASE).search(listhtml)
        if np:
            pgtxt = 'Currently in {0}'.format(re.findall(r'class="pagination".+?class="current">([\d+])', listhtml)[0])
            site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(pgtxt), np.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def List2(url):
    listhtml = utils.getHtml(url, site.url)
    items = re.compile(r'<article.+?/article>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for item in items:
        iurl, name, img = re.compile(r'title">\s*<a\s*href="([^"]+)">([^<]+).+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(item)[0]
        name = utils.cleantext(name)
        site.add_download_link(name, iurl, 'Playvid', img, name)

    purl = re.compile(r'''class="pagination.+?class="current.+?href="([^"]+)''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if purl:
        pgtxt = 'Currently in {0}'.format(re.findall(r'class="pages">([^<]+)', listhtml)[0])
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(pgtxt), purl.group(1), 'List2', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videourl = ''

    if url.startswith('http'):
        videopage = utils.getHtml(url, site.url)
        links = re.compile(r'''href="(https?://((?!aagmaal)[^/]+)[^"]+)"[^>]*>.*?Watch''', re.DOTALL | re.IGNORECASE).findall(videopage)
    else:
        links = pickle.loads(binascii.unhexlify(url))

    if links:
        links = {host: link for link, host in links if vp.resolveurl.HostedMediaFile(link)}
        videourl = utils.selector('Select link', links)
    else:
        r = re.search(r'<iframe\s*loading="lazy"\s*src="([^"]+)', videopage)
        if r:
            videourl = r.group(1)
        else:
            r = re.search(r'<iframe.+?src="(http[^"]+)', videopage)
            if r:
                videourl = r.group(1)

    if not videourl:
        utils.notify('Oh Oh', 'No Videos found')
        vp.progress.close()
        return

    vp.play_from_link_to_resolve(videourl)


@site.register()
def Categories(url):
    match = []
    while url:
        cathtml = utils.getHtml(url, site.url)
        match += re.compile(r'<article.+?href="([^"]+).+?src="([^"]+).+?title">([^<]+)', re.DOTALL).findall(cathtml)
        np = re.compile(r'''class="pagination".+?class="current">.+?href="([^"]+)"\s*class="inactive''', re.DOTALL | re.IGNORECASE).search(cathtml)
        url = np.group(1) if np else False

    for catpage, img, name in sorted(match, key=lambda item: item[2].lower()):
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'List', img)
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

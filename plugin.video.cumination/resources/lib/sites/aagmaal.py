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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('aagmaal', '[COLOR hotpink]Aag Maal[/COLOR]', 'https://aagmaal.com/', 'https://i.imgur.com/ZdrI4Xn.png', 'aagmaal')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}?s='.format(site.url), 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'class=recent-item.+?src=([^\s]+).+?href=([^\s]+)[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, videopage, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    url = re.compile(r'''class=pagination.+?class=current.+?href=['"]?([^\s'"]+)''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if url:
        pgtxt = 'Currently in {0}'.format(re.findall(r'class=pages>([^<]+)', listhtml)[0])
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), url.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def List2(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<article.+?href=([^\s>]+)>([^<]+).+?src=([^\s]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    url = re.compile(r'''class=pagination.+?class=current.+?href=['"]?([^\s'"]+)''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if url:
        pgtxt = 'Currently in {0}'.format(re.findall(r'class=pages>([^<]+)', listhtml)[0])
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] {0}'.format(pgtxt), url.group(1), 'List2', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    videopage = re.compile(r"<p>(<.+?</a>)</p>", re.DOTALL | re.IGNORECASE).findall(videopage)
    if videopage:
        links = re.compile(r"href=(https?://([^/]+)[^\s]+)", re.DOTALL | re.IGNORECASE).findall(videopage[-1])
        if links:
            links = {host: link for link, host in links if vp.resolveurl.HostedMediaFile(link).valid_url()}
            videourl = utils.selector('Select link', links)
            if not videourl:
                vp.progress.close()
                return
            vp.play_from_link_to_resolve(videourl)
        else:
            utils.notify('Oh Oh', 'Cant find resolvable links')
            vp.progress.close()
            return
    else:
        utils.notify('Oh Oh', 'No Videos found')
        vp.progress.close()
        return


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="menu-item.+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    match += re.compile(r'class="cat-item.+?href=([^\s]+)[^>]+>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        catpage = site.url[:-1] + catpage if catpage.startswith('/') else catpage
        site.add_dir(name, catpage, 'List2')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List2(searchUrl)

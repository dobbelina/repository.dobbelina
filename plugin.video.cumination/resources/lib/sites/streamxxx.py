'''
    Cumination
    Copyright (C) 2015 Whitecream
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

site = AdultSite('streamxxx', '[COLOR hotpink]StreamXXX[/COLOR]', 'https://streamxxx.tv/', 'streamxxx.png', 'streamxxx')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url, 'Tags', '', '')
    site.add_dir('[COLOR hotpink]Movies[/COLOR]', site.url + 'category/movies-xxx/', 'MainMovies', '', '')
    site.add_dir('[COLOR hotpink]International Movies[/COLOR]', site.url + 'category/movies-xxx/international-movies/', 'MainInternationalMovies', '', '')
    site.add_dir('[COLOR hotpink]Search Overall[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Search Scenes[/COLOR]', site.url + '?cat=5562&s=', 'Search', site.img_search)
    List(site.url + 'category/clips/')
    utils.eod()


@site.register()
def MainMovies():
    List(site.url + 'category/movies-xxx/')
    utils.eod()


@site.register()
def MainInternationalMovies():
    List(site.url + 'category/movies/international-movies/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, url)
    match = re.compile(r'<article.+?title.+?href=([^\s]+).+?>([^<]+).+?title="([^"]+).+?src=([^\s]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, info, img in match:
        name = utils.cleantext(name)
        info = utils.cleantext(info)
        # if videopage.startswith('/'):
        #     videopage = site.url[:-1] + videopage
        site.add_download_link(name, videopage, 'Playvid', img, info)
    np = re.compile(r'class="next page-numbers"\s*href="?([^\s>"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        currpg = re.compile(r'class="page-numbers\s*current">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        lastpg = re.compile(r'>([^<]+)</a></li>\s*<li><a\s*class="next\s*page-numbers"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        site.add_dir('Next Page...(Currently in {0} of {1})'.format(currpg, lastpg), np.group(1), 'List', site.img_next)

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


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'href=(https://streamxxx\.tv/category/[^\s]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Tags(url):
    html = utils.getHtml(url, '')
    match = re.compile(r'href=(https://streamxxx\.tv/tag/[^\s]+).+?label="([^"]+)', re.DOTALL | re.IGNORECASE).findall(html)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    phtml = utils.getHtml(url, site.url)
    phtml = re.compile('(<main.+?main>)').findall(phtml)[0]
    sources = re.compile(r'href=([^\s]+)\s*(?:target=_blank rel="nofollow noopener noreferrer")?\s*class="external').findall(phtml)
    links = {}
    for link in sources:
        if 'adshrink' in link:
            link = 'http' + link.split('http')[-1]
        if vp.resolveurl.HostedMediaFile(link).valid_url():
            links[link.split('/')[2]] = link
    videourl = utils.selector('Select link', links)
    if not videourl:
        vp.progress.close()
        return
    vp.play_from_link_to_resolve(videourl)

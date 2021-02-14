'''
    Cumination
    Copyright (C) 2016 Whitecream, hdgdl, holisticdioxide

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

site = AdultSite('xhamster', '[COLOR hotpink]xHamster[/COLOR]', 'https://xhamster.com/', 'xhamster.png', 'xhamster')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories - Straight[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - Gay[/COLOR]', site.url + 'gay/categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - Shemale[/COLOR]', site.url + 'shemale/categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search.php?q=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    response = utils.getHtml(url, site.url)
    match0 = re.compile('<head>(.*?)</head>.*?index-videos.*?>(.*?)<footer>', re.DOTALL | re.IGNORECASE).findall(response)
    main_block = match0[0][1]
    match = re.compile('thumb-image-container" href="([^"]+)".*?<i class="thumb-image-container__icon([^>]+)>.*?src="([^"]+)".*?alt="([^"]+)".*?duration">([^<]+)</div', re.DOTALL | re.IGNORECASE).findall(main_block)
    for video, hd, img, name, length in match:
        hd = ' [COLOR orange]HD[/COLOR]' if 'hd' in hd else ''
        name = utils.cleantext(name) + hd + ' [COLOR hotpink]' + length + '[/COLOR]'
        site.add_download_link(name, video, 'Playvid', img, name)

    np = re.compile(r'<a\s+data-page="next"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(response)
    if np:
        site.add_dir('Next Page', np.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_link_to_resolve(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match0 = re.compile('<div class="letter-blocks page">(.*?)<footer>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    match = re.compile('<a href="(.+?)" >([^<]+)<').findall(match0[0])
    for url, name in match:
        site.add_dir(name.strip(), url + '/newest', 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '_')
        searchUrl = searchUrl + title
        List(searchUrl)

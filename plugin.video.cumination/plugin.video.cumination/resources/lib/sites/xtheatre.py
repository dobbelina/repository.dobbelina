'''
    Cumination
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

site = AdultSite('xtheatre', '[COLOR hotpink]Xtheatre[/COLOR]', 'https://pornxtheatre.com/', 'https://pornxtheatre.com/wp-content/uploads/2020/06/ggf.png', 'xtheatre')

addon = utils.addon

sortlistxt = [addon.getLocalizedString(30022), addon.getLocalizedString(30023), addon.getLocalizedString(30024),
              addon.getLocalizedString(30025)]


@site.register(default_mode=True)
def XTMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'XTCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'XTSearch', site.img_search)
    Sort = '[COLOR hotpink]Current sort:[/COLOR] ' + sortlistxt[int(addon.getSetting("sortxt"))]
    site.add_dir(Sort, '', 'XTSort', '', '')
    XTList(site.url + '?filter=latest', 1)
    utils.eod()


@site.register()
def XTSort():
    addon.openSettings()
    XTMain()


@site.register()
def XTCat(url):
    nextpg = True
    while nextpg:
        cathtml = utils.getHtml(url, '')
        match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
        for catpage, name, img in match:
            catpage = catpage + 'page/1/' if catpage.endswith('/') else catpage + '/page/1/'
            site.add_dir(name, catpage, 'XTList', img, 1)
        pagination = re.findall('class="pagination">(.+?</ul>)', cathtml)[0]
        np = re.search('class="current".+?href="([^"]+)', pagination)
        if np:
            url = np.group(1)
        else:
            nextpg = False
    utils.eod()


@site.register()
def XTSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'XTSearch')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        XTList(searchUrl, 1)


@site.register()
def XTList(url, page=1):
    sort = getXTSortMethod()
    if re.search(r'\?', url, re.DOTALL | re.IGNORECASE):
        url = url + '&filter=' + sort
    else:
        url = url + '?filter=' + sort

    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'XTVideo', img, name)

    npage = re.search('href="([^"]+)">Next', listhtml, re.DOTALL | re.IGNORECASE)
    if npage:
        site.add_dir('Next Page ...', npage.group(1), 'XTList', site.img_next, npage)
    else:
        pagination = re.findall('class="pagination">(.+?</ul>)', listhtml)[0]
        np = re.search('class="current".+?href="([^"]+)', pagination)
        if np:
            site.add_dir('Next Page ...', np.group(1), 'XTList', site.img_next)
    utils.eod()


@site.register()
def XTVideo(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)


def getXTSortMethod():
    sortoptions = {0: 'date',
                   1: 'title',
                   2: 'views',
                   3: 'likes'}
    sortvalue = addon.getSetting("sortxt")
    return sortoptions[int(sortvalue)]

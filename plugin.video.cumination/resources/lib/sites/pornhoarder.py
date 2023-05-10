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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('pornhoarder', '[COLOR hotpink]PornHoarder[/COLOR]', 'https://pornhoarder.tv/', 'pornhoarder.jpg', 'pornhoarder')

headers = {
    'Origin': 'https://pornhoarder.tv',
    'User-Agent': utils.USER_AGENT,
    'X-Requested-With': 'XMLHttpRequest',
}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'studios/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'Search', site.img_search)
    List(site.url + 'ajax_search.php')
    utils.eod()


@site.register()
def List(url, page=1):
    search = ''
    if not url.startswith('https://'):
        search = url
        url = site.url + 'ajax_search.php'
    data = Createdata(page, search)
    listhtml = utils.postHtml('https://pornhoarder.tv/ajax_search.php', headers=headers, form_data=data)
    match = re.compile('href="([^"]+)".*?data-src="([^"]+)"(.*?)h1>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, length, name in match:
        name = utils.cleantext(name)
        videopage = site.url[:-1] + videopage

        if 'length' in length:
            length = re.search('length">([^<]+)<', length, re.IGNORECASE | re.DOTALL).group(1)
        else:
            length = ''

        site.add_download_link(name, videopage, 'Playvid', img, name, duration=length)

    np = re.compile('next"><span class="pagination-button" data-page="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1)
        site.add_dir('Next Page (' + page_number + ')', site.url + 'ajax_search.php', 'List', site.img_next, page=int(page_number))
    utils.eod()


def Createdata(page=1, search=''):
    data = [
        ('search', search),
        ('sort', '0'),
        ('date', '0'),
        ('servers[]', '21'),
        ('servers[]', '11'),
        ('servers[]', '37'),
        ('servers[]', '12'),
        ('servers[]', '35'),
        ('servers[]', '39'),
        ('servers[]', '26'),
        ('servers[]', '25'),
        ('servers[]', '31'),
        ('servers[]', '17'),
        ('author', '0'),
        ('page', page)
    ]

    return data


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=r'''<iframe.+?src\s*=\s*["']([^'"]+)''')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    videopage = re.compile('iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
    vidhtml = utils.postHtml(videopage, headers=headers, form_data={'play': ''})
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_html(vidhtml)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(keyword, page=1)


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'article>\s*<a href="/search/\?search=([^"]+)".*?data-src="/??([^"]+)".*?h2>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name in match:
        name = utils.cleantext(name.strip())
        img = site.url + img if img.startswith('/') else img
        site.add_dir(name, catpage, 'List', img)

    nextp = re.compile('class="next"><a href="/([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        page_link = nextp[0]
        page_nr = re.findall(r'\d+', page_link)[-1]
        site.add_dir('Next Page ({})'.format(page_nr), site.url + page_link, 'Categories', site.img_next)

    utils.eod()

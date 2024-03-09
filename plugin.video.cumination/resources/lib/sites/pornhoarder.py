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

site = AdultSite('pornhoarder', '[COLOR hotpink]PornHoarder[/COLOR]', 'https://ww2.pornhoarder.tv/', 'pornhoarder.jpg', 'pornhoarder')

ph_headers = {
    'Origin': 'https://ww2.pornhoarder.tv',
    'User-Agent': utils.USER_AGENT,
    'X-Requested-With': 'XMLHttpRequest',
}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'studios/', 'Studios', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'Search', site.img_search)
    List(site.url + 'ajax_search.php')
    utils.eod()


@site.register()
def List(url, page=1):
    search = '' if url.startswith('https://') else url
    data = Createdata(page, search)
    listhtml = utils.postHtml('https://ww2.pornhoarder.tv/ajax_search.php', headers=ph_headers, form_data=data)
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
        site.add_dir('Next Page (' + page_number + ')', url, 'List', site.img_next, page=int(page_number))
    utils.eod()


@site.register()
def List2(url, page=1):
    listhtml = utils.getHtml(url)
    match = re.compile(r'article>\s+<a href="([^"]+)".*?data-src="([^"]+)"(.*?)h1>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
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

    np = re.compile('next"><a href="([^"]+)".*?data-page="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(2)
        nextpage = np.group(1)
        site.add_dir('Next Page (' + page_number + ')', site.url + nextpage, 'List2', site.img_next, page=int(page_number))
    utils.eod()


def Createdata(page=1, search=''):
    return [
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
        ('page', page),
    ]


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=r'''<iframe.+?src\s*=\s*["']([^'"]+)''')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    videopage = re.compile('iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
    vidhtml = utils.postHtml(videopage, headers=ph_headers, form_data={'play': ''})
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


@site.register()
def Pornstars(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'article>\s*<a href="([^"]+)".*?data-src="/??([^"]+)".*?h2>([^<]+)<.*?meta">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name, videos in match:
        name = utils.cleantext(name.strip())
        img = site.url + img if img.startswith('/') else img
        name = '{} [COLOR deeppink]{}[/COLOR]'.format(name, videos.strip())
        catpage = site.url + catpage + 'videos/'
        site.add_dir(name, catpage, 'List2', img)

    nextp = re.compile('class="next"><a href="/([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        page_link = nextp[0]
        page_nr = re.findall(r'\d+', page_link)[-1]
        site.add_dir('Next Page ({})'.format(page_nr), site.url + page_link, 'Pornstars', site.img_next)
    utils.eod()


@site.register()
def Studios(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'article>\s*<a href="([^"]+)".*?<h2>([^<]+)<.*?conunt">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name.strip())
        name = '{} [COLOR deeppink]{}[/COLOR]'.format(name, videos.strip())
        catpage = site.url + catpage + 'videos/'
        site.add_dir(name, catpage, 'List2', '')
    utils.eod()

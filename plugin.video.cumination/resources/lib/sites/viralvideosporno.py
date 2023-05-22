'''
    Cumination
    Copyright (C) 2018 holisticdioxide

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

site = AdultSite('viralvideosporno', '[COLOR hotpink]Viral Videos Porno[/COLOR]', 'https://www.viralvideosporno.com/', 'vvp.jpg', 'viralvideosporno')


@site.register(default_mode=True)
def Main():
    '''
    Content is the same as Elreyx, with almost the same layout and English descriptions.
    Used functions are defined in elreyx.py
    '''
    site.add_dir('[COLOR hotpink]Full Movies[/COLOR]', site.url + 'peliculas/amateur', 'MList')
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'buscar-', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="notice".+?href="([^"]+)">([^<]+).+?src="([^"]+).+?tion">(.*?)</div', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, desc in match:
        if videopage.startswith('//'):
            videopage = 'https:' + videopage
        if img.startswith('//'):
            img = 'https:' + img
        name = utils.cleantext(name)
        desc = re.sub(r"<.+?>", "", desc, 0, re.MULTILINE)
        desc = utils.cleantext(desc)
        site.add_download_link(name, videopage, 'Playvid', img, desc)
    np = re.compile(r'''id="pagination".+?href=['"]([^'"]+)[^>]+>(?:<span.+?span>)?\s*&raquo''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nextp = np.group(1)
        if nextp.startswith('//'):
            nextp = 'https:' + nextp
        elif not nextp.startswith('http'):
            nextp = site.url + nextp
        page_number = re.search(r'.+[/-](\d+)[/.]?', nextp).group(1)
        site.add_dir('Next Page (' + page_number + ')', nextp, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    phtml = utils.getHtml(url, site.url)
    sources = re.compile(r'class="box\s.+?href="([^"]+)', re.DOTALL | re.IGNORECASE).findall(phtml)
    if utils.addon.getSetting("universal_resolvers") == "true":
        sources += re.compile(r'class="ocult".+?Enlaces"[^>]+>(?:<b>)?(.*?)(?:...)?<', re.DOTALL | re.IGNORECASE).findall(phtml)
    links = {}
    for link in sources:
        if vp.resolveurl.HostedMediaFile(link).valid_url():
            links[link.split('/')[2]] = link
    videourl = utils.selector('Select link', links)
    if not videourl:
        vp.progress.close()
        return
    vp.play_from_link_to_resolve(videourl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)

    match = re.compile(r'href="([^"]+)"\s*title="Ver.+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match[1:]:
        name = utils.cleantext(name)
        if catpage.startswith('//'):
            catpage = 'https:' + catpage
        site.add_dir(name, catpage, 'List', '')

    utils.eod()


@site.register()
def MList(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="portada.+?href="([^"]+).+?src="([^"]+).+?titles">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        if videopage.startswith('//'):
            videopage = 'https:' + videopage
        if img.startswith('//'):
            img = 'https:' + img
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)
    np = re.compile(r'''id="pagination".+?href='([^']+)[^>]+>(?:<span.+?span>)?\s*&raquo''', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nextp = re.findall('(.+/)', url)[0] + np.group(1)
        page_number = np.group(1).split('_')[-1]
        site.add_dir('Next Page (' + page_number + ')', nextp, 'MList', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title + '.html'
        List(searchUrl)

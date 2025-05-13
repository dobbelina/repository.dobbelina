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

site = AdultSite('javgg', '[COLOR hotpink]JavGG[/COLOR]', 'https://javgg.co/', 'https://javgg.co/javggclub.png', 'javgg')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'tags', 'Cats', site.img_cat)
    site.add_dir('[COLOR hotpink]Trending[/COLOR]', site.url + 'trending/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Featured[/COLOR]', site.url + 'featured/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'genre-list/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'new-post/page/1/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')

    delimiter = '<article'
    re_videopage = 'href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = 'img src="([^"]+)"'

    contextmenu = []
    contexturl = (utils.addon_sys + "?mode=javgg.Lookupinfo&url=")
    contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))
    utils.videos_list(site, 'javgg.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, contextm=contextmenu)

    np = re.compile(r'''class="pagination".+?href=["']([^"']+)["']><i\s*id=['"]next''').search(listhtml)
    if np:
        p = re.compile(r'''class="pagination"><span>([^<]+)''').search(listhtml)
        pgtxt = p.group(1) if p else ''
        site.add_dir('Next Page...  ({0})'.format(pgtxt), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex='"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    eurls = re.compile(r'''<iframe[^<]+?src='([^']+)''').findall(videopage)
    sources = {}
    for eurl in eurls:
        if vp.resolveurl.HostedMediaFile(eurl):
            sources.update({eurl.split('/')[2]: eurl})
    videourl = utils.selector('Select Hoster', sources)
    vp.play_from_link_to_resolve(videourl)


@site.register()
def Cats(url):
    match = [
        ('Random', 'random/'),
        ('HD Uncensored', 'tag/hd-uncensored/'),
        ('Uncensored Leak', 'tag/uncensored-leak/'),
        ('Decensored', 'tag/decensored/'),
        ('Censored', 'tag/censored/'),
        ('Chinese Subtitle', 'tag/chinese-subtitle/'),
        ('English Subtitle', 'tag/english-subtitle/'),
    ]

    for name, catpage in match:
        site.add_dir(name, site.url + catpage, 'List', '')

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile('/(genre/[^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url + tagpage, 'List', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Genres", r'/(genre/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Maker", r'/(maker/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Label", r'/(label/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Director", r'/(director/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Cast", r'/(star/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'javgg.List', lookup_list)
    lookupinfo.getinfo()

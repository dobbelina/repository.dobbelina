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
from six.moves import urllib_parse
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import requests
import json

site = AdultSite('hdporn92', '[COLOR hotpink]Hdporn92[/COLOR]', 'https://hdporn92.com/', 'hdporn92.png', 'hdporn92')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', site.url + 'actors/', 'Categories', site.img_star)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_tags)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    if '>Nothing found</h1>' in listhtml:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?(?:poster|src)="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, img in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('hdporn92.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    add_next_page(listhtml, 'List')
    utils.eod()


def add_next_page(listhtml, mode):
    np = re.compile(r'class="pagination".+?class="current">\d+</a></li><li><a\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if not np:
        return
    next_url = np.group(1)
    page_number = next_url.split('/')[-2]
    cm_page = (utils.addon_sys
               + "?mode=" + str('hdporn92.GotoPage')
               + "&url=" + urllib_parse.quote_plus(next_url)
               + "&np=" + page_number
               + "&lp=0"
               + "&listmode=" + mode)
    cm = [('[COLOR deeppink]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
    site.add_dir('Next Page (' + page_number + ')', next_url, mode, site.img_next, contextm=cm)


@site.register()
def GotoPage(url, np, lp=0, listmode='List'):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        try:
            pg_num = int(pg)
            lp_num = int(lp)
        except (TypeError, ValueError):
            utils.notify(msg='Invalid page number!')
            return
        if pg_num < 1:
            utils.notify(msg='Invalid page number!')
            return
        if lp_num > 0 and pg_num > lp_num:
            utils.notify(msg='Out of range!')
            return
        if listmode not in ('List', 'Categories'):
            listmode = 'List'
        new_url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        if new_url == url:
            utils.notify(msg='Could not open that page')
            return
        contexturl = (utils.addon_sys + "?mode=" + "hdporn92." + listmode + "&url=" + urllib_parse.quote_plus(new_url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    playhtml = utils.getHtml(url)
    match = re.compile(r'<iframe.+?src="([^"]+)"[^>]+allowfullscreen', re.DOTALL | re.IGNORECASE).findall(playhtml)
    if match:
        link = match[0]
        if vp.resolveurl.HostedMediaFile(link):
            link = requests.head(link, allow_redirects=True, verify=False).url
            vp.play_from_link_to_resolve(link)
            return
        else:
            embedhtml = utils.getHtml(link, url)
            unpacked = utils.get_packed_data(embedhtml)
            jsondata = unpacked.split('var links=')[1].split('}')[0] + '}'
            jsondata = json.loads(jsondata)
            videolink = jsondata.get('hls2', '')
            if videolink:
                vp.play_from_direct_link(videolink)
            return
    else:
        utils.notify('Oh Oh', 'No Videos found')


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
    listhtml = utils.getHtml(url)
    match = re.compile(r'<article.+?href="([^"]+)"\s*title="([^"]+).+?(?:poster|src)="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip())
        site.add_dir(name, catpage + '?filter=latest', 'List', img)

    add_next_page(listhtml, 'Categories')
    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('com/(tag/[^"]+)".*?aria-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name.strip())
        site.add_dir(name, site.url + tagpage + '?filter=latest', 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'(category/[^"]+)"\s*?class="label"\s*?title="([^"]+)"', ''),
        ("Model", r'(actor/[^"]+)"\s*?title="([^"]+)"', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'hdporn92.List', lookup_list)
    lookupinfo.getinfo()

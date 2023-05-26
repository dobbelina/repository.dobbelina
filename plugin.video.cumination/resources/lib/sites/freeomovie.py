"""
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
"""

import re
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('freeomovie', '[COLOR hotpink]FreeOMovie[/COLOR]', 'https://www.freeomovie.to/', 'freeomovies.png', 'freeomovie')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}?s='.format(site.url), 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('class="thumi">.+?href="([^"]+).+?title="([^"]+).+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('freeomovie.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    nextp = re.compile('rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        site.add_dir('Next Page... ({0})'.format(nextp.split('/')[-2]), nextp, 'List', site.img_next)

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
def Cat(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<li class="cat-item">.+?<a href="([^"]+)"[^>]?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'List', '', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", ['Categories:(.*?)<div class="clearfix">', '(category/[^"]+)"[^>]+>([^<]+)'], ''),
        ("Tag", '(tag/[^"]+)">([^<]+)', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'freeomovie.List', lookup_list)
    lookupinfo.getinfo()
    

@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=r'href="([^"]+)"\s*target="myIframe"', direct_regex=None)
    vp.play_from_site_link(url, url)

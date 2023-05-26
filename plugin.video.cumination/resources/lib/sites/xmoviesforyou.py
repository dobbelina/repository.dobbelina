'''
    Ultimate Whitecream
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
import json
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xmoviesforyou', '[COLOR hotpink]Xmoviesforyou[/COLOR]', 'https://xmoviesforyou.com/', 'https://xmoviesforyou.com/wp-content/uploads/2018/08/logo.png', 'xmoviesforyou')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'wp-json/wp/v2/categories?page=1', 'Categories', site.img_cat)
    # site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'wp-json/wp/v2/tags?page=1', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'class="grid-box-img"><a href="([^"]+)" rel="bookmark" title="([^"]+)">.+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, img in match:
        name = name.replace('[', '[COLOR pink]').replace('] ', '[/COLOR] ')
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('xmoviesforyou.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)
    nextp = re.compile(r'class="next page-numbers"\s*href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        npage = re.findall(r'\d+', np)[-1]
        lastp = re.compile(r'>([^<]+)<[^"]+class="next page-numbers"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lpage = '/' + lastp[0] if lastp else ""
        site.add_dir('Next Page ({}{})'.format(npage, lpage), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)


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
    catjson = json.loads(cathtml)
    jdata = []
    i = 0
    while i < 10 and len(catjson) > 0:
        i += 1
        jdata += catjson
        url = url.split('?page=')
        url[1] = str(int(url[1]) + 1)
        url = '?page='.join(url)
        cathtml = utils.getHtml(url, '')
        catjson = json.loads(cathtml)

    for category in jdata:
        name = '{} ([COLOR hotpink]{}[/COLOR])'.format(category['name'], category['count'])
        site.add_dir(name, category['link'], 'List', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", '(category/[^"]+)" rel="tag">([^<]+)', ''),
        ("Tag", '(tag/[^"]+)" rel="tag">([^<]+)', '')]

    lookupinfo = utils.LookupInfo(site.url, url, 'xmoviesforyou.List', lookup_list)
    lookupinfo.getinfo()


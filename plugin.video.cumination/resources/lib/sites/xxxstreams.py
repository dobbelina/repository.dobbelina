'''
    Cumination
    Copyright (C) 2016 Whitecream
    Copyright (C) 2016 anton40

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
from xbmc import executebuiltin
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xxxstreams', '[COLOR hotpink]XXX Streams (watch)[/COLOR]', 'https://xxxstreams.watch/', 'xxxstreams.png', 'xxxstreams')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Most popular searches[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    match = re.compile(r'data-id="\d+"\s*title="([^"]+)"\s*href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for name, videopage, img in match:
        name = utils.cleantext(name)
        sitename = name.split()[0]
        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('xxxstreams.Searchsite')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Search {}[/COLOR]'.format(sitename.strip()), 'RunPlugin(' + contexturl + ')'))
        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    nextp = re.compile(r"""'pages'>([^<]+).+?link"?\s*rel="next"\s*href="([^"]+)""", re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        site.add_dir('Next Page... (Currently in {0})'.format(nextp.group(1)), nextp.group(2), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile('<li><a href="([^"]+?)">([^<]+?)</a></li>').findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Searchsite(url):
    html = utils.getHtml(url, site.url)
    result = re.findall('(?si)<h4>Tags:</h4><a href="([^"]+?)" rel="tag">', html)[0]
    if result:
        contexturl = (utils.addon_sys
                      + "?mode=" + str('xxxstreams.List')
                      + "&url=" + urllib_parse.quote_plus(result))
        executebuiltin('Container.Update(' + contexturl + ')')
    else:
        utils.notify('Notify', 'No site tag found for this video')
        return


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)

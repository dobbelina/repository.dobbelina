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
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('taboofantazy', '[COLOR hotpink]TabooFantazy[/COLOR]', 'https://www.taboofantazy.com/', 'taboofantazy.png', 'taboofantazy')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    html = listhtml.split('>SHOULD WATCH<')[0]
    match = re.compile(r'video-uid="\d*?".*?href="([^"]+)"\s*title="([^"]+)">.*?data-src="([^"]+)"(.*?)</span', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        for videourl, name, img, hd in match:
            name = utils.cleantext(name)
            hd = 'HD' if 'HD' in hd else ''

            contextmenu = []
            contexturl = (utils.addon_sys
                          + "?mode=" + str('taboofantazy.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videourl))
            contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

            site.add_download_link(name, videourl, 'Play', img, name, contextm=contextmenu, quality=hd)

    re_npurl = 'href="([^"]+)"[^>]*>Next' if '>Next' in html else 'class="current".+?href="([^"]+)"'
    re_npnr = r'/page/(\d+)[^>]*>Next' if '>Next' in html else r'class="current".+?rel="follow">(\d+)<'
    re_lpnr = r'/page/(\d+)[^>]*>Last' if '>Last' in html else r'rel="follow">(\d+)<\D+<\/main>'
    utils.next_page(site, 'taboofantazy.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='taboofantazy.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'article\s+id="post.+?href="([^"]+)"\s+title="([^"]+)".+?src="([^"]+)"\s+class', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name, img in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', img)
    match = re.compile(r'class="current">\d+<.+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if match and '/categories/' in match[0]:
        site.add_dir('[COLOR hotpink]Next Page[/COLOR]', match[0], 'Cat', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='data-wpfc-original-src="([^"]+)"')
    vp.play_from_site_link(url)


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url, url)
    match = re.compile('/(tag/[^"]+)".*?aria-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url + tagpage, 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'(category/[^"]+)"\s*class="label"\s*title="([^"]+)"', ''),
        ("Tag", r'(tag/[^"]+)"\s*class="label"\s*title="([^"]+)"', ''),
        ("Actor", r'(actor[^"]+)"\s*title="([^"]+)"', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'taboofantazy.List', lookup_list)
    lookupinfo.getinfo()

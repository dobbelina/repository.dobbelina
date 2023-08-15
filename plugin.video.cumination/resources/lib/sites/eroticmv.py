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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('eroticmv', "[COLOR hotpink]EroticMV[/COLOR]", 'http://eroticmv.com/', 'https://eroticmv.com/wp-content/uploads/2019/10/logo-2.png', 'eroticmv')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'category/decades/?archive_query=latest')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if '<h1 class="archive-title h2 extra-bold">' in html:
        html = html.split('<h1 class="archive-title h2 extra-bold">')[-1]
    else:
        html = html.split('">Related videos</h3>')[-1]
    if 'nothing matched your search terms' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<article id="post-'
    re_videopage = 'data-hyperlink="([^"]+)"'
    re_name = r'\stitle="([^"]+)"'
    re_img = 'src="([^"]+.jpg)"'
    utils.videos_list(site, 'eroticmv.Playvid', html, delimiter, re_videopage, re_name, re_img, contextm='eroticmv.Related')

    re_npurl = r'href="([^"]+)">&raquo;<'
    re_npnr = r'href="[^"]+/page/(\d+)/[^"]*">&raquo;<'
    re_lpnr = r"<span class='pages'>Page \d+ of (\d+)<"
    utils.next_page(site, 'eroticmv.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='eroticmv.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}/'.format(np), '/page/{}/'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('eroticmv.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'(https://eroticmv.com/category/genre/[^"]+)">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r'source src=\s*"([^"]+)"')
    vp.play_from_site_link(url)

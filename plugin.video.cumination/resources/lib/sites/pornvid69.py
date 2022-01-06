'''
    Cumination
    Copyright (C) 2022 Team Cumination

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

site = AdultSite('pornvid69', '[COLOR hotpink]Pornvid69[/COLOR]', 'https://pornvid69.com/', 'pornvid69.png', 'pornvid69')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    if '0 videos found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = 'data-post-id="'
    re_videopage = 'href="([^"]+)" title'
    re_name = 'title="([^"]+)"'
    re_img = 'data-src="([^"]+)"'
    re_duration = r'duration">([\d:]+)<'
    utils.videos_list(site, 'pornvid69.Playvid', html, delimiter, re_videopage, re_name=re_name, re_img=re_img, re_duration=re_duration, contextm='pornvid69.Related')

    re_npurl = 'href="([^"]+)">&raquo;<'
    re_npnr = r'/(\d+)/[^"]*">&raquo;<'
    re_lpnr = r'>(\d+)<\D+next page-link'
    utils.next_page(site, 'pornvid69.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='pornvid69.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page/{}'.format(np), 'page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornvid69.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url).replace("'", '"')
    match = re.compile(r'class="col-6.+?href="([^"]+)"\s*title="([^"]+)".+?data-src="([^"]+)".+?video-datas">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, img, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({})[/COLOR]'.format(count.strip())
        site.add_dir(name, caturl, 'List', img)
    if 'aria-label="Posts navigation"' in cathtml:
        re_npurl = 'href="([^"]+)">&raquo;<'
        re_npnr = r'/(\d+)/[^"]*">&raquo;<'
        re_lpnr = r'>(\d+)<\D+next page-link'
        utils.next_page(site, 'pornvid69.Categories', cathtml, re_npurl, re_npnr=re_npnr, re_lpnr=re_lpnr, contextm='pornvid69.GotoPage')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex='<source src="([^"]+)"')
    vp.play_from_site_link(url)

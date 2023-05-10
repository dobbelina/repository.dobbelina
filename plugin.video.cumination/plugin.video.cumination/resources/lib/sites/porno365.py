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

site = AdultSite('porno365', "[COLOR hotpink]Porno365[/COLOR]", 'http://m.porno365.pics/', 'http://m.porno365.pics/settings/l8.png', 'porno365')
porn365_headers = utils.base_hdrs.copy()
porn365_headers.update({'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'})


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'models', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?q=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url, headers=porn365_headers)
    if '404 :(</h1>' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    html = html.split('class="related_video trailer"', 1)[1] if 'class="related_video trailer"' in html else html
    delimiter = '<li id="'
    re_videopage = 'class="image" href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = 'img src="([^"]+)"'
    re_duration = '<span class="duration">([^<]+)<'
    utils.videos_list(site, 'porno365.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='porno365.Related')

    re_npurl = r'class="next_link"\s*href="([^"]+)"'
    re_npnr = r'class="next_link"\s*href="[^"]+/(\d+)"'
    # re_lpnr = r'>(\d+)<[^"]+"[^"]+"\s*class="prevnext"'
    utils.next_page(site, 'porno365.List', html, re_npurl, re_npnr, contextm='porno365.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}'.format(np), '/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('porno365.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}=".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, headers=porn365_headers)
    match = re.compile(r'class="categories-list-div".+?href="([^"]+)".+?img src="([^"]+)".+?alt="([^"]+)".+?class="text">(\d+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({} videos)[/COLOR]'.format(count)
        caturl = utils.fix_url(caturl, site.url)
        img = utils.fix_url(img, site.url)
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, headers=porn365_headers)
    match = re.compile(r'class="item_model".+?href="([^"]+)".+?src="([^"]+)".+?class="cnt_span">(\d+)<.+?class="model_eng_name">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, count, name in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({} videos)[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', img)
    re_npurl = r'class="next_link" href="([^"]+)"'
    re_npnr = r'class="next_link" href="[^"]+/(\d+)"'
    utils.next_page(site, 'porno365.Models', cathtml, re_npurl, re_npnr, contextm='porno365.GotoPage')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex='meta property="og:video" content="([^"]+)">')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url, headers=porn365_headers)
    vp.play_from_html(videohtml)

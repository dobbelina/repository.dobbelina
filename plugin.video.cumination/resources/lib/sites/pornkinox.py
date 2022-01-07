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

site = AdultSite('pornkinox', '[COLOR hotpink]Pornkinox[/COLOR]', 'https://pornkinox.to/', 'https://pornkinox.to/wp-content/uploads/2018/07/logo.png', 'pornkinox')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url)
    if '>Nichts gefunden!<' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = 'article id="post'
    re_videopage = 'href="([^"]+)" title'
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+)"'
    utils.videos_list(site, 'pornkinox.Playvid', html, delimiter, re_videopage, re_name, re_img, contextm='pornkinox.Related')

    re_npurl = r'class="next page-numbers" href="([^"]+)"'
    re_npnr = r'class="next page-numbers" href="[^"]+?/page/(\d+)'
    re_lpnr = r'>(\d+)<[^=]+class="next page-numbers"'
    utils.next_page(site, 'pornkinox.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='pornkinox.GotoPage')
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
def ListRelated(url):
    html = utils.getHtml(url, site.url)
    delimiter = '><li><a '
    re_videopage = r'href="([^"]+)"\s*class="crp_link'
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+)"'
    utils.videos_list(site, 'pornkinox.Playvid', html.split('>Schaue auch:<')[-1], delimiter, re_videopage, re_name, re_img, contextm='pornkinox.Related')
    utils.eod()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornkinox.ListRelated') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    cathtml = cathtml.split('>Kategorien<')
    match = re.compile(r'class="cat-item.+?href="([^"]+)".+?>([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml[-1])
    for caturl, name in match:
        site.add_dir(name, caturl, 'List', '')
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
    vp = utils.VideoPlayer(name, download, regex='<a href="([^"]+)" target="_blank"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    vp.play_from_html(videohtml)

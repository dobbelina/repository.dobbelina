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

site = AdultSite('ividz', '[COLOR hotpink]Ividz[/COLOR]', 'https://www.incestvidz.com/', 'ividz.png', 'ividz')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', '', '')
    # site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tag', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?orderby=date')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)

    if 'Sorry, but nothing matched your search terms' in listhtml:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<article id="post'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+)"'
    re_duration = 'class="duration">([^<]+)<'
    skip = 'I like this'
    utils.videos_list(site, 'ividz.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='ividz.Related', skip=skip)

    re_npurl = r'class="current">\d+</a></li><li><a href="([^"]+)"'
    re_npnr = r'class="current">\d+</a></li><li><a href="[^"]+" class="inactive">(\d+)<'
    re_lpnr = r'page/(\d+)/[^>]*>Last<'
    utils.next_page(site, 'ividz.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='ividz.GotoPage')
    utils.eod()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('ividz.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


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
def Cat(url):

    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'article id="post.+?href="([^"]+)" title="([^"]+)".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in match:
        name = utils.cleantext(name)
        site.add_dir(name, catpage + '?orderby=date', 'List', img)
    utils.eod()


@site.register()
def Tag(url):
    taghtml = utils.getHtml(url, site.url)
    match = re.compile('/(tag[^ ]+/).*?label="([^"]+)"').findall(taghtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url + tagpage + '?orderby=date', 'List', '')

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+') + '&orderby=date'
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex=r"""<iframe[.\n]*.*?src\s*=\s*?["']*?([^'" ]+)""")
    vp.play_from_site_link(url)

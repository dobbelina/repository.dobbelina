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

import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hitprn', '[COLOR hotpink]Hitprn[/COLOR]', 'https://www.hitprn.net/', 'https://hitprn.net/wp-content/uploads/2025/02/hitprn-logo.png', 'hitprn')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1/?filter=latest')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if 'It looks like nothing was found for this search' in listhtml:
        utils.notify(msg='No videos found!')
        return

    delimiter = r'<article data-video-id="video'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = r'src="([^"]+)"'
    re_duration = r'fa-clock-o"></i>\D*([^<]+)</span>'
    skip = 'Terms of Use'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('hitprn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('hitprn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'hitprn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, skip=skip, contextm=cm)

    re_npurl = r'class="current">[^=]+?href="([^"]+)"'
    re_npnr = r'class="current">.+?class="inactive">(\d+)<'
    re_lpnr = r'/page/(\d+)/[^"]*">Last<'
    utils.next_page(site, 'hitprn.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='hitprn.GotoPage')
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
    contexturl = (utils.addon_sys + "?mode=" + str('hitprn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    html = utils.getHtml(url, site.url)
    vp.play_from_html(html, url)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Pornstar", r'/(actor/[^"]+)" class="label" title="([^"]+)"', ''),
        ("Tag", r'/(tag/[^"]+)" class="label" title="([^"]+)"', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'hitprn.List', lookup_list)
    lookupinfo.getinfo()

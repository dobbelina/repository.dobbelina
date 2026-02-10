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

import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xmoviesforyou', '[COLOR hotpink]Xmoviesforyou[/COLOR]', 'https://xmoviesforyou.com/', 'https://xmoviescdn.online/2018/08/logo.png', 'xmoviesforyou')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?q=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')

    delimiter = r'<article class="group'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = r'<img src="([^"]+)"'
    re_quality = '">(HD)</span>'
    skip = 'class="th-title"'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('xmoviesforyou.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))

    utils.videos_list(site, 'xmoviesforyou.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_quality=re_quality, skip=skip, contextm=cm)

    re_npurl = '<a href="([^"]+)"[^>]+>Next<'
    re_npnr = r'page=(\d+)"[^>]+>Next</a>'
    re_lpnr = r'of (\d+)\s+</span>\s+<a href'
    utils.next_page(site, 'xmoviesforyou.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='xmoviesforyou.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + "xmoviesforyou.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


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
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'(category/[^"]+)".+?>category</span>([^<]+)<', ''),
        ("Tag", r'(tag/[^"]+)"[^>]+?>([^<]+)', '')]

    lookupinfo = utils.LookupInfo(site.url, url, 'xmoviesforyou.List', lookup_list)
    lookupinfo.getinfo()

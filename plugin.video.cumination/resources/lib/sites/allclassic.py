"""
    Cumination site scraper
    Copyright (C) 2026 Team Cumination

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
"""

import re
from six.moves import urllib_parse
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite('allclassic', '[COLOR hotpink]AllClassic.Porn[/COLOR]', 'https://allclassic.porn/', 'https://allclassic.porn/images/logo.png', 'allclassic')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    List(site.url + 'page/1/')
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception:
        utils.notify(msg='No videos found!')
        return
    if 'No videos found ' in listhtml:
        utils.notify(msg='No videos found!')
        return

    delimiter = r'<a class="th item"'
    re_videopage = 'href="([^"]+)"'
    re_name = 'class="th-description">([^<]+)<'
    re_img = r'img src="([^"]+)"'
    re_duration = r'la-clock-o"></i>([\d:]+)<'
    skip = 'class="th-title"'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('allclassic.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('allclassic.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'allclassic.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, skip=skip, contextm=cm)

    re_npurl = 'class="active">.+?href="/([^"]+)"'
    re_npnr = r'class="active">.+?href="[^"]+">0*(\d+)<'
    utils.next_page(site, 'allclassic.List', listhtml, re_npurl, re_npnr, contextm='allclassic.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + "allclassic.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    vpage = utils.getHtml(url, site.url)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url.format(keyword.replace(' ', '-')))


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="th" href="([^"]+)".+?img src="([^"]+)" alt="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actor", r'btn-small" href="{}(models/[^"]+)"\s*itemprop="actor">([^<]+)<'.format(site.url), ''),
        ("Studio", r'btn-small" href="{}(studios/[^"]+)">([^<]+)<'.format(site.url), ''),
        ("Category", r'btn-small" href="{}(categories/[^"]+)"\s*itemprop="genre">([^<]+)<'.format(site.url), ''),
        ("Tag", r'btn-small" href="{}(tags/[^"]+)"\s*itemprop="keywords">([^<]+)<'.format(site.url), '')]
    lookupinfo = utils.LookupInfo(site.url, url, 'allclassic.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('allclassic.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

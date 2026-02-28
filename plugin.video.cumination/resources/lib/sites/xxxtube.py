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

site = AdultSite('xxxtube', '[COLOR hotpink]X-X-X Video[/COLOR]', 'https://x-x-x.tube/', 'xxxtube.png', 'xxxtube')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    List(site.url + 'videos/?by=post_date')
    utils.eod()


@site.register()
def List(url):
    if '/videos/' not in url and ('/categories/' in url or '/tags/' in url or '/models/' in url):
        url += 'videos/?by=post_date'
    listhtml = utils.getHtml(url)
    if 'class="buttons flex"' not in listhtml and 'Related Videos' not in listhtml:
        utils.notify(msg='No videos found!')
        return

    delimiter = r'class="thumb-inner"'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = r'data-original="([^"]+)"'
    re_duration = r'class="duration">\s*([\d:]+)\s*<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('xxxtube.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('xxxtube.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'xxxtube.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    re_npurl = 'class="item active">.+?href="/([^"]+)"'
    re_npnr = r'class="item active">.+?href="[^"]+">(\d+)<'
    re_lpnr = r'>(\d+)</a>\s+</li>\s+<li class="item pager">'
    utils.next_page(site, 'xxxtube.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='xxxtube.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + "xxxtube.List&url=" + urllib_parse.quote_plus(url))
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
def Lookupinfo(url):
    lookup_list = [
        ("Actor", r'<a href="{}(models/([^"]+)/)" class="btn">\s*View Model\s*<'.format(site.url), ''),
        ("Category", r'<a class="btn" href="{}(categories/[^"]+)">([^<]+)<'.format(site.url), ''),
        ("Tag", r'<a class="btn" href="{}(tags/[^"]+)">([^<]+)<'.format(site.url), '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'xxxtube.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('xxxtube.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

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
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite('premiumporn', '[COLOR hotpink]PremiumPorn[/COLOR]', 'https://premiumporn.org/', 'premiumporn.png', 'premiumporn')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', site.url + 'actors/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'video/page/1/?rawx_per_page=24')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, error=True)
    if 'It looks like nothing was found for this search' in listhtml:
        utils.notify('No results found', 'Try a different search term')
        return

    delimiter = 'data-post-id="'
    re_videopage = 'href="([^"]+)"'
    re_name = '"vc-title">([^<]+)<'
    re_img = 'src="([^"]+)"'
    re_duration = '"vc-dur">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=premiumporn.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    # cm_related = (utils.addon_sys + "?mode=premiumporn.Related&url=")
    # cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'premiumporn.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    re_npurl = r'class="page-numbers current".+?href="([^"]+)"'
    re_npnr = r'class="page-numbers current".+?href="[^"]+"[^>]*>(\d+)<'
    re_lpnr = r'>(\d+)</a>\s+<a class="next page-numbers"'

    utils.next_page(site, 'premiumporn.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='premiumporn.GotoPage')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a href="([^"]+)" class=".+?src="([^"]+)".+?alt="([^"]+)".+?">(\d+) VIDEOS<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for siteurl, img, name, videos in match:
        name = utils.cleantext(name) + '[COLOR hotpink] (' + videos + ' videos)[/COLOR]'
        site.add_dir(name, siteurl, 'List', img)
    match = re.search(r'class="page-numbers current".+?href="([^"]+)"', cathtml, re.IGNORECASE | re.DOTALL)
    if match:
        site.add_dir('Next Page', match.group(1), 'Categories', site.img_next)
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
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)

    html = utils.getHtml(url)
    match = re.compile(r'data-src="([^"]+)"\s+data-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if match:
        src = {m[1]: m[0] for m in match}
        embed_url = utils.selector("Select host", src)
        if embed_url:
            vp.play_from_link_to_resolve(embed_url)
    else:
        utils.notify('Oh oh', 'No video found')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('premiumporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actors", r'<a href="(https://premiumporn.org/actor/[^/]+/)" class="si-actor-card">.+?class="si-actor-name">([^<]+)</span>', ''),
        ("Tags", r'<a href="(https://premiumporn.org/tag/[^"]+)" class="v-tag">([^<]+)<', ''),
        # ("Studios", r'<a href="(https://premiumporn.org/[^/]+/)" title="([^"]+)">', ''),
    ]
    lookupinfo = utils.LookupInfo('', url, 'premiumporn.List', lookup_list)
    lookupinfo.getinfo()

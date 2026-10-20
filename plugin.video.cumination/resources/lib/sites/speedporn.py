'''
    Cumination
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
'''

import re
import json
import html as html_lib
import xbmc
import xbmcgui

from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite('speedporn', '[COLOR hotpink]SpeedPorn[/COLOR]', 'https://speedporn.net/', 'https://i0.wp.com/speedporn.net/wp-content/uploads/2026/10/speedpornlogo.png', 'speedporn')


@site.register(default_mode=True)
def Main():
    for title, path in (
        ('Genres', 'watch-free-moivies-by-genres/'),
        ('Studios', 'watch-free-moivies-by-studios/'),
        ('Years', 'watch-free-moivies-by-release-years/'),
        ('Directors', 'watch-free-moivies-by-Directors/'),
    ):
        site.add_dir(f'[COLOR hotpink]{title}[/COLOR]', site.url + path, 'Category', site.img_cat)

    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    site.add_dir(f'[COLOR hotpink]Pornstars[/COLOR]', site.url + path, 'Category', site.img_star)
    List(site.url + 'all-movies/')
    utils.eod()


@site.register()
def Category(url):
    page = utils.getHtml(url, '')

    match = re.compile(r'class="tcard" href="([^"]+)">.+?<img src="([^"]+)" alt="([^"]+)".+?<small>([^<]+)</small>', re.DOTALL | re.IGNORECASE).findall(page)
    if not match:  # years
        match = re.compile(r'class="tcard" href="([^"]+)"()><b>([^<]+)</b><small>([^<]+)</small>', re.DOTALL | re.IGNORECASE).findall(page)
    if not match:  # genres
        match = re.compile(r'class="chip" href="([^"]+)"()>([^<]+)<small>([^<]+)</small>', re.DOTALL | re.IGNORECASE).findall(page)

    for link, img, title, count in match:
        title = utils.cleantext(title) + ' [COLOR deeppink](' + utils.cleantext(count) + ')[/COLOR]'
        site.add_dir(title, link, 'List', img)

    next_match = re.search(r'<a\b(?=[^>]*\bclass=["\'][^"\']*\bnext\b)[^>]*\bhref=["\']([^"\']+)["\']', page, re.DOTALL | re.IGNORECASE)
    if next_match:
        site.add_dir('[COLOR hotpink]Next Page[/COLOR]', next_match.group(1), 'Category', site.img_next)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')

    delimiter = 'class="card__th"'
    re_videopage = 'href="([^"]+)"'
    re_name = '>([^<]+)</a></h'
    re_img = 'src="([^"]+)"'
    re_duration = r'class="card__dur">([\d:]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('speedporn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('speedporn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'speedporn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    re_npurl = r'class="page-numbers current".+?href="([^"]+)"'
    re_npnr = r'class="page-numbers current".+?href="[^"]+"[^>]*>([\d,]+)<'
    re_lpnr = r'>([\d,]+)</a>\s*<a class="next page-numbers"'
    utils.next_page(site, 'speedporn.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='speedporn.GotoPage')
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
    contexturl = (utils.addon_sys + "?mode=" + str('speedporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, '[CR]Loading video page[CR]')
    videopage = utils.getHtml(url)

    match = re.search(r'data-servers=["\']([^"\']*)["\']', videopage, re.IGNORECASE | re.DOTALL)
    if match:
        servers = json.loads(html_lib.unescape(match.group(1)))
        for server in servers:
            title = server.get('l', 'Server')
            src = server.get('u', '')
            if src:
                links[title] = src

    if not links:
        vp.progress.close()
        utils.notify(msg='SpeedPorn: no server links found')
        return

    videourl = utils.selector('Select server', links, setting_valid=False)
    if not videourl:
        vp.progress.close()
        return

    vp.progress.update(90, '[CR]Loading video page[CR]')
    vp.play_from_link_to_resolve(videourl)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ('Actor', '(pornstars/[^"]+)">([^<]+)</a>', ''),
        ('Director', '(directors/[^"]+)">([^<]+)</a>', ''),
        ('Genres', '(genres/[^"]+)">([^<]+)</a>', ''),
        ('Studio', '(director/[^"]+)">([^<]+)</a>', ''),
    ]
    utils.LookupInfo(site.url, url, 'speedporn.List', lookup_list).getinfo()

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('justfullporn', '[COLOR hotpink]Just Full Porn[/COLOR]', 'https://justfullporn.net/', 'https://justfullporn.net/wp-content/uploads/2024/12/cropped-Made_with_FlexClip_AI-2024-12-26T013132-removebg-preview.png', 'justfullporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')

    delimiter = 'data-post-id="'
    re_videopage = 'href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = 'data-src="([^"]+)"'

    contexturl = (utils.addon_sys + "?mode=justfullporn.Lookupinfo&url=")
    contextmenu = [('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')]
    utils.videos_list(site, 'justfullporn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, contextm=contextmenu)

    re_npurl = r'class="page-link current".+?href="([^"]+)"'
    re_npnr = r'class="page-link current".+?href="[^"]+">([\d,]+)<'
    re_lpnr = r'>([\d,]+)<\D+class="next page-link"'

    utils.next_page(site, 'justfullporn.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='justfullporn.GotoPage')
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
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = url + keyword.replace(' ', '+')
        List(searchUrl)


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'video-block-cat.+?href="([^"]+)"\s*title="([^"]+).+?(?:poster|src)="([^"]+).+?class="video-datas">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img, videos in match:  # in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip())
        name += ' [COLOR blue]' + videos.strip() + '[/COLOR]'
        site.add_dir(name, catpage, 'List', img)

    np = re.compile(r'class="next page-link" href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-1]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'Categories', site.img_next)

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile('class="tag-item"><a href="([^"]+)" title="[^"]+">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name.strip())
        site.add_dir(name, tagpage, 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'(category/[^"]+)"\s*?class="label"\s*?title="([^"]+)"', ''),
        ("Model", r'(tag/[^"]+)"\s*?class="label"\s*?title="([^"]+)"', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'justfullporn.List', lookup_list)
    lookupinfo.getinfo()

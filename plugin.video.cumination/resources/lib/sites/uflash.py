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
import json

site = AdultSite('uflash', '[COLOR hotpink]Uflash[/COLOR]', 'http://www.uflash.tv/', 'http://www.uflash.tv/templates/frontend/default/images/logo.png', 'uflash')


@site.register(default_mode=True)
def Main():
    # site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    # site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?search_type=videos&search_query=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    headers = {'User-Agent': 'iPad', 'Accept-Encoding': 'deflate'}
    html = utils._getHtml(url, headers=headers)
    if 'No videos found!' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = r'<li\s+style='
    re_videopage = 'href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = 'img src="([^"]+)"'
    re_duration = r'class="duration">[\s\t]*([\d:]+)'
    skip = 'adultfriendfinder.com'
    utils.videos_list(site, 'uflash.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, skip=skip)

    # re_npurl = r'href="([^"]+)"\s*class="prevnext">Next'
    # re_npnr = r'(\d+)"\s*class="prevnext">Next'
    # re_lpnr = r'>(\d+)</a></li><li><a[^>]+Next'
    # utils.next_page(site, 'uflash.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='uflash.GotoPage')
    site.add_dir('[COLOR hotpink]Show More...[/COLOR]', site.url, 'List', site.img_next)

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    headers = {'User-Agent': 'iPad', 'Accept-Encoding': 'deflate'}
    cathtml = utils.getHtml(url, headers=headers)
    cathtml = cathtml.split('CATEGORIES')[-1].split('THUMBS')[0]
    match = re.compile(r'<li><a href="([^"]+)".*?>([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    i = 0
    for caturl, name in match:
        i += 1
        caturl = site.url[:-1] + caturl
        if i < 5:
            name = '[Female videos] ' + name
        elif i < 9:
            name = '[Male videos] ' + name
        else:
            name = '[Top keywords] ' + name

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
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    headers = {'User-Agent': 'iPad', 'Accept-Encoding': 'deflate', 'X-Requested-With': 'XMLHttpRequest'}
    id = url.split('/')[4]
    data = {'vid': '{}'.format(id)}
    html = utils.getHtml(site.url + 'ajax/getvideo', url, headers=headers, data=data)
    jdata = json.loads(html)

    videourl = jdata["video_src"]
    vp.play_from_direct_link(videourl + '|Referer=' + url)

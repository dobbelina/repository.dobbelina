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
import time
from six.moves import urllib_parse
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite('asianviralhub', '[COLOR hotpink]AsianViralHub[/COLOR]', 'https://asianviralhub.com/', 'https://asianviralhub.com/contents/gfgaesewhgls/theme/logo.png', 'asianviralhub')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)

    if 'There is no data in this list.' in listhtml.split('<div id="list_albums')[0]:
        utils.notify(msg='No videos found!')
        return

    if url.startswith('{}video/'.format(site.url)):
        listhtml = listhtml.split('<span>Related Videos</span>')[-1]

    delimiter = r'<div class="item'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = r'data-original="([^"]+)"'
    re_duration = r'class="duration">([\d:]+)<'
    re_quality = r'class="is-hd">([^<]+)<'
    skip = 'private ">'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=asianviralhub.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin({})'.format(cm_lookupinfo)))
    cm_related = (utils.addon_sys + "?mode=asianviralhub.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin({})'.format(cm_related)))

    utils.videos_list(site, 'asianviralhub.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, skip=skip, contextm=cm)

    match = re.search(r'from:(\d+)">Last<.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">Next<', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        lpnr, block_id, params = match.groups()
        npage = params.split(':')[-1]
        params = params.replace(';', '&').replace(':', '=')
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, int(time.time() * 1000))
        nurl = nurl.replace('+from_albums', '')
        lastp = '/{}'.format(lpnr) if lpnr else ''
        cm_page = (utils.addon_sys + "?mode=asianviralhub.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&lp=" + str(lpnr))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, contextm=cm)
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
        contexturl = (utils.addon_sys + "?mode=" + "asianviralhub.List&url=" + urllib_parse.quote_plus(url))
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
def PLContextMenu():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    order = utils.selector('Select order', sort_orders)
    if order:
        utils.addon.setSetting('jbsortorder', order)
        xbmc.executebuiltin('Container.Refresh')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('asianviralhub.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actor", r'class="link" href="{}(models/[^"]+)">.+?</i>\s+([^<]+)\s+</span>'.format(site.url), ''),
        ("Category", r'<a class="btn-cat" href="{}(categories/[^"]+)">\s+([^<]+)\s+</a>'.format(site.url), ''),
        ("Tag", r'<a class="btn-tags" href="{}(tags/[^"]+)">\s+([^<]+)\s+</a>'.format(site.url), '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'asianviralhub.List', lookup_list)
    lookupinfo.getinfo()

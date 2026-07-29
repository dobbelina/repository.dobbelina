'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('pornez', '[COLOR hotpink]PorneZOO[/COLOR]', 'https://pornezoo.net', 'https://pornezoo.net/wp-content/uploads/2026/07/Pornezoo-logo.png', 'pornez')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    listhtml = listhtml.split('</main>')[0]

    delimiter = 'article data-video-id='
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+)"'
    re_duration = r'clock-o"></i>([\d:]+)<'
    re_quality = r'class="hd-video">([^<]+)<'

    cm = []
    cm_related = (utils.addon_sys + "?mode=pornez.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'pornez.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    re_npurl = r'<a class="current".+?href="([^"]+)"'
    re_npnr = r'<a class="current".+?href="[^>]+>(\d+)<'
    re_lpnr = r'page/(\d+)/[^"]*">Last<'

    utils.next_page(site, 'pornez.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='pornez.GotoPage')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornez.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    videohtml = utils.getHtml(url)
    match = re.compile(r'<iframe[^>]+src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if not match:
        return
    playerurl = match[0]
    if vp.resolveurl.HostedMediaFile(playerurl):
        vp.play_from_link_to_resolve(playerurl)
    else:
        playerhtml = utils.getHtml(playerurl, url)
        match = re.compile(r'source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(playerhtml)
        # videos = {}
        # for m in match:
        #     videos[m[1]] = m[0]
        # videourl = utils.prefquality(videos, sort_by=lambda x: int(x[:-1]), reverse=True)
        videourl = match[0]
        if videourl:
            vp.play_from_direct_link(videourl)

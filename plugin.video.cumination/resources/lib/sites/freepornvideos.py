'''
    Cumination
    Copyright (C) 2025 Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc
import xbmcgui


site = AdultSite('freepornvideos', '[COLOR hotpink]FreePornVideos[/COLOR]', 'https://www.freepornvideos.xxx/', 'freepornvideos.png', 'freepornvideos')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{}/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if 'There is no data in this list.' in listhtml:
        utils.notify(msg='No videos found!')
        return
    listhtml = listhtml.replace('<div class="k4">', '<div class="FHD">')

    delimiter = r'<div class="item">\s*?<a'
    re_videopage = 'href="([^"]+)" target'
    re_name = 'title="([^"]+)"'
    re_img = r'src="([^"]+\.jpg)"'
    re_duration = r'class="duration">\D*([^<]+)<'
    re_quality = '<div class="(FHD)">'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('freepornvideos.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('freepornvideos.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'freepornvideos.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    re_npurl = r'class="page-current">.+?class="page"><a href="([^"]+)">\d+<'
    re_npnr = r'class="page-current">.+?class="page"><a href="[^"]+">(\d+)<'
    re_lpnr = r'/(\d+)/">Last<'
    utils.next_page(site, 'freepornvideos.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='freepornvideos.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'/\d+/$', r'/{}/'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "freepornvideos.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url.format(keyword.replace(' ', '-')))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    match = re.compile(r"<source\s+src='([^']+)'[^>]+?label=\"([^\"]+)\"", re.DOTALL | re.IGNORECASE).findall(videopage)
    sources = {}
    if match:
        for videourl, quality in match:
            quality = '1080p' if quality == '2160p' else quality
            sources[quality] = videourl
        videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
        if videourl:
            vp.progress.update(75, "[CR]Video found[CR]")
            vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Channel", r'<a class="btn_sponsor" href="https://www.freepornvideos.xxx/(sites/[^"]+)">([^<]+)<', ''),
        ("Pornstar", r'<a class="btn_model" href="https://www.freepornvideos.xxx/(models/[^"]+)">([^<]+)<', ''),
        ("Network", r'<a class="btn_sponsor_group" href="https://www.freepornvideos.xxx/(networks/[^"]+)">([^<]+)<', ''),
        ("Tags", r'<a class="btn_tag" class="link" href="https://www.freepornvideos.xxx/(categories/[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'freepornvideos.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('freepornvideos.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

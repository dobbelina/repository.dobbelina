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


site = AdultSite('longvideos', '[COLOR hotpink]LongVideos.xxx[/COLOR]', 'https://www.longvideos.xxx/', 'longvideos.png', 'longvideos')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{}/relevance/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if 'There is no data in this list.' in listhtml:
        utils.notify(msg='No videos found!')
        return
    listhtml = listhtml.replace('<div class="k4">', '<div class="FHD">')

    delimiter = '<div class="item"'
    re_videopage = '<a href="({}[^"]+)"'.format(site.url + 'videos/')
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+jpg)"'
    re_duration = r'"duration">\D*([^<]+)\D*<'
    re_quality = '<div class="(FHD)">'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('longvideos.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('longvideos.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'longvideos.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    re_npurl = 'aria-label="Next" href="([^"]+)"'
    re_npnr = r'aria-label="Next" href="[^"]+/(\d+)/"'
    re_lpnr = r'/(\d+)/">[^<]+</a></li>\s*<li class="next"'
    utils.next_page(site, 'longvideos.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='longvideos.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + "longvideos.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url.format(keyword.replace(' ', '-')))


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<a\s+class="item"\shref="([^"]+)"\stitle="([^"]+)">', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'<source\s+src=[\'"]([^\'"]+)[\'"][^>]*type=[\'"]video/mp4[\'"][^>]*label=[\'"]([^\'"]+)[\'"]', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if match:
        sources = {v[1].replace('2160p', '1080p'): v[0] for v in match}
        vp.progress.update(50, "[CR]Loading video[CR]")
        videourl = utils.prefquality(sources, sort_by=lambda x: int(x[:-1]), reverse=True)
        if videourl:
            vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Channel", r'href="https://www.longvideos.xxx/(sites[^"]+)">([^<]+)<', ''),
        # ("Network", r'href="https://www.longvideos.xxx/(networks[^"]+)">([^<]+)<', ''),
        # ("Categories", r'href="https://www.longvideos.xxx/(categories[^"]+)">([^<]+)<', ''),
        ("Models", r'href="https://www.longvideos.xxx/(models[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'longvideos.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('longvideos.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

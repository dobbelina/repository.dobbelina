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


site = AdultSite('cloudbate', '[COLOR hotpink]Cloudbate[/COLOR]', 'https://www.cloudbate.com/', 'cloudbate.png', 'cloudbate')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Girls[/COLOR]', site.url + 'categories/girls/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Trans[/COLOR]', site.url + 'categories/trans/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Couples[/COLOR]', site.url + 'categories/couples/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search (models)[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    listhtml = listhtml.split('>Popular Videos<')[0]

    if 'There is no data in this list.' in listhtml.split('class="thumbs albums-thumbs')[0]:
        utils.notify(msg='No videos found!')
        return

    delimiter = r'<div class="video-block'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = r'data-webp="([^"]+)"'
    re_duration = r'class="duration">([\d:]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=cloudbate.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin({})'.format(cm_lookupinfo)))
    cm_related = (utils.addon_sys + "?mode=cloudbate.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin({})'.format(cm_related)))
    utils.videos_list(site, 'cloudbate.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm, thumbnails=True)

    re_npurl = 'class="next page-link" href="([^"]+)"'
    re_npnr = r'class="next page-link"[^>]*:(\d+)">'
    re_lpnr = r'>(\d+)</a>\s+</li>\s+<li class="page-item">\s+<a class="next page-link"'
    utils.next_page(site, 'cloudbate.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='cloudbate.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'/0*{}/'.format(np), r'/{}/'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "cloudbate.List&url=" + urllib_parse.quote_plus(url))
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
    def SrcList(url):
        listhtml = utils.getHtml(url, site.url)
        match = re.compile(r'<li class="lists">\s*<a href="([^"]+)" title="([^"]+)">', re.IGNORECASE | re.DOTALL).findall(listhtml)
        if not match:
            utils.notify(msg='No models found!')
            return ''
        sources = {}
        for url, name in match:
            sources[name] = url
        if sources:
            model = utils.selector("Select Model", sources)
            if model:
                List(model)

    if not keyword:
        site.search_dir(url, 'Search')
    else:
        SrcList(url.format(keyword.replace(' ', '-')))


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('cloudbate.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Model", r'href="{}(models/[^"]+)">([^<]+)<'.format(site.url), ''),
        ("Category", r'href="{}(categories/[^"]+)">([^<]+)<'.format(site.url), ''),
        ("Tag", r'href="{}(tags/[^"]+)">([^<]+)</a>'.format(site.url), '')]
    lookupinfo = utils.LookupInfo(site.url, url, 'cloudbate.List', lookup_list)
    lookupinfo.getinfo()

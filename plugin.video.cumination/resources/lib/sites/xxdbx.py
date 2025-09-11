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


site = AdultSite('xxdbx', '[COLOR hotpink]xxdbx[/COLOR]', 'https://xxdbx.com/', 'https://xxdbx.com/l.png', 'xxdbx')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if '&ndash; 0 videos &ndash;' in listhtml:
        utils.notify(msg='No videos found!')
        return

    delimiter = '<div class="v">'
    re_videopage = '<a href="([^"]+)">'
    re_name = 'class="v_title">([^<]+)<'
    re_img = 'src="(//[^"]+)"'
    re_duration = r'class="v_dur">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('xxdbx.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('xxdbx.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'xxdbx.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    re_npurl = r'<a href="([^"]+)" class="">Next '
    re_npnr = r'\?page=(\d+)" class="">Next '
    utils.next_page(site, 'xxdbx.List', listhtml, re_npurl, re_npnr, contextm='xxdbx.GotoPage')
    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('?page={}'.format(np), '?page={}'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + "xxdbx.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '%20'))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    match = re.compile(r'<source\s+src="([^"]+)"\s+title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    if match:
        sources = {qual: 'https:' + videourl for videourl, qual in match}
        videourl = utils.prefquality(sources, sort_by=lambda x: 2160 if x == '4k' else int(x[:-1]), reverse=True)
        if videourl:
            vp.progress.update(75, "[CR]Video found[CR]")
            vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh Oh', 'No Videos found')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Dates", r'href="(/dates/[^"]+)">([^<]+)<', ''),
        ("Channels", r'href="(/channels/[^"]+)">([^<]+)<', ''),
        ("Stars", r'href="(/stars/[^"]+)">([^<]+)<', ''),
        ("Search", r'href="(/search/[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'xxdbx.List', lookup_list, starthtml='<div class="tags">', stophtml='</div>')
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('xxdbx.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

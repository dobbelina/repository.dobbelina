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

site = AdultSite('justporn', "[COLOR hotpink]JustPorn[/COLOR]", 'https://justporn.com/', 'justporn.png', 'justporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_search)
    # site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'video-list?lang=en&page=1')
    utils.eod()


@site.register()
def List(url):
    url = site.url[:-1] + url if url.startswith('/') else url
    url = url if 'page=' in url else url + '?page=1'

    listhtml = utils.getHtml(url, site.url)

    delimiter = '<div class="content"'
    re_videopage = '<a href="([^"]+)"'
    re_name = '>([^<]+)</a></h2>'
    re_img = '<img src="([^"]+)"'
    re_duration = r'</div>\s*([\d:]+)\s*h*d*\s*</div>'
    re_quality = r'\s(hd)\s*</div>'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('justporn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('justporn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'justporn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    match = re.search(r'page=(\d+)', url, re.IGNORECASE)
    if match:
        cp = match.group(1)
        np = int(cp) + 1
        npurl = url.replace('page={}'.format(cp), 'page={}'.format(np))

        cm_page = (utils.addon_sys + "?mode=justporn.GotoPage&list_mode=justporn.List&url=" + urllib_parse.quote_plus(npurl) + "&np=" + str(np))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np), npurl, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp=0):
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
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('justporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<div class="filter featured-category\s*"\s*data-val="(\d+)">\s*([^<]+)\s*<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    match.sort(key=lambda x: x[1])
    for data, name in match:
        name = utils.cleantext(name)
        caturl = '{0}?page=1&category[]={1}'.format(site.url, data)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)

    match = re.compile(r'<source src="([^"]+)" title="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        sources = {m[1]: site.url[:-1] + m[0].replace('&amp;', '&') for m in match}
        videourl = utils.prefquality(sources, reverse=True)
        if videourl:
            vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh Oh', 'No Videos found')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'href="(/category/[^"]+)" style="cursor: pointer">\s*([^<]+)\s*</a', ''),
        ("Tag", r'href="(/tag/[^"]+)" style="cursor: pointer">\s*<i>#</i>([^<]+)\s*</a', '')
    ]

    lookupinfo = utils.LookupInfo('', url, 'justporn.List', lookup_list)
    lookupinfo.getinfo()

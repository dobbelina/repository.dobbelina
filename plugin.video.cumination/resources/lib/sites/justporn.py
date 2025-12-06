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
import time
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('justporn', "[COLOR hotpink]JustPorn[/COLOR]", 'https://justporn.com/', 'justporn.png', 'justporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{}/', 'Search', site.img_search)
    List(site.url + 'porn-videos/')
    utils.eod()


@site.register()
def List(url):
    url = site.url[:-1] + url if url.startswith('/') else url
    url = url if 'page=' in url else url + '?page=1'

    listhtml = utils.getHtml(url, site.url)

    delimiter = '<div class="thumb thumb_rel item'
    re_videopage = '<a href="([^"]+)"'
    re_name = ' title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = r'class="time">([\d:]+)<'
    re_quality = r'class="qualtiy">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('justporn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('justporn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'justporn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    match = re.search(r'''<a class="active[^"]+">(\d+)<.+?class='next'.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">''', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        ts = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, ts)
        lpnr, lastp = 0, ''
        match = re.search(r">(\d+)</a>\s*<a\s+class='next'", listhtml, re.DOTALL | re.IGNORECASE)
        if match:
            lpnr = match.group(1)
            lastp = '/{}'.format(lpnr)
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=justporn.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&lp=" + str(lpnr))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "justporn.List&url=" + urllib_parse.quote_plus(url))
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
        List(url.format(keyword.replace(' ', '-')))


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<a href="([^"]+)"\s*title="([^"]+)">\s*<div class="img-holder">\s*<img src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for data, name, img in match:
        name = utils.cleantext(name)
        site.add_dir(name, data, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r"video(?:_|_alt_)url\d*:\s*'([^']+)'.+?video(?:_|_alt_)url\d*_size:\s*'\d+x(\d+)'", re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        sources = {m[1]: m[0] for m in match}
        vp.progress.update(75, "[CR]Video found[CR]")
        videourl = utils.prefquality(sources, sort_by=lambda x: int(x), reverse=True)
        if videourl:
            vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        (" Model", r'href="https://www.justporn.com(/models/[^"]+)">\s*<i><svg class.*?</i>\s*(\S[^<]*\S)\s*</a', ''),
        (" Sites", r'href="https://www.justporn.com(/sites/[^"]+)">\s*<i><svg class.*?</i>\s*(\S[^<]*\S)\s*</a', ''),
        ("Cat", r'href="https://www.justporn.com(/categories/[^"]+)">\s*(\S[^<]*\S)\s*</a', ''),
        ("Tag", r'href="https://www.justporn.com(/tags/[^"]+)">\s*(\S[^<]*\S)\s*</a', '')
    ]

    lookupinfo = utils.LookupInfo('', url, 'justporn.List', lookup_list)
    lookupinfo.getinfo()

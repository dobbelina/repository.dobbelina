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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
from kodi_six import xbmcgui, xbmcplugin
import json
from math import ceil
from six import unichr

site = AdultSite('pornhits', "[COLOR hotpink]PornHits[/COLOR]", 'https://www.pornhits.com/', 'pornhits.png', 'pornhits')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories.php', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'videos.php?p=1&q=', 'Search', site.img_search)
    List(site.url + 'videos.php?p=1&s=l')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    if '>There is no data in this list.<' in listhtml:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    if 'Related Videos' in listhtml:
        listhtml = listhtml.split('Related Videos')[-1].split('<div class="thumb-slider">')[0]
    delimiter = '<div class="item">'
    re_videopage = 'a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = 'duration">([^<]+)<'
    utils.videos_list(site, 'pornhits.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='pornhits.Related')

    match = re.compile(r'class="pagination.+?data-page="(\d+)"\s+data-count="(\d+)"\s+data-total="(\d+)"', re.IGNORECASE | re.DOTALL).findall(listhtml)
    if match:
        cp, count, total = match[0]
        np_url = re.sub(r'\?p=\d+', '?p={}'.format(int(cp) + 1), url)
        np = str(int(cp) + 1)
        lp = str(ceil(int(total) / int(count)))
        if int(np) <= int(float(lp)):
            cm_page = (utils.addon_sys + "?mode=pornhits.GotoPage" + "&url=" + urllib_parse.quote_plus(np_url) + "&np=" + np + "&lp=" + lp)
            cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
            site.add_dir('Next Page ({}/{})'.format(np, lp), np_url, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornhits.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = "{0}{1}/".format(url, keyword.replace(' ', '%20'))
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="item" href="([^"]+)" title="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name in match:
        site.add_dir(name.replace(' porn videos', ''), caturl, 'List', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url)
    match = re.compile(r'video:url"\s+content="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(html)
    if match:
        embedurl = match[0]
        embedhtml = utils.getHtml(embedurl)
        match = re.compile(r"\s},\s+'([^']+)',\s+null\);", re.IGNORECASE | re.DOTALL).findall(embedhtml)
        if match:
            enc_url = match[0]
            dec_url = decode_url(enc_url)
            src = json.loads(dec_url)
            sources = {s["format"][1:-4].replace('hq', '720p').replace('lq', '360p'): s["video_url"] for s in src}

            videourl = utils.prefquality(sources, reverse=True)
            if videourl:
                replacelst = {'A': '\u0410', 'B': '\u0412', 'C': '\u0421', 'E': '\u0415', 'M': '\u041c'}
                for key in replacelst:
                    videourl = videourl.replace(replacelst[key], key)
                url1 = utils._bdecode(videourl.split(',')[0] + '==')
                url2 = utils._bdecode(videourl.split(',')[1] + '==')
                videolink = site.url[:-1] + url1 + '?' + url2 + '|referer=' + embedurl
                vp.play_from_direct_link(videolink)


def decode_url(t):
    # does not work in python 2 !!!
    e = u'\u0410\u0412\u0421D\u0415FGHIJKL\u041cNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
    n = ''
    r = 0
    while r < len(t):
        o = e.index(t[r])
        i = e.index(t[r + 1])
        a = e.index(t[r + 2])
        s = e.index(t[r + 3])
        o = o << 2 | i >> 4
        i = (15 & i) << 4 | a >> 2
        c = (3 & a) << 6 | s
        n += unichr(o)
        if a != 64:
            n += unichr(i)
        if s != 64:
            n += unichr(c)
        r += 4
    return n


@site.register()
def GotoPage(url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('?p={}'.format(np), '?p={}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=pornhits.List" + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')

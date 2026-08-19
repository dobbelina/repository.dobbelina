'''
    Cumination
    Copyright (C) 2015 Whitecream

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
import ssl
from http.cookiejar import MozillaCookieJar
from urllib import request


site = AdultSite("anybunny", "[COLOR hotpink]Anybunny[/COLOR]", "https://anybunny.org/", "anybunny.png", "anybunny")


@site.register(default_mode=True)
def Main():
    # site.add_dir('[COLOR hotpink]Categories - images[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - all[/COLOR]', site.url, 'Categories2', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'new/', 'Search', site.img_search)
    # List(site.url + 'new/twins')
    Categories(site.url)
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        utils.notify(msg='No videos found!')
        return

    delimiter = r"<li\s+data-id='|class='nuyrfe"
    re_videopage = "href='([^']+)'"
    re_name = "alt='([^']+)'"
    re_img = r"src='([^']+)'"
    re_duration = r"'>([\d:]+)</div>"
    re_quality = r"'>(HD)\s*</div>"

    cm = []
    cm_related = (utils.addon_sys + "?mode=anybunny.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'anybunny.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    re_npurl = 'href="([^"]+)">Next'
    re_npnr = r'\?p=(\d+)">Next'
    utils.next_page(site, 'anybunny.List', listhtml, re_npurl, re_npnr, contextm='anybunny.GotoPage')
    utils.eod()


@site.register()
def Categories(url):
    utils.kodilog('Categories url: {}'.format(url))
    cathtml = utils.getHtml(url, '')
    match = re.compile(r"href='/top/([^']+)'>.*?src='([^']+)'\s*alt='([^']+)'", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match = sorted(match, key=lambda x: x[2])
    for catid, img, name in match:
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Categories2(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r"href='/top/([^']+)'>([^<]+)</a> <a>([^)]+\))", re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catid, name, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '_'))


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'\?p=\d+', r'?p={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "anybunny.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('anybunny.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


def fetch(url, headers):
    request = utils.Request(url, headers=headers)
    response = utils.opener.open(request, timeout=20)
    data = response.read().decode('utf-8', errors='ignore')
    return data


@site.register()
def Playvid(url, name, download=None):
    hdr = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Referer': url,
    }

    def make_opener(cookie_jar=None):
        if cookie_jar is None:
            cookie_jar = MozillaCookieJar()

        opener = request.build_opener(
            request.HTTPCookieProcessor(cookie_jar),
            request.HTTPSHandler(context=ssl.create_default_context())
        )
        return opener, cookie_jar

    def fetch(url, cookie_jar=None):
        opener, cookie_jar = make_opener(cookie_jar)
        req = request.Request(url, headers=hdr)
        resp = opener.open(req, timeout=30)
        data = resp.read().decode('utf-8', 'replace')
        return data, cookie_jar

    vp = utils.VideoPlayer(name, download)

    cj = None

    for i in range(5):
        html, cj = fetch(url, cookie_jar=cj)
        if '/stream1/' in html:
            break

    if html and '/stream1/' in html:
        match = re.search(r"<iframe.+?src='([^']*)'", html, re.DOTALL | re.IGNORECASE)
        if match:
            iframe_url = match.group(1)

            data, cj = fetch(iframe_url, cookie_jar=cj)
            match = re.search(r'file:"[^"]*(http[^"]*)"', data, re.DOTALL | re.IGNORECASE)
            if match:
                video_url = match.group(1)
                video_url = video_url + '|User-Agent=' + hdr['User-Agent']
                vp.play_from_direct_link(video_url)
    else:
        utils.notify('Oh Oh', 'No Video found')

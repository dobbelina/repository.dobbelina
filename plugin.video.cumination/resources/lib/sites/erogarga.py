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
import json
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.sites.spankbang import Playvid

site = AdultSite('erogarga', '[COLOR hotpink]EroGarga[/COLOR]', 'https://www.erogarga.com/', 'erogarga.png', 'erogarga')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    html = listhtml.split('>SHOULD WATCH<')[0]
    videos = html.split('article data-video-uid')
    videos.pop(0)
    for video in videos:
        if 'type-photos' in video:
            continue
        match = re.compile(r'href="([^"]+).+?data-src="([^"]+)".+?<span>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            videourl, img, name = match[0]
            name = utils.cleantext(name)
            site.add_download_link(name, videourl, 'Play', img, name)

    re_npurl = 'href="([^"]+)"[^>]*>Next' if '>Next' in html else 'class="current".+?href="([^"]+)"'
    re_npnr = r'/page/(\d+)[^>]*>Next' if '>Next' in html else r'class="current".+?rel="follow">(\d+)<'
    re_lpnr = r'/page/(\d+)[^>]*>Last' if '>Last' in html else r'rel="follow">(\d+)<\D+<\/main>'
    utils.next_page(site, 'erogarga.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='erogarga.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    cathtml = cathtml.split('>TAGS<')[-1].split('/section>')[0]
    match = re.compile(r'<a href="([^"]+)".+?aria-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='"file":"([^"]+)"')
    videohtml = utils.getHtml(url)
    match = re.compile(r'''<iframe[^>]+src=['"]([^'"]+)['"]''', re.DOTALL | re.IGNORECASE).findall(videohtml)

    playerurl = match[0]
    if 'phixxx.cc/player/play.php?vid=' in playerurl:
        vid = playerurl.split('?vid=')[-1]
        posturl = 'https://phixxx.cc/player/ajax_sources.php'
        formdata = {'vid': vid, 'alternative': 'spankbang', 'ord': '0'}
        data = utils.postHtml(posturl, form_data=formdata)
        data = data.replace(r'\/', '/')
        jsondata = json.loads(data)
        src = jsondata["source"]
        if len(src) > 0:
            videolink = src[0]["file"]
        else:
            formdata = {'vid': vid, 'alternative': 'mp4', 'ord': '0'}
            data = utils.postHtml(posturl, form_data=formdata)
            data = data.replace(r'\/', '/')
            jsondata = json.loads(data)
            videolink = jsondata["source"][0]["file"]
    elif 'pornflip.com' in playerurl:
        playerhtml = utils.getHtml(playerurl, url)
        match = re.compile(r'(data-\S+src\d*)="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(playerhtml)
        src = {m[0]: m[1] for m in match}
        videolink = utils.selector('Select video', src)
        videolink = videolink.replace('&amp;', '&') + '|referer=https://www.pornflip.com/'
    else:
        playerhtml = utils.getHtml(playerurl, url)
        match = re.compile(r'''var hash = '([^']+)'.+?var baseURL = '([^']+)'.+?getPhiPlayer\(hash,'([^']+)',"(\d+)"\);''', re.DOTALL | re.IGNORECASE).findall(playerhtml)
        if match:
            hash, baseurl, alternative, order = match[0]
            formdata = {'vid': hash, 'alternative': alternative, 'ord': order}
            data = utils.postHtml(baseurl + 'ajax_sources.php', form_data=formdata)
            data = data.replace(r'\/', '/')
            jsondata = json.loads(data)
            videolink = jsondata["source"][0]["file"]
            if 'blogger.com' in videolink:
                vp.direct_regex = '"play_url":"([^"]+)"'
                vp.play_from_site_link(videolink, url)
                return
        else:
            videolink = playerurl

    if 'spankbang' in videolink:
        videolink = videolink.replace('/embed/', '/video/')
        Playvid(videolink, name, download=download)
    elif 'xhamster' in videolink or 'eporner' in videolink:
        vp.play_from_link_to_resolve(videolink)
    else:
        vp.play_from_direct_link(videolink)

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
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('beemtube', '[COLOR hotpink]BeemTube[/COLOR]', 'https://beemtube.com/', 'beemtube.png', 'beemtube')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/alphabetical/', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?q=', 'Search', site.img_search)
    List(site.url + 'most-recent/')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url)
    if 'Sorry, no results were found.' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<div class="content'
    re_videopage = r'<a href="([^"]+)"\s*class="thumb'
    re_name = '<strong>([^<]+)<'
    re_img = 'data-src="([^"]+)"'
    re_duration = 'class="duration">([^<]+)<'
    re_quality = 'span class="([^_]+)_video"'
    utils.videos_list(site, 'beemtube.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality)

    re_npurl = r'''href=['"]([^'"]+)['"]>Next<'''
    re_npnr = r"href='[^>]+page=(\d+)'>Next" if '&page=' in html else r'href="page(\d+).html">Next<'
    utils.next_page(site, 'beemtube.List', html, re_npurl, re_npnr, baseurl=url.split('page')[0], contextm='beemtube.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page{}.html'.format(np), 'page{}.html'.format(pg))
        url = url.replace('&page={}'.format(np), '&page={}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Channels(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="channel_item".+?href="([^"]+)" title="([^"]+)".+?data-src="([^"]+)".+?"channel_item_videos">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, img, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({})[/COLOR]'.format(count.strip())
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Pornstars(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="content item actors".+?href="([^"]+)" title="([^"]+)".+?data-src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, img in match:
        site.add_dir(name, caturl, 'List', img)
    re_npurl = r'''href=['"]([^'"]+)['"]>Next<'''
    re_npnr = r'href="page(\d+).html">Next<'
    utils.next_page(site, 'beemtube.Pornstars', cathtml, re_npurl, re_npnr, baseurl=url.split('page')[0], contextm='beemtube.GotoPage')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="content categor.+?href="([^"]+)".+?data-src="([^"]+)".+?strong>([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name in match:
        site.add_dir(name.title(), caturl, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    match = re.compile(r'"embedUrl":\s+"([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        embedhtml = utils.getHtml(match[0])
        match = re.compile(r'"playlist":\s+"([^"]+)"', re.IGNORECASE | re.DOTALL).findall(embedhtml)
        if match:
            playlist = utils.getHtml(match[0])
            jdata = json.loads(playlist)
            if "label" not in jdata["playlist"][0]["sources"][0].keys():
                jdata["playlist"][0]["sources"][0]["label"] = "0p"
            sources = {j["label"]: j["file"] for j in jdata["playlist"][0]["sources"]}
            videourl = utils.prefquality(sources, reverse=True)
            if videourl:
                vp.play_from_direct_link(videourl + '|referer:' + url)

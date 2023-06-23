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
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('fullxcinema', '[COLOR hotpink]fullxcinema[/COLOR]', 'https://fullxcinema.com/', 'fullxcinema.png', 'fullxcinema')


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
        # if 'type-photos' in video:
        #     continue
        match = re.search(r'href="([^"]+).+?data-src="([^"]+)"\salt="([^"]+)".+?fa-clock-o"></i>([^<]+)<', video, re.DOTALL | re.IGNORECASE)
        if match:
            videourl, img, name, duration = match.group(1), match.group(2), match.group(3), match.group(4)
            name = utils.cleantext(name)
            site.add_download_link(name, videourl, 'Play', img, name, duration=duration)

    re_npurl = 'href="([^"]+)"[^>]*>Next' if '>Next' in html else 'class="current".+?href="([^"]+)"'
    re_npnr = r'/page/(\d+)[^>]*>Next' if '>Next' in html else r'class="current".+?rel="follow">(\d+)<'
    re_lpnr = r'/page/(\d+)[^>]*>Last' if '>Last' in html else r'rel="follow">(\d+)<\D+<\/main>'
    utils.next_page(site, 'fullxcinema.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='fullxcinema.GotoPage')
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
    cathtml = cathtml.split('title">Tags<')[-1].split('/section>')[0]
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
    vp = utils.VideoPlayer(name, download=download, regex='<source src="([^"]+)"')
    videohtml = utils.getHtml(url)
    match = re.compile(r'<iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if match:
        link = match[0]
        if vp.resolveurl.HostedMediaFile(link):
            vp.play_from_link_to_resolve(link)
        else:
            html = utils.getHtml(link)
            vp.play_from_html(html)

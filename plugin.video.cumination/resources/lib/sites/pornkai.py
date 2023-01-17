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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('pornkai', "[COLOR hotpink]PornKai[/COLOR]", 'https://pornkai.com/', 'pornkai.png', 'pornkai')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'all-categories', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'api?query={}&sort=best&page=0&method=search', 'Search', site.img_search)
    List(site.url + 'api?query=_best&sort=new&page=0&method=search')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    html = html.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')

    delimiter = '<div class="thumbnail">'
    re_videopage = 'href="([^"]+)"'
    re_name = '<span class="trigger_pop th_wrap">([^<]+)</span>'
    re_img = "src='([^']+)'"
    re_duration = 'fa-clock"></i>([^<]+)<'
    utils.videos_list(site, 'pornkai.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='pornkai.Related')

    match = re.compile(r'"results_remaining":(\d+)', re.DOTALL | re.IGNORECASE).search(html)
    if match:
        rr = match.group(1)
        match = re.compile(r'[?&]page=(\d+)', re.DOTALL | re.IGNORECASE).search(url)
        if match:
            page = int(match.group(1))

        lp = page + 2 + int(rr) // 120
        np = page + 2
        if int(rr) > 0:
            npurl = url.replace('page={}'.format(page), 'page={}'.format(page + 1))
            site.add_dir('Next Page ({}/{})'.format(np, lp), npurl, 'List', site.img_next)
    utils.eod()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornkai.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url.format(keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'''thumbnail_link"\s*href="([^"]+)".+?data-src='([^']+)'.+?title">([^<]+)<''', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name in match:
        name = utils.cleantext(name)
        caturl = site.url + 'api?query={}&sort=best&page=0&method=search'.format(caturl.split('?q=')[-1])
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=r'iframe.+?src="([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'iframe.+?src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        videolink = match[0]
        if 'xh.video' in videolink:
            videolink = utils.getVideoLink(videolink).split('?')[0]
        vp.play_from_link_to_resolve(videolink)

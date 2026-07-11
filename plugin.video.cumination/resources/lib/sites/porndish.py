'''
    Ultimate Whitecream
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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc


site = AdultSite('porndish', '[COLOR hotpink]Porndish[/COLOR]', 'https://www.porndish.com/', 'porndish.png', 'porndish')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Networks[/COLOR]', site.url, 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)

    delimiter = 'class="g1-collection-item'
    re_videopage = 'href="([^"]+)"'
    re_name = ' title="([^"]+)"'
    re_img = 'data-src="([^"]+)"'
    re_duration = 'video-duration">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=porndish.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin({})'.format(cm_lookupinfo)))
    cm_related = (utils.addon_sys + "?mode=porndish.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin({})'.format(cm_related)))

    utils.videos_list(site, 'porndish.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm, img_options='|Referer={}'.format(url))

    next_page = re.compile(r'next-page-url="([^"]+/page/(\d+)/[^"]*)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if next_page:
        site.add_dir('Next Page ({})'.format(next_page.group(2)), next_page.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'menu-item-\d+"><a href="({}([^/]+)[^"]+)">([^<]+)</a>'.format(site.url), re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, network, name in match:
        name = '[COLOR hotpink]{}[/COLOR] - {}'.format(network.title(), name)
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=None)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    vp.progress.update(50, "[CR]Processing video page[CR]")
    videohtml = videohtml.replace('\\', '')
    vp.play_from_html(videohtml, url)


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('porndish.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Tag", r'/(video2/[^"]+)" class="entry-tag entry-tag-\d+">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, '{}.List'.format(site.module_name), lookup_list)
    lookupinfo.getinfo()

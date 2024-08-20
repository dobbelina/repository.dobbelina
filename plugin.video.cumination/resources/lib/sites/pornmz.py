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
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite('pornmz', '[COLOR hotpink]Pornmz[/COLOR]', 'https://pornmz.com/', 'https://pornmz.com/wp-content/uploads/2021/03/PornMZ.png', 'pornmz')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Best[/COLOR]', site.url + 'page/1?filter=popular', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'page/1?filter=most-viewed', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Longest[/COLOR]', site.url + 'page/1?filter=longest', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1?filter=latest')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)

    delimiter = '<article id="post'
    re_videopage = 'href="([^"]+)"'
    re_name = ' title="([^"]+)"'
    re_img = '(?:img src|img data-src|poster)="([^"]+)"'
    re_duration = 'duration">([^<]+)<'
    re_quality = '>HD<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=pornmz.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=pornmz.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'pornmz.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)
    np = re.compile(r'class="current">\d+<[^h]+href="([^"]+)"\s*class="inactive">(\d+)<', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page... ({0})'.format(np.group(2)), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    while True:
        cathtml = utils.getHtml(url, site.url)
        match = re.compile(r'<article [^<]+<a\s+href="([^"]+)"\s+title="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
        for sitepage, name, img in match:
            name = utils.cleantext(name)
            siteurl = sitepage + '/page/1?filter=latest'
            site.add_dir(name, siteurl, 'List', img)
        np = re.search(r'current">\d</a></li><li><a\s+href="([^"]+)"', cathtml, re.IGNORECASE | re.DOTALL)
        if np:
            url = np.group(1)
        else:
            break
    utils.eod()


@site.register()
def Tags(url):
    taghtml = utils.getHtml(url, site.url)
    match = re.compile(r'tag-item"><a\s+href="([^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(taghtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = tagpage + '/page/1?filter=latest'
        site.add_dir(name, tagpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url)
    iframematch = re.compile(r'iframe\s+src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if iframematch:
        iframe = iframematch[0]
        html = utils.getHtml(iframe, site.url)
        videomatch = re.compile(r'source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
        if videomatch:
            videourl = videomatch[0] + '|Referer={}'.format(site.url)
            vp.play_from_direct_link(videourl)
            return
    utils.notify('Oh oh', 'No video found')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornmz.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'href="([^"]+)"[^>]+><i class="fa\s+fa-folder"></i>([^<]+)<', ''),
        ("Pornstar", r'href="([^"]+)"[^>]+><i class="fa\s+fa-star"></i>([^<]+)<', ''),
        ("Tag", r'href="([^"]+)"[^>]+><i class="fa\s+fa-tag"></i>([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo('', url, 'pornmz.List', lookup_list)
    lookupinfo.getinfo()

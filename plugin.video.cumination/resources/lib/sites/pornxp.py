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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('pornxp', '[COLOR hotpink]PornXP[/COLOR]', 'https://pornxp.com/', 'https://pornxp.com/logo2.png', 'pornxp')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]New releases[/COLOR]', site.url + 'released/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]HD[/COLOR]', site.url + 'hd/?sort=new', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url, 'Tags', site.img_cat)
    #site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?q=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('item_cont">.*?href="/([^"]+)".*?(?:data-)*src="([^"]+jpg)".*?dur">([^<]+)<.*?item_title">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, duration, name in match:
        name = utils.cleantext(name)
        img = 'https:' + img if img.startswith('//') else img
        videopage = site.url + videopage

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('pornxp.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

    np = re.compile(r'"chosen">\d*<.*?href="/([^"]+)"[^>]+>(\d+?)<', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(2)
        site.add_dir('Next Page (' + page_number + ')', site.url + np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videopage = utils.getHtml(url, site.url)

    sources = {}
    srcs = re.compile(r'source\s*src="([^"]+)"\s*title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    for src, quality in srcs:
        sources[quality] = src
    videourl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
    if not videourl:
        vp.progress.close()
        return
    videourl = 'https:' + videourl if videourl.startswith('//') else videourl
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(videourl)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    tagpart = re.compile('class="tags">(.*?)</div', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tags in tagpart:
        match = re.compile('href="/([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(tags)
        for tagpage, name in match:
            name = utils.cleantext(name.strip())
            site.add_dir(name, site.url + tagpage + '?sort=new', 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    class PornxpLookup(utils.LookupInfo):
        def url_constructor(self, url):
            return site.url + url + '?sort=new'

    lookup_list = [
        ("Tag", ['class="tags">(.*?)class', '/(tags/[^"]+)">([^<]+)<'], '')]

    lookupinfo = PornxpLookup(site.url, url, 'pornxp.List', lookup_list)
    lookupinfo.getinfo()
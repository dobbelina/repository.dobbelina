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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hitprn', '[COLOR hotpink]Hitprn[/COLOR]', 'https://www.hitprn.com/', 'https://www.hitprn.com/wp-content/uploads/2021/03/hitprn-logo.png', 'hitprn')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Sites[/COLOR]', site.url, 'Sites', '', '')
    site.add_dir('[COLOR hotpink]Most Views[/COLOR]', site.url + 'page/1/?orderby=views', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Likes[/COLOR]', site.url + 'page/1/?orderby=likes', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1/?orderby=date')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="clip-link" data-id="\d+" title="([^"]+)" href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, videopage, img in match:
        name = utils.cleantext(name)

        contexturl = (utils.addon_sys
                      + "?mode=hitprn.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu = [('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')]

        site.add_download_link(name, videopage, 'Play', img, name, contextm=contextmenu)

    np = re.compile('Next page" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page... ({0})'.format(np.group(1).split('/')[-2]), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Sites(url):
    siteshtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="level-\d+" value="([^"]+)">([^<]+)</option', re.DOTALL | re.IGNORECASE).findall(siteshtml)
    for sitepage, name in match:
        name = name.replace('&nbsp;&nbsp;&nbsp;', '- ')
        name = utils.cleantext(name)
        siteurl = site.url + '?cat=' + sitepage
        site.add_dir(name, siteurl, 'List')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+') + '&orderby=date'
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    sources = re.compile(r'''<source\s*src="([^"]+)".+?label="([^"]+)''', re.DOTALL | re.IGNORECASE).findall(html)
    sources = {quality: videourl for videourl, quality in sources}
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: int(x[:-1]), reverse=True)
    if videourl:
        vp.play_from_direct_link(videourl + '|Referer=' + site.url)
    else:
        vp.progress.close()
        return


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Site", r'/(sites/[^"]+)"\s+rel="category tag">([^<]+)<', ''),
        ("Pornstar", r'/(pornstar/[^"]+)"\s+rel="tag">([^<]+)<', ''),
        ("Tag", r'/(tag/[^"]+)"\s+rel="tag">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'hitprn.List', lookup_list)
    lookupinfo.getinfo()

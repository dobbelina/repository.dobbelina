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

site = AdultSite('alluretube', '[COLOR hotpink]Allure Tube[/COLOR]', 'https://www.alluretube.com/', 'https://www.alluretube.com/images/logo/logo.png', 'alluretube')
site2 = AdultSite('desihoes', '[COLOR hotpink]Desi Hoes[/COLOR]', 'https://www.desihoes.com/', 'https://www.desihoes.com/images/logo/logo.png', 'desihoes')


def getBaselink(url):
    if 'desihoes.com' in url:
        siteurl = 'https://www.desihoes.com/'
    elif 'alluretube.com' in url:
        siteurl = 'https://www.alluretube.com/'
    return siteurl


@site.register(default_mode=True)
@site2.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories', 'Cats', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', siteurl, 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/videos/', 'Search', site.img_search)
    List(siteurl + 'videos?o=mr&page=1')
    utils.eod()


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'lg-4\s+">\s+<a href="([^"]+)">.*?src="([^"]+)"\s+title="([^"]+)"[^>]+>\s+<div class="duration">([^\d]+)(\d[^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, name, hd, duration in match:
        name = utils.cleantext(name)
        duration = utils.cleantext(duration.strip())
        hd = 'HD' if 'hd' in hd.lower() else ''
        videopage = siteurl + videopage

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('alluretube.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))

        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd, contextm=contextmenu)

    np = re.compile(r'<a\s+class="page-link"\s+href="([^"]+)" class="prevnext"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page...', np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title + '?o=mr&page=1'
        List(searchUrl)


@site.register()
def Cats(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    match = re.compile(r'/(videos/[^"]+)">.*?src="([^"]+)"\s+title="([^"]+)".*?float-right">([^<]+)</', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name, videos in match:
        name = '{} - [COLOR hotpink]{}[/COLOR]'.format(utils.cleantext(name), videos.strip())
        catpage = siteurl + catpage + '?o=mr&page=1'
        img = siteurl + img
        site.add_dir(name, catpage, 'List', img)

    utils.eod()


@site.register()
def Tags(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    match = re.compile(r"name:\s+'([^']+)', type:\s+'([^']+)'", re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, videos in sorted(match):
        name = '{} - [COLOR hotpink]{}[/COLOR]'.format(utils.cleantext(tagpage), videos)
        site.add_dir(name, siteurl + 'search/videos/', 'Search', '', keyword=tagpage)
    utils.eod()


@site.register()
def Lookupinfo(url):
    siteurl = getBaselink(url)
    lookup_list = [
        ("Tag", r'class="tag"\s+href="/(search/[^"]+)">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(siteurl, url, 'alluretube.List', lookup_list)
    lookupinfo.getinfo()

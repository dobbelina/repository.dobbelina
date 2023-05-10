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

site = AdultSite('porndish', '[COLOR hotpink]Porndish[/COLOR]', 'https://www.porndish.com/', 'https://www.porndish.com/wp-content/uploads/2022/03/logo.png', 'porndish')


@site.register(default_mode=True)
def Main():
    List(site.url + 'page/1/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    if '/page/1/' in url:
        first2match = re.compile("New Porn Videos(.*?)More Porn", re.IGNORECASE | re.DOTALL).findall(listhtml)
        if not first2match:
            return
        first2match = first2match[0]
        match1 = re.compile('<a title="([^"]+)".*?href="([^"]+)".*?data-src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(first2match)
        for name, videopage, img in match1:
            name = utils.cleantext(name)
            site.add_download_link(name, videopage, 'Playvid', img, name)

    match = re.compile("More Porn Videos(.*?)g1-pagination-end", re.IGNORECASE | re.DOTALL).findall(listhtml)
    if match:
        match = match[0]
        match2 = re.compile('<a title="([^"]+)".*?href="([^"]+)".*?data-src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(match)
        if not match2:
            return
        for name, videopage, img in match2:
            name = utils.cleantext(name)
            site.add_download_link(name, videopage, 'Playvid', img, name)
    else:
        return            
    next_page = re.compile('rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if next_page:
        site.add_dir('Next Page', next_page.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=None)
    vp.play_from_site_link(url, url)

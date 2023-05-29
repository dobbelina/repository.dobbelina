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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('ividz', '[COLOR hotpink]Ividz[/COLOR]', 'https://www.incestvidz.com/', 'https://www.incestvidz.com/wp-content/uploads/logo-1.jpg', 'ividz')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', '', '')
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tag', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?orderby=date')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="clip-link" data-id="\d+" title="([^"]+)" href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, videopage, img in match:
        name = utils.cleantext(name)

        site.add_download_link(name, videopage, 'Play', img, name)

    np = re.compile('Next page" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page... ({0})'.format(np.group(1).split('/')[-2]), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'/(category[^ ]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url + catpage + '?orderby=date', 'List')
    utils.eod()


@site.register()
def Tag(url):
    taghtml = utils.getHtml(url, site.url)
    match = re.compile('/(tag[^ ]+/).*?label="([^"]+)"').findall(taghtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url + tagpage + '?orderby=date', 'List', '')

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
    vp = utils.VideoPlayer(name, download=download, regex=r"""<iframe[.\n]*.*?src\s*=\s*?["']*?([^'" ]+)""")
    vp.play_from_site_link(url)

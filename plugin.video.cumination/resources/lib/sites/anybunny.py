'''
    Cumination
    Copyright (C) 2015 Whitecream

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

site = AdultSite("anybunny", "[COLOR hotpink]Anybunny[/COLOR]", "http://anybunny.org/", "anybunny.png", "anybunny")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Top videos[/COLOR]', site.url + 'top/', 'List', '', '')
    site.add_dir('[COLOR hotpink]Categories - images[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - all[/COLOR]', site.url, 'Categories2', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'new/', 'Search', site.img_search)
    List(site.url + 'new/?p=1')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r"class='nuyrfe'\s*href='([^']+).+?src='([^']+).+?alt='([^']+)", re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, '')

    nextp = re.compile('href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, 'src=["]([^"]+)')
    vp.play_from_site_link(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("<a href='/top/([^']+)'>.*?src='([^']+)' alt='([^']+)'", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match = sorted(match, key=lambda x: x[2])
    for catid, img, name in match:
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Categories2(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r"href='/top/([^']+)'>([^<]+)</a> <a>([^)]+\))", re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catid, name, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '_')
        searchUrl = searchUrl + title
        List(searchUrl)

"""
    Cumination
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 Fr40m1nd

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
"""

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('mrsexe', '[COLOR hotpink]Mr Sexe[/COLOR]', 'https://www.mrsexe.com/', 'mrsexe.png', 'mrsexe')

progress = utils.progress


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Classiques[/COLOR]', site.url + 'classiques/', 'List', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?search=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Stars[/COLOR]', site.url + 'filles/', 'Stars', '', '')
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'<ul\s*class="thumb-list\s*xx.+?class="dark', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        match = re.compile(r'<ul\s*class="thumb-list\s*xx.+?footer', re.DOTALL | re.IGNORECASE).findall(listhtml)
    items = re.compile(r'<li\s*class="(\s*hd|)".+?href="([^"]+).+?src="([^"]+).+?tion">[^\d]+([^<]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(match[0])
    for qual, videopage, img, duration, name in items:
        if img.startswith('//'):
            img = 'http:' + img
        name = utils.cleantext(name.strip())
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', img, name, duration=duration, quality=qual)

    nextp = re.compile(r'<li\s*class="arrow"><a\s*href="(.+?)">suivant').search(match[0])
    if nextp:
        site.add_dir('Next Page', site.url[:-1] + nextp.group(1), 'List', site.img_next)

    utils.eod()


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
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('value="(/cat[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, site.url[:-1] + catpage, 'List', '')
    utils.eod()


@site.register()
def Stars(url):
    starhtml = utils.getHtml(url, '')
    match = re.compile(r'<ul\s*class="thumb-list\s*xx.+?Simila', re.DOTALL | re.IGNORECASE).findall(starhtml)[0]
    items = re.compile(r'nail">.+?src="([^"]+).+?href="([^"]+)">([^<]+).+?\s([^<]+)', re.DOTALL | re.IGNORECASE).findall(match)
    for img, starpage, name, vidcount in items:
        if img.startswith('//'):
            img = 'http:' + img
        name = "{0}[COLOR orange] [COLOR deeppink][I]({1})[/I][/COLOR]".format(utils.cleantext(name), vidcount.strip())
        site.add_dir(name, site.url[:-1] + starpage, 'List', img)
    nextp = re.compile(r'<li\s*class="arrow"><a\s*href="(.+?)">suivant').search(starhtml)
    if nextp:
        site.add_dir('Next Page', site.url[:-1] + nextp.group(1), 'Stars', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    html = utils.getHtml(url, site.url)
    videourl = re.compile(r"src='(/inc/clic\.php\?video=.+?&cat=mrsex.+?)'").findall(html)
    html = utils.getHtml(site.url[:-1] + videourl[0], site.url)
    videourl = re.compile("""['"]([^'"]*mp4)['"]""", re.DOTALL).findall(html)
    if videourl:
        utils.playvid(videourl[-1], name, download)
    else:
        return

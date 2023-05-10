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

site = AdultSite('bubbaporn', '[COLOR hotpink]BubbaPorn[/COLOR]', 'https://www.bubbaporn.com/', 'bubba.png', 'bubbaporn')


@site.register(default_mode=True)
def TPMain():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'channels/', 'TPCat', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'TPPornstars', '', '')
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/a/', 'TPList', '', '')
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'most-viewed/a/', 'TPList', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?q=', 'TPSearch', site.img_search)
    TPList(site.url)
    utils.eod()


@site.register()
def TPList(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'src="([^"]+jpg)[^<]+[^"]+"([^"]+)">([^<]+)<[^"]+[^>]+>([^\s]+)\s', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for thumb, videourl, name, duration in match:
        if thumb.startswith('//'):
            thumb = 'http:' + thumb
        name = utils.cleantext(name)
        videourl = site.url[:-1] + videourl
        site.add_download_link(name, videourl, 'TPPlayvid', thumb, '', duration=duration)
    p = re.search(r'<a\s*href="([^"]+)"\s*class="btn-pagination">Next', listhtml, re.DOTALL | re.IGNORECASE)
    if p:
        purl = site.url[:-1] + p.group(1)
        site.add_dir('Next Page...', purl, 'TPList', site.img_next)
    utils.eod()


@site.register()
def TPPlayvid(url, name, download=None):
    videopage = utils.getHtml(url, site.url)
    match = re.compile(r'<source\s*src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    if match:
        videourl = match[0]
        if videourl.startswith('//'):
            videourl = 'http:' + videourl
        utils.playvid(videourl, name, download)


@site.register()
def TPCat(url):
    caturl = utils.getHtml(url, site.url)
    match = re.compile('class="cat.+?data-src="([^"]+)"[^<]+<[^"]+"([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(caturl)
    match = sorted(match, key=lambda x: x[2])
    for thumb, caturl, cat in match:
        caturl = site.url[:-1] + caturl
        site.add_dir(cat, caturl, 'TPList', thumb, 1)
    utils.eod()


@site.register()
def TPPornstars(url):
    pshtml = utils.getHtml(url, site.url)
    pornstars = re.compile("""class="box-chica.+?data-src=['"]([^'"]+).+?href="([^"]+)">([^<]+).+?total-videos.+?>([^<]+)""", re.DOTALL | re.IGNORECASE).findall(pshtml)
    for img, psurl, title, videos in pornstars:
        psurl = site.url[:-1] + psurl
        title = title + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(title, psurl, 'TPList', img, 1)
    p = re.search(r'<a\s*href="([^"]+)"\s*class="btn-pagination">Next', pshtml, re.DOTALL | re.IGNORECASE)
    if p:
        purl = site.url[:-1] + p.group(1)
        site.add_dir('Next Page...', purl, 'TPPornstars', site.img_next)
    utils.eod()


@site.register()
def TPSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'TPSearch')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        TPList(searchUrl)

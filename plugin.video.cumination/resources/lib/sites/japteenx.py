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

site = AdultSite('japteenx', '[COLOR hotpink]JapTeenX[/COLOR]', 'https://www.japteenx.com/', 'https://cdn.japteenx.com/images/logo/logo.png', 'japteenx')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'tags', 'Cats', site.img_cat)
    site.add_dir('[COLOR hotpink]Girls[/COLOR]', site.url + 'pornstars', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/videos?search_query=', 'Search', site.img_search)
    List(site.url + 'videos?o=mr&type=public&page=1')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'well well-sm[^"]*?">\s*<a href="/([^"]+)".*?src="([^"]+)"\s*title="([^"]+)"(.*?)duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, name, hd, duration in match:
        name = utils.cleantext(name)
        duration = utils.cleantext(duration)
        hd = 'HD' if 'HD' in hd else ''
        videopage = site.url + videopage

        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    np = re.compile('<li><a href="([^"]+)" class="prevnext', re.DOTALL | re.IGNORECASE).search(listhtml)
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
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title + '&type=public'
        List(searchUrl)


@site.register()
def Cats(url):
    match = [
        ('Amateur', 'videos/amateur'),
        ('Gravure Idols', 'videos/gravure-idols'),
        ('Hentai', 'videos/hentai'),
        ('JAV', 'videos/jav'),
        ('JAV Amateur', 'videos/jav-amateur'),
        ('JAV Softcore', 'videos/jav-softcore'),
        ('JAV Uncensored', 'videos/jav-uncensored'),
        ('Southeast Asia', 'videos/southeast-asia'),
        ('Western Girls', 'videos/western-girls'),
    ]
    for name, catpage in match:
        site.add_dir(name, site.url + catpage + '?type=public&o=mr', 'List', '')

    utils.eod()


@site.register()
def Pornstars(url):
    listhtml = utils.getHtml(url)
    match = re.compile('class="model-sh" href="/([^"]+)">.*?src="([^"]+)".*?title-small">([^<]+)<.*?fa-film"></i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, img, name, videos in match:
        name = '{} - [COLOR hotpink]{}[/COLOR]'.format(utils.cleantext(name), videos)
        videos = utils.cleantext(videos)
        site.add_dir(name, site.url + catpage, 'List', img)

    np = re.compile('<li><a href="([^"]+)" class="prevnext', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        site.add_dir('Next Page...', np.group(1), 'Pornstars', site.img_next)

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url, site.url, error=True)
    match = re.compile('/(tags/[^"]+)">([^<]+)</a><span>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name, videos in match:
        name = '{} - [COLOR hotpink]{}[/COLOR]'.format(utils.cleantext(name), videos)
        site.add_dir(name, site.url + tagpage + '?type=public&o=mr', 'List', '')

    utils.eod()

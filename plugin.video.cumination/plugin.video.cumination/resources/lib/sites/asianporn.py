'''
    Cumination
    Copyright (C) 2022 Team Cumination

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
import xbmc

site = AdultSite('asianporn', '[COLOR hotpink]AsianPorn[/COLOR]', 'https://asianporn.li/', 'https://asianporn.li/templates/bootadult4/images/logo.png?t=1672106520', 'asianporn')


@site.register(default_mode=True)
def Main(url):
    sort_orders = {'Recent': '', 'Most viewed': 'viewed/', 'Top rated': 'rated/', 'Most favorited': 'favorited/', 'Recently watched': 'watched/', 'Longest': 'longest/'}
    order = utils.addon.getSetting('apsortorder') if utils.addon.getSetting('apsortorder') else ''
    ordername = list(sort_orders.keys())[list(sort_orders.values()).index(order)]
    site.add_dir('[COLOR hotpink]Sort Order: [/COLOR] [COLOR orange]{}[/COLOR]'.format(ordername), site.url, 'Sortorder', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Lists[/COLOR]', site.url + 'playlists/', 'Lists', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/video/?s=', 'Search', site.img_search)
    List(site.url + 'videos/')
    utils.eod()


@site.register()
def List(url):
    order = utils.addon.getSetting('apsortorder') if utils.addon.getSetting('apsortorder') else ''
    if not '/' + order in url:
        if '?' in url:
            pageurl = url + '&o=' + order[:-1]
        else:
            pageurl = url + order
    else:
        pageurl = url

    try:
        listhtml = utils.getHtml(pageurl, '')
    except:
        return None

    if 'class="grid mx-auto videos"' in listhtml:
        listhtml = listhtml.split('class="grid mx-auto videos"')[-1]
    else:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    match = re.compile(r'class="cell video".+?href="([^"]+)"\s*title="([^"]+)".+?data-src="([^"]+)".+?fa-clock-o"></i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        site.add_download_link(name, site.url[:-1] + videopage, 'Playvid', site.url[:-1] + img, name, duration=duration)

    nextp = re.compile(r'href="([^"]+)" class="page-link" title="Go to next page!"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        nextp = site.url[:-1] + nextp[0]
        np = re.findall(r'\d+', nextp)[-1]
        lp = re.compile(r'title="Go to last page!">(\d+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
        if lp:
            lp = '/' + lp[0]
        else:
            lp = ''
        site.add_dir('Next Page ({}{})'.format(np, lp), nextp, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url)
    if 'source src="' not in html:
        match = re.compile(r'id="player">\s*<iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
        if match:
            iframe = match[0]
            html = utils.getHtml(iframe, site.url)
    match = re.compile(r'source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if match:
        videourl = match[0] + '|Referer={}'.format(site.url)
        vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh oh', 'No video found')


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile(r'category-thumb".+?href="([^"]+)" title="([^"]+)".+?data-src="([^"]+)".+?class="fa fa-video-camera"></i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + count.strip() + "[/COLOR]"
        if int(count.strip()) > 0:
            site.add_dir(name, site.url[:-1] + catpage, 'List', site.url[:-1] + img)
    utils.eod()


@site.register()
def Lists(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile(r'class="playlist-thumb".+?href="([^"]+)" title="([^"]+)".+?data-src="([^"]+)".+?class="fa fa-video-camera"></i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + count.strip() + "[/COLOR]"
        if int(count.strip()) > 0:
            site.add_dir(name, site.url[:-1] + catpage, 'List', site.url[:-1] + img)
    nextp = re.compile(r'href="([^"]+)" class="page-link" title="Go to next page!"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if nextp:
        nextp = site.url[:-1] + nextp[0]
        np = re.findall(r'\d+', nextp)[-1]
        site.add_dir('Next Page ({})'.format(np), nextp, 'Lists', site.img_next)

    # match = re.compile(r'a href="(/videos/[^"]+)" title="([^"]+)">', re.DOTALL | re.IGNORECASE).findall(cathtml)
    # for page, name in match:
    #     if name.startswith('Go to'):
    #         continue
    #     site.add_dir(name, site.url[:-1] + page, 'List', site.img_cat)
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
def Sortorder(url):
    sort_orders = {'Recent': '', 'Most viewed': 'viewed/', 'Top rated': 'rated/', 'Most favorited': 'favorited/', 'Recently watched': 'watched/', 'Longest': 'longest/'}
    order = utils.selector('Select category', sort_orders.keys())
    if order:
        utils.addon.setSetting('apsortorder', sort_orders[order])
        xbmc.executebuiltin('Container.Refresh')

'''
    Cumination
    Copyright (C) 2021 Team Cumination

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

site = AdultSite('herexxx', '[COLOR hotpink]HereXXX[/COLOR]', 'https://herexxx.com/', 'https://herexxx.com/templates/defboot/images/logo.png?t=1561455885', 'herexxx')
site1 = AdultSite('asstoo', '[COLOR hotpink]Asstoo[/COLOR]', 'https://asstoo.com/', 'https://asstoo.com/templates/defboot/images/logo.png?t=1603875063', 'asstoo')


def getBaselink(url):
    if 'herexxx.com' in url:
        siteurl = site.url
    elif 'asstoo.com' in url:
        siteurl = site1.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    sort_orders = {'Recent': '', 'Most viewed': 'viewed/', 'Top rated': 'rated/', 'Most favorited': 'favorited/', 'Recently watched': 'watched/', 'Longest': 'longest/'}
    order = utils.addon.getSetting('heresortorder') if utils.addon.getSetting('heresortorder') else ''
    ordername = list(sort_orders.keys())[list(sort_orders.values()).index(order)]
    site.add_dir('[COLOR hotpink]Sort Order: [/COLOR] [COLOR orange]{}[/COLOR]'.format(ordername), siteurl, 'Sortorder', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Lists[/COLOR]', siteurl, 'Lists', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/video/?s=', 'Search', site.img_search)
    List(siteurl + 'videos/')
    utils.eod()


@site.register()
def List(url):
    siteurl = getBaselink(url)
    order = utils.addon.getSetting('heresortorder') if utils.addon.getSetting('heresortorder') else ''
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

    match = re.compile(r'class="video".+?href="([^"]+)"\s*title="([^"]+)".+?src="([^"]+)".+?class="duration"><strong>([^<]+)<\/strong>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, hd, duration in match:
        name = utils.cleantext(name)
        site.add_download_link(name, siteurl[:-1] + videopage, 'Playvid', siteurl[:-1] + img, name, duration=duration, quality=hd)

    nextp = re.compile(r'href="([^"]+)" class="prevnext" title="Go to next page!"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        nextp = siteurl[:-1] + nextp[0]
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
    vp = utils.VideoPlayer(name, download, 'source src="([^"]+)"')
    vp.play_from_site_link(url)


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile(r'li id=".+?href="([^"]+)" title="([^"]+)".+?src="([^"]+)".+?class="fa fa-video-camera"></i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " + count.strip() + "[/COLOR]"
        if int(count.strip()) > 0:
            site.add_dir(name, siteurl[:-1] + catpage, 'List', siteurl[:-1] + img)
    utils.eod()


@site.register()
def Lists(url):
    siteurl = getBaselink(url)
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile(r'a href="(/videos/[^"]+)" title="([^"]+)">', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for page, name in match:
        if name.startswith('Go to'):
            continue
        site.add_dir(name, siteurl[:-1] + page, 'List', site.img_cat)
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
        utils.addon.setSetting('heresortorder', sort_orders[order])
        xbmc.executebuiltin('Container.Refresh')

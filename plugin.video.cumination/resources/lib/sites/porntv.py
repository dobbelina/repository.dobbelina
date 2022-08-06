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
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
from collections import OrderedDict

site = AdultSite('porntv', '[COLOR hotpink]Porn TV[/COLOR] - Porn TV Network', 'https://www.porntv.com/', 'https://cdn1.images.ptvvideos.com/dart/logo.png', 'porntv')
site1 = AdultSite('youngpornvideos', '[COLOR hotpink]Young Porn Videos[/COLOR] - Porn TV Network', 'https://www.youngpornvideos.com/', 'https://cdn1.images.ypvcdn.com/dart/logo.png', 'youngpornvideos')
site2 = AdultSite('cartoonpornvideos', '[COLOR hotpink]Cartoon Porn Videos[/COLOR] - Porn TV Network', 'https://www.cartoonpornvideos.com/', 'https://cdn1.images.cartoonpornvideos.com/dart/logo.png', 'cartoonpornvideos')
site3 = AdultSite('lesbianpornvideos', '[COLOR hotpink]Lesbian Porn Videos[/COLOR] - Porn TV Network', 'https://www.lesbianpornvideos.com/', 'https://cdn1.images.lesbianpornvideos.com/dart/logo.png', 'lesbianpornvideos')
site4 = AdultSite('ghettotube', '[COLOR hotpink]Ghetto Tube[/COLOR] - Porn TV Network', 'https://www.ghettotube.com/', 'https://cdn1.images.ghettotube.com/dart/logo.png', 'ghettotube')
site5 = AdultSite('asspoint', '[COLOR hotpink]Ass Point[/COLOR] - Porn TV Network', 'https://www.asspoint.com/', 'https://cdn1.images.asspoint.com/dart/logo.png', 'asspoint')
site6 = AdultSite('mobilepornmovies', '[COLOR hotpink]Mobile Porn Movies[/COLOR] - Porn TV Network', 'https://www.mobilepornmovies.com/', 'https://cdn1.images.mobilepornmovies.com/dart/logo.png', 'mobilepornmovies')
site7 = AdultSite('asianpornmovies', '[COLOR hotpink]Asian Porn Movies[/COLOR] - Porn TV Network', 'https://www.asianpornmovies.com/', 'https://cdn1.images.asianpornmovies.com/dart/logo.png', 'asianpornmovies')
site8 = AdultSite('sexoasis', '[COLOR hotpink]Sex Oasis[/COLOR] - Porn TV Network', 'https://www.sexoasis.com/', 'https://cdn1.images.sexoasis.com/dart/logo.png', 'sexoasis')
site9 = AdultSite('movieshark', '[COLOR hotpink]Movie Shark[/COLOR] - Porn TV Network', 'https://www.movieshark.com/', 'https://www.movieshark.com/images/dart/logo.png', 'movieshark')


def getBaselink(url):
    if 'porntv.com' in url:
        siteurl = site.url
    elif 'youngpornvideos.com' in url:
        siteurl = site1.url
    elif 'cartoonpornvideos.com' in url:
        siteurl = site2.url
    elif 'lesbianpornvideos.com' in url:
        siteurl = site3.url
    elif 'ghettotube.com' in url:
        siteurl = site4.url
    elif 'asspoint.com' in url:
        siteurl = site5.url
    elif 'mobilepornmovies.com' in url:
        siteurl = site6.url
    elif 'asianpornmovies.com' in url:
        siteurl = site7.url
    elif 'sexoasis.com' in url:
        siteurl = site8.url
    elif 'movieshark.com' in url:
        siteurl = site9.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
@site5.register(default_mode=True)
@site6.register(default_mode=True)
@site7.register(default_mode=True)
@site8.register(default_mode=True)
@site9.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories/', 'Categories', site.img_cat)
    if 'cartoonpornvideos' in siteurl:
        site.add_dir('[COLOR hotpink]Characters[/COLOR]', siteurl + 'characters/', 'Pornstars', site.img_cat)
    else:
        site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + 'pornstars/', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', siteurl + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/video/', 'Search', site.img_search)
    if 'lesbianpornvideos' in siteurl:
        List(siteurl + 'videos/all-recent.html?min_duration=0')
    else:
        List(siteurl + 'videos/straight/all-recent.html?min_duration=0')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url)
    if 'Page not found!' in html or 'No files matching your search criteria were found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<div class="outer-item">'
    delimiter = '<div class="thumb-ratio">'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = '"lazy" src="([^"]+)"'
    re_quality = 'class="flag-hd">([^<]+)<'
    re_duration = 'class="time">([^<]+)<'
    utils.videos_list(site, 'porntv.Playvid', html, delimiter, re_videopage, re_name, re_img, re_quality=re_quality, re_duration=re_duration, contextm='porntv.Related')
    re_npurl = r'href="([^"]+)"\s*class="next"'
    re_npnr = r'(\d+)\D+>Next'
    re_lpnr = 'class="total_pages">([^<]+)<'
    utils.next_page(site, 'porntv.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='porntv.GotoPage')
    utils.eod()


@site.register()
def ListRel(url):
    siteurl = getBaselink(url)
    posturl = siteurl + 'stp/ajax.php'
    a0 = 'S' + url.split('-')[-1].split('.')[0]
    formdata = OrderedDict()
    formdata['xjxfun'] = 'related_videos'
    formdata['xjxr'] = 1653140769918
    formdata['xjxargs[0]'] = a0
    formdata['xjxargs[1]'] = 'N1'
    formdata['xjxargs[2]'] = 'N36'
    html = utils.postHtml(posturl, form_data=formdata)
    delimiter = '<div class="outer-item">'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = '"lazy" src="([^"]+)"'
    re_quality = 'class="flag-hd">([^<]+)<'
    re_duration = 'class="time">([^<]+)<'
    utils.videos_list(site, 'porntv.Playvid', html, delimiter, re_videopage, re_name, re_img, re_quality=re_quality, re_duration=re_duration, contextm='porntv.Related')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        url = url.replace('-{}.html'.format(np), '-{}.html'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('porntv.ListRel') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Letters(url):
    letters = ['#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    letter = utils.selector('Select letter', letters)
    if letter:
        Categories(url, letter)


@site.register()
def Categories(url, letter=None):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    if letter:
        cathtml = cathtml.split('class="category-letter">{}<'.format(letter))[1].split('class="category-letter">')[0]
        items = re.compile(r'href="([^"]+)">([^<]+).+?quantity">(\s\d+)', re.DOTALL).findall(cathtml)
        for catpage, name, count in items:
            name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
            catpage = siteurl[:-1] + catpage
            site.add_dir(name, catpage, 'List')
    else:
        site.add_dir('[COLOR violet]Tags[/COLOR]', url, 'Letters', site.img_next)
        items = re.compile(r'class="item\s*video.+?src="([^"]+).+?href="([^"]+).+?>([^<]+).+?<h2>(\d+)', re.DOTALL).findall(cathtml)
        for img, catpage, name, count in items:
            name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
            site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Pornstars(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    items = re.compile(r'class="item".+?src="([^"]+).+?href="([^"]+).+?>([^<]+).+?videos"[^\d]+([\d]+)', re.DOTALL).findall(cathtml.split('<!-- alphabetical -->')[-1])
    for img, catpage, name, count in items:
        name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Channels(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    items = re.compile(r'class="item".+?src="([^"]+).+?href="([^"]+).+?>([^<]+).+?videos[^\d]+([\d]+)', re.DOTALL).findall(cathtml)
    for img, catpage, name, count in items:
        name = utils.cleantext(name) + " [COLOR orange][I]{0} videos[/I][/COLOR]".format(count)
        site.add_dir(name, catpage + 'videos/', 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=None, direct_regex=r'(?:sources:\s*\[\{\s*file:\s*|<source\s*src=)"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_site_link(url)

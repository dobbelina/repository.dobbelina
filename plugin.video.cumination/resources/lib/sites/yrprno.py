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

site = AdultSite('yrprno', "[COLOR hotpink]YrPrno[/COLOR]", 'https://www.yrprno.com/', 'yrprno.png', 'yrprno')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'channels/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'most-recent/')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if 'Sorry, no results were found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<div class="well well-sm"'
    re_videopage = 'class="video-link" href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = '<div class="duration">([^<]+)<'
    re_quality = '>HD<'
    skip = '=modelfeed'
    utils.videos_list(site, 'yrprno.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm='yrprno.Related', skip=skip)

    re_npurl = r'''href=['"]([^'"]+)['"]\s*class="prevnext">Next'''
    re_npnr = r'''href=['"]page(\d+)\.html['"]\s*class="prevnext">Next'''
    utils.next_page(site, 'yrprno.List', html, re_npurl, re_npnr, baseurl=url.split('page')[0], contextm='yrprno.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page{}.html'.format(np), 'page{}.html'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('yrprno.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<a href="([^"]+)" title="([^"]+)">', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r'source src="([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url, ignoreCertificateErrors=True)
    vp.play_from_html(videohtml)

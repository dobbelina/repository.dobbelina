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

site = AdultSite('netfapx', '[COLOR hotpink]Netfapx[/COLOR]', 'https://netfapx.com/', 'https://netfapx.com/wp-content/uploads/2017/11/netfapx-lg-1_319381e1f227e13ae1201bfa30857622.png', 'netfapx')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories & Tags[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstar/?orderby=popular', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?orderby=newest')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    if '>No posts found.<' in html or 'Sorry, the page you were looking for was not found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<article class="pinbox"'
    re_videopage = 'class="thumb">.+?href="([^"]+)"'
    re_name = 'class="title".+?title="([^"]+)"'
    re_img = 'img.+?src="([^"]+)"'
    re_duration = r'title="Duration">([\d:]+)'
    utils.videos_list(site, 'netfapx.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration)

    re_npurl = r'href="([^"]+)"\s*class="next">Next'
    re_npnr = r'/page/(\d+)\D+class="next">Next'
    utils.next_page(site, 'netfapx.List', html, re_npurl, re_npnr, videos_per_page=30, contextm='netfapx.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    cathtml = cathtml.split('class="infovideo-cat"')
    match = re.compile(r'href="([^"]+)"><img width="\d+" height="\d+" src="([^"]+)">', re.IGNORECASE | re.DOTALL).findall(cathtml[0])
    for caturl, img in match:
        name = img.split('/')[-1].split('.')[0].replace('-', ' ')
        site.add_dir(name, caturl, 'List', img)
    match = re.compile(r'a href="([^"]+)"[^>]+>([^<]+)</a>', re.IGNORECASE | re.DOTALL).findall(cathtml[1].split('class="footerbar"')[0])
    for caturl, name in match:
        site.add_dir('[tag] ' + name, caturl, 'List', '')
    utils.eod()


@site.register()
def Pornstars(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="preview">.+?href="([^"]+)">.+?src="([^"]+)".+?alt="([^"]+)".+?title="Videos">(\d+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        caturl = caturl.replace('/pornstar/', '/videos/')
        name = utils.cleantext(name) + '[COLOR hotpink] ({} videos)[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', img)

    re_npurl = r'href="([^"]+)"\s*class="next">Next'
    re_npnr = r'/page/(\d+)\D+class="next">Next'
    utils.next_page(site, 'netfapx.Pornstars', cathtml, re_npurl, re_npnr, contextm='netfapx.GotoPage')
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
    vp = utils.VideoPlayer(name, download, direct_regex='source src="([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'source src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        videolink = match[0]
        vp.play_from_direct_link(videolink + '|verifypeer=false')
    else:
        utils.notify('Oh Oh', 'No Videos found')

'''
    Cumination
    Copyright (C) 2020 Whitecream

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite("erome", "[COLOR hotpink]Erome[/COLOR]", "https://www.erome.com/", "https://www.erome.com/img/logo-erome-horizontal.png", "erome")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?o=new&q=', 'Search', site.img_search)
    # site.add_dir('[COLOR hotpink]Search user[/COLOR]', site.url, 'Search_user', site.img_search)
    List(site.url + 'explore/new')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    albums = listhtml.split(' id="album-')
    for album in albums:

        match = re.search(r'''title"\s*href="([^"]+)"\s*>([^<]+)''', album, re.DOTALL | re.IGNORECASE)
        if match:
            iurl = match.group(1)
            name = utils.cleantext(match.group(2))
        else:
            continue
        img = re.search(r'src="([^"]+)', album, re.DOTALL | re.IGNORECASE)
        img = img.group(1) if img else ''
        img += '|Referer={0}'.format(site.url)
        pics = False
        vids = False
        if 'class="album-user"' in album:
            user = re.findall(r'<span class="album-user"\s*>([^<]+)<', album, re.DOTALL | re.IGNORECASE)[0]
            user = utils.cleantext(user)
            name = name + ' [by {} - '.format(user)
        if '"album-videos"' in album:
            items = re.findall(r'class="album-videos"[^\d]+(\d+)', album)[0]
            name += '[COLOR hotpink][I] {0} vids[/I][/COLOR]'.format(items)
            vids = True
        if '"album-images"' in album:
            items = re.findall(r'class="album-images"[^\d]+(\d+)', album)[0]
            name += '[COLOR orange][I] {0} pics[/I][/COLOR]'.format(items)
            pics = True
        cm = []
        if 'class="album-user"' in album:
            name += ' ]'
            cm_user = (utils.addon_sys + "?mode=" + str('erome.Related') + "&url=" + urllib_parse.quote_plus(site.url + user + '?t=posts'))
            cm = [('[COLOR deeppink]Author page [{}][/COLOR]'.format(user), 'RunPlugin(' + cm_user + ')')]

        if pics and vids:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='both', contextm=cm)
        elif pics:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='pics', contextm=cm)
        elif vids:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='vids', contextm=cm)

    re_npurl = r'<li class="active"><span>\d+</span></li>\s+<li><a href="([^"]+)">'
    re_npnr = r'<li class="active"><span>\d+</span></li>\s+<li><a href="[^"]+">(\d+)<'
    re_lpnr = r'>(\d+)</a></li>\s+<li><a href="[^"]+"\s+rel="next"'
    utils.next_page(site, 'erome.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='erome.GotoPage', baseurl=url.split('?')[0])
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'page={}'.format(np), r'page={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "erome.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def List2(url, section):
    if section == 'both':
        site.add_dir('Photos', url, 'List2', '', section='pics')
        site.add_dir('Videos', url, 'List2', '', section='vids')
    else:
        listhtml = utils.getHtml(url, site.url)
        items = listhtml.split('<div class="media-group')
        if len(items) > 1:
            items.pop(0)
            itemcount = 0
            for item in items:
                item = item.split('class="clearfix"')[0]
                if 'class="video"' in item and section == 'vids':
                    itemcount += 1
                    img, surl, hd, duration = re.findall(r'''poster="([^"]+).+?source\s*src="([^"]+).+?label='([^']+).+?class="duration"\s*>([^<]+)''', item, re.DOTALL)[0]
                    img += '|Referer={0}'.format(site.url)
                    surl += '|Referer={0}'.format(site.url)
                    site.add_download_link('Video {0}'.format(itemcount), surl, 'Playvid', img, duration=duration, quality=hd)
                elif 'class="video"' not in item and section == 'pics':
                    img = re.search(r'class="img-front(?:\s*lasyload)?"\s*(?:data-)?src="([^"]+)', item, re.DOTALL)
                    if img:
                        itemcount += 1
                        img = img.group(1) + '|Referer={0}'.format(site.url)
                        site.add_img_link('Photo {0}'.format(itemcount), img, 'Showpic')

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))


@site.register()
def Search_user(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search_user')
    else:
        List(url + keyword.replace(' ', '+') + '?t=posts')


@site.register()
def Showpic(url, name):
    utils.showimage(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(url)


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('erome.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

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
from resources.lib import utils
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
from kodi_six import xbmcgui, xbmcplugin

site = AdultSite('heroero', "[COLOR hotpink]Heroero[/COLOR]", 'https://heroero.com/', 'https://www.heroero.com/images/logo.png', 'heroero')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Actress[/COLOR]', site.url + 'actress/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'see/{}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={}&category_ids=&sort_by=&from_videos=1&from_albums=1', 'Search', site.img_search)

    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)

    delimiter = 'class="item  "'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = 'item-panel-col">([^<]+)<'
    re_quality = '>HD<'
    utils.videos_list(site, 'heroero.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm='heroero.Related')

    if '?' in url:
        match = re.compile(r'\D(\d+)">Next<', re.IGNORECASE | re.DOTALL).findall(listhtml)
        if match:
            npage = int(match[0])
            match = re.compile(r'\D(\d+)">Last<', re.IGNORECASE | re.DOTALL).findall(listhtml)
            lastp = '/' + match[0] if match else ''
            nurl = re.sub(r'([&?])from([^=]*)=(\d+)', r'\1from\2={0:02d}', url).format(npage)
            site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, npage)
    else:
        re_npurl = 'class="next"><a href="([^"]+)"'
        re_npnr = r'class="next"><a href="[^"]+/(\d+)/"'
        re_lpnr = r'class="last"><a href="[^"]+/(\d+)/"'
        utils.next_page(site, 'heroero.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='heroero.GotoPage')
    utils.eod()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('heroero.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = url.format(title, title)
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="item" href="([^"]+)" title="([^"]+)".+?(?:src="([^"]+)"|>no image<)(.+?)</a>', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, img, data in match:
        img = img.replace(' ', '%20')
        name = utils.cleantext(name)
        if '/categories/' in url:
            name = name.capitalize()
        if 'videos">' in data:
            match = re.compile(r'videos">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(data)
            name = name + ' [COLOR cyan][{}][/COLOR]'.format(match[0])
        site.add_dir(name, caturl, 'List', img)
    re_npurl = r'class="next"><a href="([^"]+)"'
    re_npnr = r'class="next"><a href="[^"]+/(\d+)/"'
    re_lpnr = r'class="last"><a href="[^"]+/(\d+)/"'
    utils.next_page(site, 'heroero.Categories', cathtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='heroero.GotoPage')
    if '/categories/' in url:
        xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url)
    surl = re.search(r"video_url:\s*'([^']+)'", html)
    if surl:
        surl = surl.group(1)
        if surl.startswith('function/'):
            license = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, license)
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(surl)


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if url.endswith('/{}/'.format(np)):
            url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')

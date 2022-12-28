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

site = AdultSite('tnaflix', "[COLOR hotpink]T'nAflix[/COLOR]", 'https://www.tnaflix.com/', 'tnaflix.png', 'tnaflix')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars?filters[sorting]=2&filter_set=true', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/all/most-viewed/1', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search.php?what=', 'Search', site.img_search)
    List(site.url + 'new/?d=all&period=all')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if 'No results found matching your criteria.' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = "data-vid='"
    re_videopage = "'thumb no_ajax' href='([^']+)'"
    re_name = 'alt="([^"]+)"'
    re_img = "data-original='([^']+)'"
    re_quality = 'class="hdIcon">([^<]+)<'
    re_duration = "class='videoDuration'>([^<]+)<"
    utils.videos_list(site, 'tnaflix.Playvid', html, delimiter, re_videopage, re_name, re_img, re_quality=re_quality, re_duration=re_duration, contextm='tnaflix.Related')

    re_npurl = r'link rel="next"\s*href="([^"]+)"'
    if '/video' in url:
        re_npnr = r'rel="next"\s*href="[^"]+page=(\d+)\D*"'
    else:
        re_npnr = r'link rel="next"\s*href="[^\"]+?(\d+)\?*[^"]*"'
    utils.next_page(site, 'tnaflix.List', html, re_npurl, re_npnr, contextm='tnaflix.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}?'.format(np), '/{}?'.format(pg))
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        if url.endswith('/{}'.format(np)):
            url = url.replace('/{}'.format(np), '/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('tnaflix.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="thumb[^"]*"\s*href="([^"]+)".+?(?:img src|data-original)="([^"]+)".+?class="vidcountSp">([\d,]+)<.+?title="[^"]*">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, count, name in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({} videos)[/COLOR]'.format(count)
        caturl = utils.fix_url(caturl, site.url)
        img = utils.fix_url(img, site.url)
        site.add_dir(name, caturl, 'List', img)
    re_npurl = r'rel="next"\s*href="([^"]+)"'
    if '/pornstars' in url:
        re_npnr = r'rel="next"\s*href="[^"]+page=(\d+)\D*"'
    else:
        re_npnr = r'rel="next"\s*href="[^"]+/(\d+)"'
    utils.next_page(site, 'tnaflix.Categories', cathtml, re_npurl, re_npnr, contextm='tnaflix.GotoPage')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}&tab=".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'itemprop="embedUrl"\s*content="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        embedurl = match[0]
        embedhtml = utils.getHtml(embedurl, url)
        match = re.compile(r'config\s*=\s*"([^"]+)"', re.IGNORECASE | re.DOTALL).findall(embedhtml)
        if match:
            videourl = 'https:' + match[0] if match[0].startswith('//') else site.url + match[0] if match[0].startswith('/') else match[0]
            html = utils.getHtml(videourl, embedurl, ignoreCertificateErrors=True)
            match = re.compile(r'<res>([^<]+)</res>\s*<videoLink><!\[CDATA\[([^]]+)\]', re.IGNORECASE | re.DOTALL).findall(html)
            if match:
                videoArray = {x[0].split('_')[0]: x[1] for x in match}
                videourl = utils.prefquality(videoArray, sort_by=lambda x: int(x[:-1]), reverse=True)

                if videourl:
                    videourl = 'https:' + videourl if videourl.startswith('//') else videourl
                    vp.play_from_direct_link(videourl)

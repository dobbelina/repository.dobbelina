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
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('tubxporn', "[COLOR hotpink]TubXporn[/COLOR]", 'https://tubxporn.xxx/', 'https://tubxporn.xxx/images/logo.png?v1', 'tubxporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?q=', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    try:
        html = utils.getHtml(url, site.url)
    except:
        html = utils._getHtml(str(url) + '?label_W9dmamG9w9zZg45g93FnLAVbSyd0bBDv=1', site.url)
    if 'There are no videos in the list' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<div class="inner">'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = r'src=\s*"https:([^"]+)"'
    re_duration = 'class="length">([^<]+)<'
    skip = 'www.rexporn.com'
    utils.videos_list(site, 'tubxporn.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='tubxporn.Related', skip=skip)

    re_npurl = r'<a href="([^"]+)"\s+class="mobnav">Next<'
    re_npnr = r'<a href="[^"]+/(\d+)(?:/\?[^"]+|/)"\s+class="mobnav">Next<'
    re_lpnr = r'<a href="[^"]+">(\d+)</a></span>\s*</div>'
    utils.next_page(site, 'tubxporn.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, baseurl=url.split('page')[0], contextm='tubxporn.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}/'.format(np), '/{}/'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=tubxporn.List&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<div class="item".+?href="([^"]+)".+?<img src="([^"]+)".+?>([^<]+)\s+\((\d+)\)</a></h2>', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({} videos)[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r'(?:src:|source src=)\s*"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        videohtml = utils.getHtml(url, site.url)
    except:
        videohtml = utils._getHtml(url + '?label_W9dmamG9w9zZg45g93FnLAVbSyd0bBDv=1', site.url)
    match = re.compile(r'div data-c="([^"]+)">\D+(\d+p)<', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        sources = {x[1]: x[0] for x in match}
        videolink = utils.prefquality(sources, sort_by=lambda x: int(x[:-1]), reverse=True)
        videolink = videolink.split(';')
        videourl = 'https://s{0}.stormedia.info/whpvid/{1}/{2}/{3}/{4}/{4}_{5}.mp4'.format(videolink[7], videolink[5], videolink[6], videolink[4][:-3] + '000', videolink[4], videolink[1])
        videourl = videourl.replace('_720p', '')
        vp.play_from_direct_link(videourl)

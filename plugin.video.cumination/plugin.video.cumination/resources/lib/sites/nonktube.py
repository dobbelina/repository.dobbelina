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

site = AdultSite('nonktube', "[COLOR hotpink]NonkTube[/COLOR]", 'https://www.nonktube.com/', 'https://media.nonktube.com/theme/img/logo.png', 'nonktube')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/videos/', 'Search', site.img_search)
    List(site.url + 'videos?o=mr')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if 'the requested search cannot be found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<div class="well well-sm">'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-src="([^"]+)"'
    re_duration = '<div class="duration">([^<]+)<'
    utils.videos_list(site, 'nonktube.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='nonktube.Related')

    re_npurl = r'href="([^"]+)"\s*class="prevnext"'
    re_npnr = r'href="[^"]+page[-=](\d+)"\s*class="prevnext"'
    re_lpnr = r'>(\d+)<[^"]+"[^"]+"\s*class="prevnext"'
    utils.next_page(site, 'nonktube.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='nonktube.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page={}'.format(np), 'page={}'.format(pg)).replace('page-{}'.format(np), 'page-{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('nonktube.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}=".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex="<source src='([^']+)'")
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'property="og:video:url" content="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        embedlink = match[0]
        embedhtml = utils.getHtml(embedlink, url)
        match = re.compile(r"<source src='([^']+)'", re.IGNORECASE | re.DOTALL).findall(embedhtml)
        if match:
            videolink = match[0] + '|Referer:' + site.url
            vp.progress.update(75, "[CR]Loading video page[CR]")
            vp.play_from_direct_link(videolink)

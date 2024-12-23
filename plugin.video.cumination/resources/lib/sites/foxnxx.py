'''
    Cumination
    Copyright (C) 2024 Team Cumination

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

site = AdultSite('foxnxx', "[COLOR hotpink]Foxnxx[/COLOR]", 'https://foxnxx.com/', 'foxnxx.png', 'foxnxx')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if "Can't Found '" in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '<div class="thumb"> '
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="[^"]+">([^<]+)<'
    re_img = 'data-src="([^"]+)"'
    re_duration = 'class="timer">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('foxnxx.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('foxnxx.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'foxnxx.Playvid', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    re_npurl = r"class='active'><a>\d+</a></li><li><a href='([^']+)'>\d+<"
    re_npnr = r"class='active'><a>\d+</a></li><li><a href='[^']+'>(\d+)<"
    re_lpnr = r"'>(\d+)</a></li></ul>"
    utils.next_page(site, 'foxnxx.List', html, re_npurl, re_npnr, re_lpnr, baseurl=site.url, contextm='foxnxx.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('{}.html'.format(np), '{}.html'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('foxnxx.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}.html".format(url, keyword.replace(' ', '-'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    match = re.compile(r'class="embed-responsive-item"\s*src="([^"]+)"').findall(videohtml)
    if match:
        embedurl = match[0]
        id = embedurl.split('.')[0].split('/')[-1]
        videourl = "https://mydaddy.cc/video/" + id + "/&alt"
        vp.play_from_link_to_resolve(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Tag", r'class="tagsstyle"><a href="(/tags/[^"]+)">([^<]+)</a>', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'foxnxx.List', lookup_list)
    lookupinfo.getinfo()

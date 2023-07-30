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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import json

site = AdultSite('drtuber', '[COLOR hotpink]DrTuber[/COLOR]', 'https://www.drtuber.com/', 'drtuber.png', 'drtuber')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/videos/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]HD[/COLOR]', site.url + 'hd/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]4k[/COLOR]', site.url + '4k/', 'List', site.img_cat)

    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    listhtml = listhtml.split('</h1>')[-1]

    delimiter = ' <a href="/video'
    re_videopage = '^([^"]+)" class="'
    re_name = 'alt="([^"]+)"'
    re_img = 'src="([^"]+)"'
    re_duration = r'class="time_thumb.+?<em>([^<]+)</em>\s*</em>'
    re_quality = 'class="quality[^"]*"(?:><i class="ico_|>)([^<"]+)'
    utils.videos_list(site, 'drtuber.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality)

    re_npurl = 'href="([^"]+)">Next'
    re_npnr = r'/(\d+)">Next'
    re_lpnr = r'>(\d+)[^=]+="next"'

    utils.next_page(site, 'drtuber.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='drtuber.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}'.format(np), '/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<li class="item"> <a href="([^"]+)"> <span>([^<]+)</span> <b>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name, count in match:
        name = utils.cleantext(name + ' ' + count)
        site.add_dir(name, site.url + caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    videoid = url.replace(site.url, '').split('/')[0]

    jsonurl = site.url + 'player_config_json/?vid={}&aid=0&domain_id=0&embed=0&ref=null&check_speed=0'.format(videoid)
    jsondata = utils.getHtml(jsonurl, site.url)
    data = json.loads(jsondata)
    videos = data["files"]
    srcs = {}
    for v in videos:
        if videos[v]:
            if v == 'lq':
                srcs['480p'] = videos[v]
            elif v == 'hq':
                srcs['720p'] = videos[v]
            elif v == '4k':
                srcs['2160p'] = videos[v]

    video = utils.prefquality(srcs, sort_by=lambda x: int(x[:-1]), reverse=True)
    if video:
        vp.play_from_direct_link(video)

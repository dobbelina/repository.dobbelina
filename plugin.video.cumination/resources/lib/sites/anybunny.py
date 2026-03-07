'''
    Cumination
    Copyright (C) 2015 Whitecream

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

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc
import xbmcgui


site = AdultSite("anybunny", "[COLOR hotpink]Anybunny[/COLOR]", "http://anybunny.org/", "anybunny.png", "anybunny")


@site.register(default_mode=True)
def Main():
    # site.add_dir('[COLOR hotpink]Categories - images[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - all[/COLOR]', site.url, 'Categories2', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'new/', 'Search', site.img_search)
    # List(site.url + 'new/twins')
    Categories(site.url)
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        utils.notify(msg='No videos found!')
        return

    delimiter = r"<li\s+data-id='|class='nuyrfe"
    re_videopage = "href='([^']+)'"
    re_name = "alt='([^']+)'"
    re_img = r"src='([^']+)'"
    re_duration = r"'>([\d:]+)</div>"
    re_quality = r"'>(HD)\s*</div>"

    cm = []
    cm_related = (utils.addon_sys + "?mode=anybunny.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'anybunny.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    re_npurl = 'href="([^"]+)">Next'
    re_npnr = r'\?p=(\d+)">Next'
    utils.next_page(site, 'anybunny.List', listhtml, re_npurl, re_npnr, contextm='anybunny.GotoPage')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r"<iframe.+?src='([^']+)'")
    vpage = utils.getHtml(url, site.url)
    if not re.match(r'id:\s*"player",\s*file:', vpage, re.DOTALL | re.IGNORECASE):
        match = re.search(r"<iframe.+?src='([^']+)'", vpage, re.DOTALL | re.IGNORECASE)
        if match:
            iframe_url = match.group(1)
            vpage = utils.getHtml(iframe_url, site.url)

    file = re.search(r'file:\s*"([^"]+")', vpage, re.DOTALL | re.IGNORECASE)
    if not file:
        return
    match = re.compile(r'\[(\d+)\](.+?)[,"]', re.DOTALL | re.IGNORECASE).findall(file.group(1))
    if match:
        sources = {quality: video_url for quality, video_url in match}
        video_url = utils.prefquality(sources, sort_by=lambda x: int(x), reverse=True)
    else:
        video_url = re.search(r'file:\s*["]([^"]+)', vpage, re.DOTALL | re.IGNORECASE)
        if video_url:
            video_url = video_url.group(1)

    if video_url:
        video_url = video_url.split(' or ')[-1].split(":cast:")[0]
        vp.play_from_direct_link(video_url + '|referer={0}'.format(url))


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("href='/top/([^']+)'>.*?src='([^']+)' alt='([^']+)'", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match = sorted(match, key=lambda x: x[2])
    for catid, img, name in match:
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Categories2(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r"href='/top/([^']+)'>([^<]+)</a> <a>([^)]+\))", re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catid, name, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '_'))


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'\?p=\d+', r'?p={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "anybunny.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('anybunny.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

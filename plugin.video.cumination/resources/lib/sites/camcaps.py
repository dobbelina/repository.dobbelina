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
from resources.lib import utils
from resources.lib.jsunpack import unpack
from resources.lib.adultsite import AdultSite
import xbmc
import xbmcgui
from six.moves import urllib_parse


site = AdultSite('camcaps', '[COLOR hotpink]Camcaps[/COLOR]', 'https://camcaps.tv/', 'camcaps', 'camcaps')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/videos/', 'Search', site.img_search)
    List(site.url + 'videos?o=mr')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')

    delimiter = 'col-sm-6|article class="thumb"'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'img src="([^"]+)"'
    re_duration = r'"dur-icon">([\d:]+)'

    utils.videos_list(site, 'camcaps.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration)

    re_npurl = r'<a class="active".+?<a href="([^"]+)"'
    re_npnr = r'<a class="active".+?<a href="[^"]+">(\d+)<'
    re_lpnr = r'>(\d+)</a>\s*<a class="next"'

    utils.next_page(site, 'camcaps.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='camcaps.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'<article class="thumb.+?href="([^"]+)".+?img src="([^"]+)"\stitle="([^"]+)".+?class="videos-icon">(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, videos in match:
        name = utils.cleantext(name.strip()).title() + " [COLOR deeppink] (" + videos + " videos)[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)

    match = re.compile(r'class="video-embedded">\s*<iframe[^>]+src="(http[^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    if match:
        refurl = match[0]
        if '/vtplayer.net/' in refurl:
            refurl = refurl.replace('embed-', '')
        if vp.resolveurl.HostedMediaFile(refurl):
            vp.play_from_link_to_resolve(refurl)
            return
        refpage = utils.getHtml(refurl)
        if '/playerz/' in refurl:
            videourl = re.compile(r'"src":"\.([^"]+)"', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
            videourl = refurl.split('/ss.php')[0] + videourl
            videourlpage = utils.getHtml(videourl)
            vp.direct_regex = '{"file":"([^"]+)"'
            vp.play_from_html(videourlpage)
        else:
            videourl = re.compile(r'>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
            videourl = unpack(videourl)
            match = re.compile('(?:src|file):"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videourl)
            if match:
                videolink = match[0] + '|Referer=' + refurl + '&verifypeer=false'
                if videolink.startswith('/') and 'vidello' in refurl:
                    videolink = 'https://oracle.vidello.net' + videolink
                vp.play_from_direct_link(videolink)
    else:
        vp.play_from_html(videopage)

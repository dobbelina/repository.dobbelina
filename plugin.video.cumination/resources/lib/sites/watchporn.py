'''
    Cumination
    Copyright (C) 2024 Cumination

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
from resources.lib.decrypters.kvsplayer import kvs_decode
import time


site = AdultSite('watchporn', '[COLOR hotpink]WatchPorn[/COLOR]', 'https://watchporn.to/', 'https://watchporn.to/contents/djifbwwmsrbs/theme/logo.png', 'watchporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    if '?' not in url and '/categories/' in url:
        tm = int(time.time() * 1000)
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&_=' + str(tm)
    listhtml = utils.getHtml(url)

    delimiter = '<div class="item  ">'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = '"duration">([^<]+)<'
    re_quality = 'class="is[^"]+">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('watchporn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('watchporn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'watchporn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        tm = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(tm))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=watchporn.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&listmode=watchporn.List")
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(url, np, listmode):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + listmode + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = '{}{}/'.format(searchUrl, keyword.replace(' ', '-'))
        List(searchUrl)


@site.register()
def Categories(url):
    tm = int(time.time() * 1000)
    url = url + str(tm)
    cathtml = utils.getHtml(url)

    match = re.compile(r'class="item"\shref="([^"]+)"\stitle="([^"]+)".+?((?:src="[^"]+jpg|>no image<)).+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"
        img = None if '>no image<' in img else img.split('src="')[1]
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)

    match = re.compile(r"video(?:_|_alt_)url\d*: '([^']+)'.+?video(?:_|_alt_)url\d*_text: '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)

    sources = {}
    if match:
        for video in match:
            sources[video[1]] = video[0]
    vp.progress.update(75, "[CR]Video found[CR]")

    videourl = utils.prefquality(sources, sort_by=lambda x: int(x.replace(' 4k', '')[:-1]), reverse=True)
    if videourl:
        if videourl.startswith('function'):
            license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
            videourl = kvs_decode(videourl, license)

        vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Category", r'<a href="https://watchporn.to/(categories[^"]+)">([^<]+)<', ''),
        ("Tag", r'<a href="https://watchporn.to/(tags[^"]+)">([^<]+)<', ''),
        ("Model", r'<a href="https://watchporn.to/(models[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'watchporn.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('watchporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

'''
    Cumination
    Copyright (C) 2023 Cumination

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
from random import randint

site = AdultSite('whoreshub', '[COLOR hotpink]WhoresHub[/COLOR]', 'https://www.whoreshub.com/', 'whoreshub.png', 'whoreshub')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/?mode=async&function=get_block&block_id=list_models_models_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR]', site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by=last_content_date&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    if '?' not in url and ('/categories/' in url or '/models/' in url):
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&_=' + str(1000000000000 + randint(0, 999999999999))

    listhtml = utils.getHtml(url)

    if '/playlists/' in url:
        delimiter = r'<div class="thumb">\s+<div class="box">'
        re_videopage = '<a href="([^"]+)"'
        re_name = 'alt="([^"]+)"'
        re_img = 'data-src="([^"]+)"'
        re_duration = None
        re_quality = None
    else:
        delimiter = 'class="box"><a class="'
        re_videopage = 'item" href="([^"]+)"'
        re_name = 'title="([^"]+)"'
        re_img = 'data-src="([^"]+)"'
        re_duration = '"duration">([^<]+)<'
        re_quality = '"is-hd">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('whoreshub.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('whoreshub.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'whoreshub.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    match = re.search(r'class="current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        rnd = 1000000000000 + randint(0, 999999999999)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=whoreshub.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&listmode=whoreshub.List")
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
def ListPL(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="item.+?item="([^"]+).+?original="([^"]+).+?title">\s*([^<\n]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'Playvid', img, name)

    nextp = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        pg = int(np) - 1
        if 'from={0:02d}'.format(pg) in url:
            next_page = url.replace('from={0:02d}'.format(pg), 'from={0:02d}'.format(int(np)))
        else:
            next_page = url + '{0}/'.format(np)
        lp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('Next Page (' + np + lp + ')', next_page, 'ListPL', site.img_next)

    utils.eod()


@site.register()
def Playlist(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="item.+?href="([^"]+).+?data-original="([^"]+).+?title">\s*([^<\n]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for lpage, img, name, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] {0}[/COLOR]".format(count)
        lpage += '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=&from=01'
        site.add_dir(name, lpage, 'ListPL', img)

    nextp = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        pg = int(np) - 1
        if 'from={0:02d}'.format(pg) in url:
            next_page = url.replace('from={0:02d}'.format(pg), 'from={0:02d}'.format(int(np)))
        else:
            next_page = url + '{0}/'.format(np)
        lp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('Next Page (' + np + lp + ')', next_page, 'Playlist', site.img_next)

    utils.eod()


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
    url = url + str(1000000000000 + randint(0, 999999999999))
    cathtml = utils.getHtml(url)

    if '/playlists/' in url:
        match = re.compile(r'class="box">\s+<a href="([^"]+)".+?title="([^"]+)".+?data-src="([^"]+)".+?class="text">(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    else:
        match = re.compile(r'class="item"\shref="([^"]+)"\stitle="([^"]+)".+?src="([^"]+jpg)".+?class="text">(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in match:
        if '/models/' in url or '/playlists/' in url:
            name = utils.cleantext(name)
        else:
            name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"
        img = 'https:' + img if img.startswith('//') else img
        site.add_dir(name, catpage, 'List', img)

    match = re.search(r'class="current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', cathtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        rnd = 1000000000000 + randint(0, 999999999999)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=whoreshub.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&listmode=whoreshub.Categories")
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'Categories', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    match = re.compile(r"video(?:_|_alt_)url\d*: '([^']+)'.+?video(?:_|_alt_)url\d*_text: '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)

    sources = {}
    if match:
        for video in match:
            sources[video[1]] = video[0]
    vp.progress.update(75, "[CR]Video found[CR]")

    videourl = utils.prefquality(sources, sort_by=lambda x: int(x.replace(' 4k', '')[:-1]), reverse=True)
    if videourl:
        videourl += '|Referer=' + url
        vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Category", r'(categories/[^"]+)"\sclass="btn">([^<]+)<', ''),
        ("Tag", r'(tags/[^"]+)"\sclass="btn">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'whoreshub.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('whoreshub.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

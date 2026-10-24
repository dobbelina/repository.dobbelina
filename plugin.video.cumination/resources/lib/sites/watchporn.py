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
import time


site = AdultSite('watchporn', '[COLOR hotpink]WatchPorn[/COLOR]', 'https://watchporn.to/', 'https://watchporn.to/contents/djifbwwmsrbs/theme/logo.png', 'watchporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'sites/', 'Studios', site.img_channels)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    if '?' not in url and '/categories/' in url:
        tm = int(time.time() * 1000)
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&_=' + str(tm)
    listhtml = utils.getHtml(url)

    delimiter = '<div class="thumb item'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-webp="([^"]+)"'
    re_duration = 'class="wp-dur">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('watchporn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('watchporn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'watchporn.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    match = re.search(r'aria-current="page">(\d+)<.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        tm = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(tm))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        lpnr = 0
        lp = ''
        match = re.search(r'data-total="(\d+)"', listhtml, re.DOTALL | re.IGNORECASE)
        if match:
            lpnr = match.group(1)
            lp = '/' + str(lpnr)
        cm_page = (utils.addon_sys + "?mode=watchporn.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&lp=" + str(lpnr))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lp + ')', nurl, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=watchporn.List&url=" + urllib_parse.quote_plus(url))
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
def Studios(url):
    listhtml = utils.getHtml(url)

    studio_re = re.compile(
        r'<a\s+class="item\s+thumb"\s+href="([^"]+)"\s+title="([^"]+)">.*?'
        r'<img\s+src="([^"]+)"[^>]*>.*?'
        r'<div\s+class="thumb__info-item">.*?</svg>\s*(\d+)\s+videos.*?</div>.*?</a>',
        re.DOTALL | re.IGNORECASE
    )

    matches = studio_re.findall(listhtml)
    for studio_url, title_attr, img, videos in matches:
        name = utils.cleantext(title_attr)
        site.add_dir(
            '[COLOR hotpink]' + name + '[/COLOR] [COLOR deeppink]' + videos + ' videos[/COLOR]',
            studio_url,
            'List',
            img
        )

    # Next page support for /sites/2/, /sites/3/, etc.
    if url.rstrip('/').endswith('/sites'):
        next_url = url.rstrip('/') + '/2/'
    elif re.search(r'/sites/(\d+)/?$', url):
        page = int(re.search(r'/sites/(\d+)/?$', url).group(1))
        next_url = re.sub(r'/sites/\d+/?$', '/sites/{}/'.format(page + 1), url)
    else:
        next_url = None

    if next_url:
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR]', next_url, 'Studios', site.img_next)

    utils.eod()


@site.register()
def Categories(url):
    tm = int(time.time() * 1000)
    url = url + str(tm)
    cathtml = utils.getHtml(url)

    match = re.compile(r'class="item thumb"\shref="([^"]+)"\stitle="([^"]+)"(.+?)<div class="thumb__title"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, info in match:
        img = re.search(r'src="([^"]+jpg)', info, re.IGNORECASE | re.DOTALL)
        img = img.group(1) if img else ''
        videos = re.search(r'class="videos">([^<]+)<', info, re.IGNORECASE | re.DOTALL)
        videos = videos.group(1) if videos else ''
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, site.url)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Category", r'href="https://watchporn.to/(categories[^"]+)"\s*>([^<]+)<', ''),
        ("Tag", r'href="https://watchporn.to/(tags[^"]+)"\s*>([^<]+)<', ''),
        ("Actor", r'href="https://watchporn.to/(models[^"]+)"\s*>([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'watchporn.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('watchporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')
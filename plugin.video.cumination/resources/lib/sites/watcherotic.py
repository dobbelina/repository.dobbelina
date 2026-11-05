'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
import time
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('watcherotic', '[COLOR hotpink]WatchErotic[/COLOR]', 'https://watcherotic.com/', 'watcherotic.png', 'watcherotic')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    html = listhtml.split('>SHOULD WATCH<')[0]
    if 'There is no data in this list' in html.split('New Albums')[0]:
        utils.notify(msg='No data found')
        return

    delimiter = '<div class="thumb thumb_rel item'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = 'class="time">([^<]+)<'
    re_quality = 'class="quality">(HD)<'
    skip = '(Magazine)'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=watcherotic.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=watcherotic.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    thumbnails = True if 'watcherotic' in site.url else False
    utils.videos_list(site, 'watcherotic.Play', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm, skip=skip, thumbnails=thumbnails)

    match = re.search(r'''class="active[^>]+>([^<]+)<.+?class='next' href=\S+\sdata-action="ajax" data-container-id="[^"]+"\s+data-block-id="([^"]+)"\s+data-parameters="([^"]+)">''', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        tm = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(tm))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=watcherotic.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&list_mode=watcherotic.List")
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        url = url.replace('from={}'.format(np), 'from={}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="wp-block-tag-cloud"')[-1].split('/section>')[0]
    match = re.compile(r'<a href="([^"]+)".+?aria-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        List(url)


@site.register()
def Play(url, name, download=None):
    videohtml = utils.getHtml(url, site.url)

    vp = utils.VideoPlayer(name, download=download, regex='"file":"([^"]+)"', direct_regex='file:"([^"]+)"')
    match = re.compile(r'''<iframe[^>]+src=['"](h[^'"]+)['"]''', re.DOTALL | re.IGNORECASE).findall(videohtml)
    playerurl = match[0]
    embedhtml = utils.getHtml(playerurl, url)
    match = re.compile(r"video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(embedhtml)
    if match:
        videolink = match[0] + '|referer=' + site.url
        vp.play_from_direct_link(videolink)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Tag", r'<a href="{}(tags/[^"]+)">([^<]+)</a>'.format(site.url), ''),
        ("Actor", r'/(models/[^"]+)">.+?</i>([^<]+)</a>', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, '{}.List'.format(site.module_name), lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('watcherotic.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

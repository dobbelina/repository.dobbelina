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
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc
import xbmcgui
from random import randint

site = AdultSite('watchmdh', '[COLOR hotpink]WatchMDH[/COLOR]', 'https://watchmdh.to/', 'https://watchmdh.to/contents/playerother/theme/logo.png', 'watchmdh')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/?mode=async&function=get_block&block_id=list_models_models_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    utils.kodilog(url)
    listhtml = utils.getHtml(url)

    delimiter = 'class="item  "'
    re_videopage = '<a href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-original="([^"]+)"'
    re_duration = '"duration">([^<]+)<'
    re_quality = '"is-hd">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('watchmdh.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('watchmdh.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'watchmdh.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        rnd = 1000000000000 + randint(0, 999999999999)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        match = re.search(r'from[^:]*:(\d+)">Letzte<', listhtml, re.DOTALL | re.IGNORECASE)
        lpparam = "&lp={}".format(match.group(1)) if match else "&lp=0"
        lptxt = "/{}".format(match.group(1)) if match else ""

        cm_page = (utils.addon_sys + "?mode=watchmdh.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + lpparam + "&listmode=watchmdh.List")
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lptxt + ')', nurl, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(url, np, lp, listmode):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
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
    url = url + str(1000000000000 + randint(0, 999999999999))
    cathtml = utils.getHtml(url)

    match = re.compile(r'class="item"\shref="([^"]+)"\stitle="([^"]+)".+?"videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', '')

    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', cathtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        rnd = 1000000000000 + randint(0, 999999999999)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        match = re.search(r'from[^:]*:(\d+)">Letzte<', cathtml, re.DOTALL | re.IGNORECASE)
        utils.kodilog(match.group(1))
        lpparam = "&lp={}".format(match.group(1)) if match else "&lp=0"
        lptxt = "/{}".format(match.group(1)) if match else ""

        cm_page = (utils.addon_sys + "?mode=watchmdh.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + lpparam + "&listmode=watchmdh.Categories")
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lptxt + ')', nurl, 'Categories', site.img_next, contextm=cm)

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
    else:
        match = re.compile(r"video_url:\s+'([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)
        sources['0p'] = match[0]
    vp.progress.update(75, "[CR]Video found[CR]")
    videourl = utils.prefquality(sources, sort_by=lambda x: int(x.replace(' 4k', '')[:-1]), reverse=True)
    if videourl:
        if videourl.startswith('function/'):
            license = re.findall(r"license_code:\s*'([^']+)", videohtml)[0]
            videourl = kvs_decode(videourl, license)
        videourl += '|Referer=' + url
        vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Tags", r'<a href="([^"]+/tags/[^"]+)">([^<]+)<', ''),
        ("Models", r'<a href="([^"]+/models/[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo('', url, 'watchmdh.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('watchmdh.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

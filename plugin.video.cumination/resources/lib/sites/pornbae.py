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
import json
import urllib.parse as urllib_parse
import xbmc
import xbmcgui
import urllib.request
from resources.lib import utils
from resources.lib import jsunpack
from resources.lib.adultsite import AdultSite

# from resources.lib.cfproxy import start_cfproxy
# start_cfproxy()

site = AdultSite('pornobae', '[COLOR hotpink]pornobae[/COLOR]', 'https://pornobae.com/', 'pornobae.png', 'pornobae')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    # site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'actors/page/1/', 'Actors', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/page/1/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1/?filter=latest')


@site.register()
def List(url):
    html = utils._getHtml(url)
    if 'Nothing found' in html:
        utils.notify(url.split('/?s=')[1], 'It looks like nothing was found for this search. Maybe try one of the links below or a new search?')
    
    delimiter = '<article data-video-id='
    re_img = 'data-main-thumb="([^"]+)"'
    re_videopage = 'class="loop-video.+?href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_duration = 'class="duration">.+?</i>([^<]+)<'

    utils.videos_list(site, '{}.Playvid'.format(site.name), html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm='pornobae.Related')

    re_npurl = r'class="pagination".+?(?!.*class="inactive")<a href="([^"]+)">Next<'
    re_npnr  = r'class="pagination".+?(?!.*class="inactive")<a href="[^"]+/(\d+)/'
    re_lpnr  = r'class="pagination".+?(?!.*class="inactive")>Next<.+?<a href="[^"]+/(\d+)/.+>Last'

    utils.next_page(
        site, '{}.List'.format(site.name), html,
        re_npurl, re_npnr, re_lpnr=re_lpnr,
        contextm='{}.GotoPage'.format(site.name)
    )
    utils.eod()

@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornobae.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}/?'.format(np), '/{}/?'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')

@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]{}[CR]".format(utils.i18n('load_vpage')))
    videohtml = utils.getHtml(url, site.url, ignoreCertificateErrors=True)
    match = re.compile(r'IFRAME SRC="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        iframe = match[0]
    else:
        utils.notify(name, utils.i18n('not_found'))
        return
    if vp.resolveurl.HostedMediaFile(iframe):
        try:
            vp.play_from_link_to_resolve(iframe)
            return
        except Exception as e:
            utils.kodilog(f"Resolve failed: {e}")

    try:
        raw = utils._getHtml(iframe)
    except:
        utils.notify('Oh oh', utils.i18n('not_found'))
        vp.progress.close()
        return
    match = re.compile(r'>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(raw)
    if match:
        videourl = jsunpack.unpack(match[0])
        m = re.search(r'file:"(.*?)"', videourl, re.S)
        if m:
            vp.play_from_direct_link(m.group(1))
            return
    match = re.compile(r"olplayer\.src\(\{.+?src: '(.+?)'", re.DOTALL | re.IGNORECASE).findall(raw)
    if match:
        videourl = match[0]
        status = head_request(videourl)

        if isinstance(status, Exception):
            utils.notify("Error:", utils.i18n('not_found'), icon='thumb')
            vp.progress.close()
            return
        vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh oh', utils.i18n('not_found'))
        vp.progress.close()
        return




def head_request(url, timeout=5):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status
    except Exception as e:
        return e


@site.register()
def Actors(url):
    html = utils._getHtml(url)
    match = re.compile(r'<article id="post-.+?href="([^"]+)".+?title="([^"]+)".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for actor_url, name, img in match:
        videourl = "http://127.0.0.1:8789/proxy?url=" + urllib.parse.quote(actor_url)
        site.add_dir(name, videourl, 'List', img)

    # utils.videos_list(site, '{}.List'.format(site.name), html, delimiter, re_videopage, re_name, re_img)

    re_npurl = r'class="pagination".+?(?!.*class="inactive")<a href="([^"]+)">Next<'
    re_npnr  = r'class="pagination".+?(?!.*class="inactive")<a href="[^"]+/(\d+)/'
    re_lpnr  = r'class="pagination".+?(?!.*class="inactive")>Next<.+?<a href="[^"]+/(\d+)/.+>Last'

    utils.next_page(
        site, '{}.List'.format(site.name), html,
        re_npurl, re_npnr, re_lpnr=re_lpnr,
        contextm='{}.GotoPage'.format(site.name)
    )
    utils.eod()


@site.register()
def Categories(url):
    html = utils._getHtml(url)
    match = re.compile(r'<article id="post-.+?href="([^"]+)".+?title="([^"]+)".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for videourl, name, img in match:
        site.add_dir(name, videourl, 'List', img)
    # utils.videos_list(site, '{}.List'.format(url), html, delimiter, re_videopage, re_name, re_img)

    re_npurl = r'class="pagination".+?(?!.*class="current")href="([^"]+)"'
    re_npnr  = r'class="pagination".+?(?!.*class="current")href="[^"]+/(\d+)/'
    re_lpnr  = r'class="pagination".+?(?!.*class="inactive")>(\d+)'

    utils.next_page(
        site, '{}.Categories'.format(site.name), html,
        re_npurl, re_npnr, re_lpnr=re_lpnr,
        contextm='{}.GotoPage'.format(site.name)
    )
    utils.eod()


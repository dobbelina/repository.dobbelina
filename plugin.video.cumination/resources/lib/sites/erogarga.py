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
import json
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.sites.spankbang import Playvid

site = AdultSite('erogarga', '[COLOR hotpink]EroGarga[/COLOR]', 'https://www.erogarga.com/', 'erogarga.png', 'erogarga')
site1 = AdultSite('fulltaboo', '[COLOR hotpink]FullTaboo[/COLOR]', 'https://fulltaboo.tv/', 'fulltaboo.png', 'fulltaboo')
site2 = AdultSite('koreanpm', '[COLOR hotpink]Korean PornMovie[/COLOR]', 'https://koreanpornmovie.com/', 'https://koreanpornmovie.com/wp-content/uploads/2020/05/tt.png', 'koreanpm')


def getBaselink(url):
    if 'erogarga.com' in url:
        siteurl = site.url
    elif 'fulltaboo.tv' in url:
        siteurl = site1.url
    elif 'koreanpornmovie.com' in url:
        siteurl = site2.url
    return siteurl


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    if 'erogarga' in siteurl:
        site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + '?s=', 'Search', site.img_search)
    List(siteurl + '?filter=latest')


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    html = listhtml.split('>SHOULD WATCH<')[0]

    delimiter = 'article data-video-uid'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'data-src="([^"]+)"'
    re_duration = 'fa-clock-o"></i>([^<]+)<'
    re_quality = 'class="hd-video">(HD)<'
    skip = 'type-photos'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=erogarga.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=erogarga.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'erogarga.Play', html, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm, skip=skip)

    re_npurl = 'href="([^"]+)"[^>]*>Next' if '>Next' in html else 'class="current".+?href="([^"]+)"'
    re_npnr = r'/page/(\d+)[^>]*>Next' if '>Next' in html else r'class="current".+?rel="follow">(\d+)<'
    re_lpnr = r'/page/(\d+)[^>]*>Last' if '>Last' in html else r'rel="follow">(\d+)<\D+<\/main>'
    utils.next_page(site, 'erogarga.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='erogarga.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Cat(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
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
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Play(url, name, download=None):
    siteurl = getBaselink(url)

    videohtml = utils.getHtml(url, siteurl)

    if 'koreanporn' in url:
        vp = utils.VideoPlayer(name, download=download)
        match = re.compile(r'<source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
        if match:
            videourl = match[0] + '|Referer={}'.format(siteurl)
            vp.play_from_direct_link(videourl)
        return

    vp = utils.VideoPlayer(name, download=download, regex='"file":"([^"]+)"')
    match = re.compile(r'''<iframe[^>]+src=['"]([^'"]+)['"]''', re.DOTALL | re.IGNORECASE).findall(videohtml)

    playerurl = match[0]
    if 'phixxx.cc/player/play.php?vid=' in playerurl:
        vid = playerurl.split('?vid=')[-1]
        posturl = 'https://phixxx.cc/player/ajax_sources.php'
        formdata = {'vid': vid, 'alternative': 'spankbang', 'ord': '0'}
        data = utils.postHtml(posturl, form_data=formdata)
        data = data.replace(r'\/', '/')
        jsondata = json.loads(data)
        src = jsondata["source"]
        if len(src) > 0:
            videolink = src[0]["file"]
        else:
            formdata = {'vid': vid, 'alternative': 'mp4', 'ord': '0'}
            data = utils.postHtml(posturl, form_data=formdata)
            data = data.replace(r'\/', '/')
            jsondata = json.loads(data)
            videolink = jsondata["source"][0]["file"]
    elif 'pornflip.com' in playerurl:
        playerhtml = utils.getHtml(playerurl, url)
        match = re.compile(r'(data-\S+src\d*)="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(playerhtml)
        src = {m[0]: m[1] for m in match}
        videolink = utils.selector('Select video', src)
        videolink = videolink.replace('&amp;', '&') + '|referer=https://www.pornflip.com/'
    elif 'watcherotic.com' in playerurl:
        embedhtml = utils.getHtml(playerurl, url)
        match = re.compile(r"video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(embedhtml)
        if match:
            videolink = match[0]
            vp.play_from_direct_link(videolink)
    else:
        playerhtml = utils.getHtml(playerurl, url)
        match = re.compile(r'''var hash = '([^']+)'.+?var baseURL = '([^']+)'.+?getPhiPlayer\(hash,'([^']+)',"(\d+)"\);''', re.DOTALL | re.IGNORECASE).findall(playerhtml)
        if match:
            hash, baseurl, alternative, order = match[0]
            formdata = {'vid': hash, 'alternative': alternative, 'ord': order}
            data = utils.postHtml(baseurl + 'ajax_sources.php', form_data=formdata)
            data = data.replace(r'\/', '/')
            jsondata = json.loads(data)
            videolink = jsondata["source"][0]["file"]
            if 'blogger.com' in videolink:
                vp.direct_regex = '"play_url":"([^"]+)"'
                vp.play_from_site_link(videolink, url)
                return
        else:
            itemprop = re.compile('itemprop="contentURL" content="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
            videolink = itemprop[0] if itemprop else playerurl

    if 'spankbang' in videolink:
        videolink = videolink.replace('/embed/', '/video/')
        Playvid(videolink, name, download=download)
    elif vp.resolveurl.HostedMediaFile(videolink).valid_url():
        vp.play_from_link_to_resolve(videolink)
    else:
        vp.play_from_direct_link(videolink)


@site.register()
def Lookupinfo(url):
    siteurl = getBaselink(url)
    lookup_list = [
        ("Tag", r'<a href="{}([^"]+)"\s*?class="label"\s*?title="([^"]+)"'.format(siteurl), ''),
        ("Actor", r'/(actor[^"]+)"\s*?title="([^"]+)"', ''),
    ]

    lookupinfo = utils.LookupInfo(siteurl, url, '{}.List'.format(site.module_name), lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('erogarga.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

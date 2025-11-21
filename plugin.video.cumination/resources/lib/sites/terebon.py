'''
    Cumination
    Copyright (C) 2025 Team Cumination

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
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite('terebon', '[COLOR hotpink]Terebon[/COLOR]', 'https://b.terebon.net/', 'terebon.png', 'terebon')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Sites[/COLOR]', site.url + 'sites/?mode=async&function=get_block&block_id=list_content_sources_sponsors_list&sort_by=title&_=' + str(int(time.time() * 1000)), 'Sites', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?q=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    if 'There is no data in this list' in listhtml:
        utils.notify(msg='No data found')
        return

    delimiter = '<div class="col-lg-4'
    re_videopage = 'href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = 'src="([^"]+)"'
    re_duration = 'class="video-preview__duration">([^<]+)<'
    re_quality = 'class="video-preview__quality">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=terebon.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=terebon.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    skip = 'Captcha'
    utils.videos_list(site, 'terebon.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm, skip=skip)

    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        ts = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, ts)
        lpnr, lastp = 0, ''
        match = re.search(r':(\d+)">Last', listhtml, re.DOTALL | re.IGNORECASE)
        if match:
            lpnr = match.group(1)
            lastp = '/{}'.format(lpnr)
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=terebon.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&lp=" + str(lpnr))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "terebon.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('terebon.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    # match = re.compile(r'<iframe[^>]+src="([^"]+)"', re.DOTALL | re.IGNORECASE).search(videopage)
    # if match:
    #     vp.progress.update(50, "[CR]Loading video[CR]")
    #     iframehtml = utils.getHtml(match.group(1), url, ignoreCertificateErrors=True)

    iframehtml = videopage

    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(iframehtml)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(iframehtml)
        for surl, qual in items:
            qual = '00' if qual == 'preview' else qual
            surl = kvs_decode(surl, license)
            sources.update({qual: surl})
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
    if videourl:
        vp.progress.update(75, "[CR]Video found[CR]")
        vp.play_from_direct_link(videourl)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url)
    cats = re.compile(r'<div class="col-xxl-2.+?href="([^"]+)"\s*title="([^"]+)".+?data-original="([^"]+)">', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for page, name, img in cats:
        name = utils.cleantext(name)
        site.add_dir(name, page, 'List', img)
    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    tags = re.compile('<a class="video-specs__tag" href="([^"]+)">([^<]+)</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for page, tag in tags:
        tag = utils.cleantext(tag.strip())
        site.add_dir(tag, page, 'List', '')
    utils.eod()


@site.register()
def Sites(url):
    listhtml = utils.getHtml(url)
    tags = re.compile(r'<a class="item" href="([^"]+)"\s*title="([^"]+)">.+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for page, name, videos in tags:
        name = utils.cleantext(name.strip()) + ' (' + videos.strip() + ')'
        site.add_dir(name, page, 'List', '')
    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        ts = int(time.time() * 1000)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, ts)
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'Sites', site.img_next)
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Category", '/(categories/[^"]+)">([^<]+)<', ''),
        ("Tags", '/(tags/[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'terebon.List', lookup_list)
    lookupinfo.getinfo()

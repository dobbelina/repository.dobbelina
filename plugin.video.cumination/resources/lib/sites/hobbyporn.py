"""
    Cumination
    Copyright (C) 2022 Team Cumination

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
"""

import re
import xbmcplugin
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import urllib.request
import ssl

site = AdultSite('hobbyporn', '[COLOR hotpink]Hobby Porn[/COLOR]', 'https://hobby.porn/', 'https://hobby.porn/static/images/logo.png', 'hobbyporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="item item-video item-lozad.+?href="([^"]+).+?title="([^"]+)".+?src="([^"]+).+?duration">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    thumbnails = utils.Thumbnails(site.name)
    for videourl, name, img, duration in match:
        img = thumbnails.fix_img(img)
        name = utils.cleantext(name)
        site.add_download_link(name, videourl, 'Playvid', img, name, duration=duration)

    nextp = re.compile(r'class="pagination".+?class="active">\s*\d+\s*</span>\s*</li>\s*<li>\s*<a\s*href="/([^"]+)').search(listhtml)
    if nextp:
        nextp = site.url + nextp.group(1)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(nextp.split('/')[-2]), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    source = re.compile(r'<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    if source:
        videopage = get_html(
            source[0],
            referer=site.url,
            cookies="accessAgeDisclaimerPH=1; accessAgeDisclaimerUK=1"
        )

        match = re.compile(r',"videoUrl":"([^"]+)","quality":"([^"]+)"', re.DOTALL).findall(videopage)
        if match:
            src = {x[1]: x[0] for x in match}
            videolink  = utils.prefquality(src, sort_by =lambda x: int(x), reverse=True)
            if videolink:
                videolink = videolink.replace('\\/', '/') + '|Referer=https://www.pornhub.com/&Cookie=accessAgeDisclaimerPH=1;accessAgeDisclaimerUK=1&Origin=https://www.pornhub.com'
                vp.play_from_direct_link(videolink)
                return

    sources = re.compile(r"video(?:_alt)?_url:\s*'([^']+).+?video(?:_alt)?_url_text:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)
    if sources:
        sources = {qual: surl for surl, qual in sources}
        source = utils.prefquality(sources, sort_by=lambda x: int(x[:-1]), reverse=True)
        if source:
            source = utils.getVideoLink(source)
            vp.play_from_direct_link(source)
        else:
            vp.progress.close()
            return
    else:
        source = re.compile(r'<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
        if source:
            if vp.resolveurl.HostedMediaFile(source[0]):
                vp.play_from_link_to_resolve(source[0])
            else:
                vp.progress.close()
                utils.notify('Oh Oh', 'No playable Videos found')
                return
        else:
            vp.progress.close()
            utils.notify('Oh Oh', 'No Videos found')
            return


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="item.+?href="([^"]+).+?(?:pan|title")>([^<]+)<.+?<span>([^<]+)').findall(cathtml)
    for caturl, name, items in match:
        name += " [COLOR deeppink]" + items + " videos[/COLOR]"
        site.add_dir(name, caturl, 'List', '', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="item\s*item-model.+?href="([^"]+).+?src="([^"]+).+?title">([^<]+).+?span>([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]({0} videos)[/COLOR]'.format(count)
        site.add_dir(name, caturl, 'List', img)

    nextp = re.compile(r'class="pagination".+?class="active">\s*\d+\s*</span>\s*</li>\s*<li>\s*<a\s*href="/([^"]+)').search(cathtml)
    if nextp:
        nextp = site.url + nextp.group(1)
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(nextp.split('/')[-2]), nextp, 'Models', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title + '/'
        List(searchUrl)


def get_html(url, referer=None, cookies=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    if referer:
        headers["Referer"] = referer

    if cookies:
        headers["Cookie"] = cookies

    req = urllib.request.Request(url, headers=headers)

    ctx = ssl.create_default_context()
    ctx.set_ciphers('DEFAULT@SECLEVEL=1')

    with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
        return response.read().decode('utf-8', errors='ignore')

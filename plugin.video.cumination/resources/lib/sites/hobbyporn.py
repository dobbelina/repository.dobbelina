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
    if 'list_models_most_recent_models_list' in listhtml:
        listhtml = listhtml.split('list_models_most_recent_models_list')[0]
    match = re.compile(r'class="item\s*item-video.+?href="([^"]+).+?src="([^"]+).+?duration">([^<]+).+?title">(?:\s*<span.+?</span>)?([^<]+)',
                       re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videourl, img, duration, name in match:
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

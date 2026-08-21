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
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('pornyteen', '[COLOR hotpink]Pornyteen[/COLOR]', 'https://pornyteen.com/', 'pornyteen.png', 'pornyteen')

addon = utils.addon


# @site.register(default_mode=True)
# def Main():
#     site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
#     List(site.url + 'videos/page1.html')
url = site.url + 'videos/' 

@site.register(default_mode=True)
def List(url=None):
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    sort_setting = utils.addon.getSetting('pornyteen_sort')
    if not sort_setting:
        sort_setting = 'Most Recent|https://pornyteen.com/videos/'
        utils.addon.setSetting('pornyteen_sort', sort_setting)
    if '/page' not in url:
        url = sort_setting.split('|')[1]
        tag = sort_setting.split('|')[0]

        site.add_dir(
            f'[COLOR hotpink]Filters[/COLOR] Sort/Tag: [COLOR yellow][{tag}][/COLOR]',
            url,
            'filters',
            site.img_filters,
            Folder=False
        )

    html = utils.getHtml(url)
    if 'Sorry, no results were found.' in html:
        utils.notify(tag, 'Nothing found.')
        utils.addon.setSetting('pornyteen_sort', 'Most Recent|https://pornyteen.com/videos/')
        return
    delimiter = 'class="item__inner"'
    re_videopage = 'href="([^"]+)"'
    re_name = 'title="([^"]+)"'
    re_img = 'src="([^"]+)"'
    re_duration = r'class="item__stat -duration.*?label[^>]*>([^<]+)<'
    re_quality = r'">(HD)</span>'


    utils.videos_list(
        site, 'pornyteen.Playvid', html, delimiter,
        re_videopage, re_name, re_img,
        re_duration=re_duration, re_quality=re_quality,
        contextm='pornyteen.Related'
    )

    re_npurl = r"<a rel='next'.+?href='([^']+)'"
    re_npnr  = r"<a rel='next'.+?href='page(\d+)\.html'"
    # re_lpnr  = r"<a class='page-numbers' href='[^']*/(\d+)[^']*'>\s*[\d,]+\s*</a>(?!.*<a class='page-numbers')"

    utils.next_page(
        site, 'pornyteen.List', html,
        re_npurl, re_npnr,
        contextm='pornyteen.GotoPage',
        # baseurl=site.url + 'videos/'
        baseurl= re.sub(r"/[^/]+$", "/", url)
    )
    utils.eod()

@site.register()
def filters(url):
    html = utils.getHtml(site.url)
    list = ("Sort", "Tag")
    selection = xbmcgui.Dialog().select('Select order', list)
    if selection == -1:
        return
    elif selection == 0:        # Sort by
        container = re.compile(
            r'<ul class="dropdown-list g--dropdown">(.+?)</ul>'
            , re.DOTALL | re.IGNORECASE
        ).findall(html)

        container = re.compile(
            r'class="dropdown-list__link"\shref="([^"]+)"\stitle="([^"]+)"'
            , re.DOTALL | re.IGNORECASE
        ).findall(container[0])
        if not container:
            return
        labels = [label for url, label in container]
        urls   = [url   for url, label in container]
        selection = xbmcgui.Dialog().select('Select order', labels)
        if selection != -1:
            utils.addon.setSetting('pornyteen_sort', labels[selection] + '|' + urls[selection])
            utils.refresh()
    elif selection == 1:        # Tags
        container = re.compile(
            r'<ul class="counter-list"(.+?)</ul>'
            , re.DOTALL | re.IGNORECASE
        ).findall(html)

        container = re.compile(
            r'''class="counter-list__li".+?title='([^']+)'\shref='([^']+).+?counter">([^>]+)<'''
            , re.DOTALL | re.IGNORECASE
        ).findall(container[0])
        if not container:
            return
        labels = [label + ' [' + counter + ']' for label, url, counter in container]
        urls   = [url   for label, url, counter in container]
        selection = xbmcgui.Dialog().select('Select order', labels)
        if selection != -1:
            utils.addon.setSetting('pornyteen_sort', labels[selection] + '|' + urls[selection])
            utils.refresh()

@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '-') + '/'
        utils.addon.setSetting('pornyteen_sort', keyword + '|' + url)
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    # vp.play_from_link_to_resolve(url)

    vp.play_from_site_link(url, url)

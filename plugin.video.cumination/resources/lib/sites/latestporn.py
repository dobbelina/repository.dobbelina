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
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('latestporn', '[COLOR hotpink]LatestPorn[/COLOR]', 'https://latestporn.co/', 'https://latestporn.co/wp-content/uploads/2020/02/cropped-LogoMakr_9cCXno.png', 'latestporn')


@site.register(default_mode=True)
def Main():
    #site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Movies[/COLOR]', site.url + 'category/movies/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url, 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'id="post-\d*".*?href="([^"]+)".*?data-src="([^"]+)".*?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, img, name in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('latestporn.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    np = re.compile(r'rel="next"\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    links = {}
    phtml = utils.getHtml(url, site.url)
    direct = re.compile("video=([^&]+)&", re.DOTALL | re.IGNORECASE).findall(phtml)
    if direct:
        links['Direct'] = direct[0]
    sources = re.compile(r'href="([^"]+)"\s*rel="noopener"', re.DOTALL | re.IGNORECASE).findall(phtml)
    for link in sources:
        if '.rar' in link:
            continue
        if vp.resolveurl.HostedMediaFile(link).valid_url():
            links[link.split('/')[2]] = link
    videourl = utils.selector('Select link', links)
    if not videourl:
        vp.progress.close()
        return
    if 'Direct' in links:
        if links['Direct'] == videourl:
            vp.play_from_direct_link(videourl)
        else:
            vp.play_from_link_to_resolve(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'/(tag/[^"]+)"\s*class="tag-cloud-link.*?aria-label="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name.strip())
        site.add_dir(name, site.url + tagpage, 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Tag", r'/(tag/[^"]+)"\s*rel="tag">([^<]+)', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'latestporn.List', lookup_list)
    lookupinfo.getinfo()
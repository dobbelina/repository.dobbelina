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

site = AdultSite('naughtyblog', '[COLOR hotpink]NaughtyBlog[/COLOR]  [COLOR red][Debrid only][/COLOR]', 'https://www.naughtyblog.org/', 'https://www.naughtyblog.org/wp-content/images/logo/main_logo.png', 'naughtyblog')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Movies[/COLOR]', site.url + 'category/movies/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'category/clips/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('class="post-author">(.*?)post-content.*?<a href="([^"]+)"><img.*?src="([^"]+)".*?title="([^"]+)".*?<strong>([^<]+)<.*?<em>([^<]+)<.*?<p>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for tags, videopage, img, name, title, release, plot in match:
        name = utils.cleantext(name)
        plot = "{}\n{}\n{}".format(utils.cleantext(title), utils.cleantext(release), utils.cleantext(plot))
        if any(tag in tags for tag in ['siterip', 'onlyfans-leak']):
            continue

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('naughtyblog.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, plot, contextm=contextmenu)

    np = re.compile(r'aria-label="Next Page"\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    sitehtml = utils.getHtml(url, site.url)
    downloads = re.compile('id="download">(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(sitehtml)[0]
    sources = re.compile(r'href="([^"]+)"\s+?title="([^\s]+)\s', re.DOTALL | re.IGNORECASE).findall(downloads)
    links = {}
    for link, hoster in sources:
        if vp.resolveurl.HostedMediaFile(link).valid_url():
            linkparts = link.split('.')
            quality = linkparts[-3] if link.endswith('.html') else linkparts[-2]
            hoster = "{0} {1}".format(hoster, quality)
            links[hoster] = link
    videourl = utils.selector('Select link', links)
    if not videourl:
        vp.progress.close()
        return
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
def Categories(url):
    listhtml = utils.getHtml(url)
    match = re.compile('href="([^"]+)"[^>]+>([^<]+)<span class="pocetvideicat">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name.strip())
        name = "{0} - {1} videos".format(name, videos.strip())
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'/((?:category|tag)/[^"]+)"\s*?rel="(?:category )*?tag">([^<]+)<', ''),
        ("Site", r'(site/[^"]+)"\s*?rel="tag">([^<]+)', ''),
        ("Model", r'/(pornstar/[^"]+)"\s*?rel="tag">([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'naughtyblog.List', lookup_list)
    lookupinfo.getinfo()
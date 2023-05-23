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

site = AdultSite('seaporn', '[COLOR hotpink]SeaPorn[/COLOR] [COLOR red][Debrid only][/COLOR]', 'https://www.seaporn.org/', '', 'seaporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('entry-title"><a href="([^"]+)"[^>]+>([^<]+).*?<time[^>]+>([^<]+)<.*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, posted, img in match:
        name = utils.cleantext(name)
        plot = "{}\n{}".format(utils.cleantext(name), utils.cleantext(posted))

        if 'static.keep2share' in img:
            continue

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('seaporn.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, plot, contextm=contextmenu)

    np = re.compile('page-numbers" href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page (' + page_number + ')', np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    sitehtml = utils.getHtml(url, site.url)
    sources = re.compile('<a href="([^"]+)" class="autohyperlink">https*://([^/]+)', re.DOTALL | re.IGNORECASE).findall(sitehtml)
    links = {}
    for link, hoster in sources:
        if vp.resolveurl.HostedMediaFile(link).valid_url():
            filename = link.split('/')[-1]
            hoster = "{0} {1}".format(hoster, filename)
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
    match = re.compile(r'cat-item-\d+"><a\s+?href="([^"]+)">([^<]+)</a>\s+?\(([^\)]+)\)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, videos in match:
        name = utils.cleantext(name.strip())
        if any(cat in name for cat in ['Galleries', 'Magazines', 'Pictures', 'Siterips', 'Mobile']):
            continue
        
        name = "{0} - {1} videos".format(name, videos.strip())
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None

    infodict = {}

    categories = re.compile(r'/(category/[^"]+)"\s*?rel="category tag">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if categories:
        for url, cat in categories:
            cat = "Cat - " + cat.strip()
            infodict[cat] = site.url + url

    tags = re.compile(r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if tags:
        for url, tag in tags:
            tag = "Tag - " + tag.strip()
            infodict[tag] = site.url + url

    if infodict:
        selected_item = utils.selector('Choose item', infodict, show_on_one=True)
        if not selected_item:
            return
        contexturl = (utils.addon_sys
                      + "?mode=" + str('seaporn.List')
                      + "&url=" + urllib_parse.quote_plus(selected_item))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    else:
        utils.notify('Notify', 'No tags or categories found for this video')
    return

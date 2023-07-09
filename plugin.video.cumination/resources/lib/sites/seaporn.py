# -*- coding: utf-8 -*-
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
def List(url, page=1):
    videodict = {}

    progress = utils.progress
    progress.create('SeaPorn', 'Loading videos..')

    while len(videodict) < 40:
        listhtml = utils.getHtml(url, '')
        match = re.compile('entry-title"><a href="([^"]+)"[^>]+>([^<]+).*?<time[^>]+>([^<]+)<.*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        if not match:
            break
        for videopage, rlsname, posted, img in match:
            rlsname = utils.cleantext(rlsname)
            name = rlsname.split('– ')[:-1][0] if '– ' in rlsname else rlsname
            plot = "{}\n{}".format(utils.cleantext(name), utils.cleantext(posted))

            if 'static.keep2share' in img:
                continue

            img = img + '|verifypeer=false'
            videodict.setdefault(name, []).append((rlsname, videopage, img, plot))
            progress.update(int(len(videodict.keys()) * 100 / 40), 'Loading video {}'.format(len(videodict.keys()) + 1))
        if progress.iscanceled():
            break

        np = re.compile('page-numbers" href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).search(listhtml)
        if not np:
            break

        url = np.group(1)
        page += 1

    progress.close()

    for name, videos in videodict.items():
        if (len(videos) == 1):
            rlsname, videopage, img, plot = videos[0]
            contexturl = (utils.addon_sys
                          + "?mode=seaporn.Lookupinfo"
                          + "&url=" + urllib_parse.quote_plus(videopage))
            contextmenu = [('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')]
            site.add_download_link(rlsname, videopage, 'Playvid', img, plot, contextm=contextmenu)
        else:
            name = '{} [{}]'.format(name, len(videos))
            site.add_dir(name, json.dumps(videos), 'Rlslist', videos[0][2], videos[0][3])

    if np:
        site.add_dir('Next Page (' + str(page) + ')', np.group(1), 'List', site.img_next, page=page)
    utils.eod()


@site.register()
def Rlslist(url):
    videos = json.loads(url)
    for rlsname, videopage, img, plot in videos:
        contexturl = (utils.addon_sys
                      + "?mode=seaporn.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu = [('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')')]
        site.add_download_link(rlsname, videopage, 'Playvid', img, plot, contextm=contextmenu)
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
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        url = url + title
        List(url)


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
    lookup_list = [
        ("Cat", r'/(category/[^"]+)"\s*?rel="category tag">([^<]+)<', ''),
        ("Tag", r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'seaporn.List', lookup_list)
    lookupinfo.getinfo()

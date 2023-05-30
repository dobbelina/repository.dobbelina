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

site = AdultSite('javgg', '[COLOR hotpink]JavGG[/COLOR]', 'https://javgg.net/', 'https://javgg.net/javgg.png', 'javgg')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'tags', 'Cats', site.img_cat)
    site.add_dir('[COLOR hotpink]Trending[/COLOR]', site.url + 'trending/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Featured[/COLOR]', site.url + 'featured/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'genre-list/', 'Tags', site.img_cat)
    List(site.url + 'new-post/page/1/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('alt="([^"]+)" data-src="([^"]+)"[^>]+>(.*?)<a href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for name, img, genre, videopage in match:
        name = utils.cleantext(name)

        if genre:
            match = re.search(">([^<]+)<", genre, re.IGNORECASE | re.DOTALL)
            if match:
                name = "{0} - {1}".format(name, match.group(1))

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('javgg.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    np = re.compile("""arrow_pag' href="([^"]+)">""", re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        page_number = np.group(1).split('/')[-2]
        site.add_dir('Next Page...  (Page {0})'.format(page_number), np.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex='"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    sources = []
    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r"data-post='([^']+)'\s+?data-nume='([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)
    for videoid, vidcount in match:
        ajaxurl = 'https://javgg.net/wp-json/dooplayer/v2/{0}/movie/{1}'.format(videoid, vidcount)
        ajaxhtml = utils.getHtml(ajaxurl, url)
        ajaxjson = json.loads(ajaxhtml)
        sources.append('"{0}"'.format(ajaxjson['embed_url']))
    vp.progress.update(50, "[CR]Loading video page[CR]")
    vp.play_from_html(', '.join(sources))


@site.register()
def Cats(url):
    match = [
        ('Random', 'random/'),
        ('HD Uncensored', 'tag/hd-uncensored/'),
        ('Uncensored Leak', 'tag/uncensored-leak/'),
        ('Decensored', 'tag/decensored/'),
        ('Censored', 'tag/censored/'),
        ('Chinese Subtitle', 'tag/chinese-subtitle/'),
        ('English Subtitle', 'tag/english-subtitle/'),
    ]

    for name, catpage in match:
        site.add_dir(name, site.url + catpage, 'List', '')

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile('/(genre/[^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, site.url + tagpage, 'List', '')
    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Genres", r'/(genre/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Maker", r'/(maker/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Label", r'/(label/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Director", r'/(director/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Cast", r'/(star/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'javgg.List', lookup_list)
    lookupinfo.getinfo()

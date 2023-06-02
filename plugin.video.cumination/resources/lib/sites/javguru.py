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
import base64
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('javguru', '[COLOR hotpink]Jav Guru[/COLOR]', 'https://jav.guru/', 'https://cdn.javsts.com/wp-content/uploads/2018/12/logofinal6.png', 'javguru')

enames = {'STREAM DD': 'DoodStream',
          'STREAM FE': 'FEmbed',
          'STREAM SB': 'StreamsB',
          'STREAM ST': 'StreamTape',
          'STREAM VO': 'Voe'}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'wp-json/wp/v2/categories/', 'Catjson', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'jav-tags-list/', 'Toplist', site.img_cat)
    site.add_dir('[COLOR hotpink]Series[/COLOR]', site.url + 'jav-series/', 'Toplist', site.img_cat)
    site.add_dir('[COLOR hotpink]Actress[/COLOR]', site.url + 'jav-actress-list/', 'Actress', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'jav-studio-list/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', site.url + 'category/jav-uncensored/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''class="inside-article".+?href='([^']+)'><img src='([^']+)'.+?<a title="([^"]+)"''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('javguru.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(video))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, video, 'Play', img, name, contextm=contextmenu)

    match = re.compile(r'''class='current'.+?href="([^"]+)">(\d+)<''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        npage, np = match[0]
        lp = re.compile(r''' href="[^"]+page/(\d+)/[^"]*">Last''', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}{1})'.format(np, lp), npage, 'List', site.img_next)
    utils.eod()


@site.register()
def Catjson(url):
    listjson = utils.getHtml(url)
    jdata = json.loads(listjson)
    for cat in jdata:
        name = '{0} ({1})'.format(cat["name"], cat["count"])
        site.add_dir(name, cat["link"], 'List', '')
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    patterns = [r'class="cat-item.+?href="([^"]+)">([^<]+)</a>\s*\((\d+)\)',
                r'href="([^"]+)"\s+?rel="tag">([^<]+)<span>\s*\((\d+)\)']
    for pattern in patterns:
        match = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(cathtml)
        for caturl, name, count in match:
            name = '{0} ({1})'.format(utils.cleantext(name), count)
            site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Toplist(url):
    site.add_dir('[COLOR hotpink]Full list, by number of videos[/COLOR]', url, 'Cat', site.img_cat)
    cathtml = utils.getHtml(url)
    match = re.compile(r'<a href="([^"]+)">\s+?<div[^<]+<img src="([^"]+)".*?tagname">([^<]+)<[^>]+>[^>]+>([^<]+).*?</i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for caturl, img, name, plot, count in match:
        name = '{0} ({1})'.format(utils.cleantext(name), count)
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Actress(url):
    actresshtml = utils.getHtml(url)
    match = re.compile(r'/(actress/[^"]+)".*?src="([^"]+)"\s+?alt="([^"]+)".*?</i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(actresshtml)
    for actressurl, img, name, videos in match:
        name = '{0} ({1})'.format(utils.cleantext(name), videos.strip())
        site.add_dir(name, site.url + actressurl, 'List', img)
    match = re.compile(r'current".+?href="([^"]+)">(\d+)<', re.DOTALL | re.IGNORECASE).findall(actresshtml)
    if match:
        npage, np = match[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np), npage, 'Actress', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    sources = []
    videohtml = utils.getHtml(url)
    match = re.compile('iframe_url":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)
    if match:
        for i, stream in enumerate(match):
            link = base64.b64decode(stream).decode('utf-8')

            vp.progress.update(25, "[CR]Loading streaming link {0} page[CR]".format(i + 1))
            streamhtml = utils.getHtml(link, url, error='raise')
            match = re.compile(r'''var OLID = '([^']+)'.+?src="([^']+)''', re.DOTALL | re.IGNORECASE).findall(streamhtml)
            if match:
                (olid, vurl) = match[0]
                olid = olid[::-1]
            else:
                continue
            src = vurl + olid
            src = utils.getVideoLink(src, link)
            sources.append('"{}"'.format(src))
    match = re.compile(r"window\.open\('([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)
    if match:
        for dllink in match:
            vp.progress.update(60, "[CR]Loading download link page[CR]")
            dllink = utils.getHtml(dllink)
            match = re.compile('URL=([^"]+)"', re.DOTALL | re.IGNORECASE).findall(dllink)
            if match:
                sources.append('"{}"'.format(match[0]))
    if sources:
        vp.progress.update(75, "[CR]Loading video page[CR]")
        utils.kodilog(sources)
        vp.play_from_html(', '.join(sources))
    else:
        return


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'/(category/[^"]+)"\s*?rel="category tag">([^<]+)<', ''),
        ("Tags", r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)</a', ''),
        ("Studio", r'/(maker/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Label", r'/(studio/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Series", r'/(series/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Actor", r'/(actor/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
        ("Actress", r'/(actress/[^"]+)"\s*?rel="tag">([^<]+)<', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'javguru.List', lookup_list)
    lookupinfo.getinfo()

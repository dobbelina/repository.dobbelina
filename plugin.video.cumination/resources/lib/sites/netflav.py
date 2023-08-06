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

import json
import re

import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('netflav', '[COLOR hotpink]Netflav[/COLOR]', 'https://netflav.com/', 'https://netflav.com/static/assets/logo.svg', 'netflav')


def make_netflav_headers():
    netflav_headers = utils.base_hdrs
    netflav_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    netflav_headers['Accept-Encoding'] = 'gzip, deflate, br'
    netflav_headers['Cookie'] = 'i18next=en'
    return netflav_headers


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Censored[/COLOR]', site.url + 'censored?page=1', 'List', site.img_cat, section='censored')
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', site.url + 'uncensored?page=1', 'List', site.img_cat, section='uncensored')
    site.add_dir('[COLOR hotpink]Chinese Sub[/COLOR]', site.url + 'chinese-sub?page=1', 'List', site.img_cat, section='chinese-sub')
    site.add_dir('[COLOR hotpink]Genres[/COLOR]', site.url + 'genre', 'Genres', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'api98/video/advanceSearchVideo?type=title&page=1&keyword=', 'Search', site.img_search, section='search')
    List(site.url + 'all?page=1', 'all')
    utils.eod()


@site.register()
def List(url, section='all'):
    try:
        listhtml = utils.getHtml(url, headers=make_netflav_headers())
    except Exception:
        return None
    if section == 'search':
        jdata = json.loads(listhtml).get("result")
    else:
        jdata = re.compile('<script id="__NEXT_DATA__" type="application/json">([^<]+)</script', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        jdata = json.loads(jdata).get("props").get("initialState").get(section)
    page = jdata.get("page")
    pages = jdata.get("pages")
    videos = jdata.get("docs")
    for video in videos:
        name = video["title_en"] if utils.PY3 else video["title_en"].encode('utf-8')
        name = utils.cleantext(name)
        img = video.get("preview", "")
        date_added = video.get("sourceDate", "").split('T')[0]
        if not date_added:
            date_added = video.get("createdAt", "").split('T')[0]
        plot = "{0}\n{1}".format(name, date_added)
        videopage = '{0}video?id={1}'.format(site.url, video.get("videoId"))

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=netflav.Lookupinfo"
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, plot, contextm=contextmenu)
    if page < pages:
        if 'page=' in url:
            npurl = url.replace('page={}'.format(page), 'page={}'.format(page + 1))
        else:
            npurl = url
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}/{1})'.format(page + 1, pages), npurl, 'List', site.img_next, section=section)
    utils.eod()


@site.register()
def Genres(url):
    try:
        genrehtml = utils.getHtml(url, headers=make_netflav_headers())
    except Exception:
        return None
    sections = re.compile('container_header_title_large"[^>]+>([^<]+)<(.*?)<iframe', re.DOTALL | re.IGNORECASE).findall(genrehtml)
    for header, genres in sections:
        header = utils.cleantext(header)
        genresmatch = re.compile(r'/(all\?genre[^"]+)"><div>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(genres)
        for genreurl, genre in sorted(genresmatch, key=lambda x: x[1]):
            name = '{0} - {1}'.format(header, utils.cleantext(genre))
            genreurl = site.url + genreurl + '&page=1'
            site.add_dir(name, genreurl, 'List', '', page=1, section='all')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url, section='search')


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    html = utils.getHtml(url, site.url)
    jdata = re.compile('<script id="__NEXT_DATA__" type="application/json">([^<]+)</script', re.DOTALL | re.IGNORECASE).findall(html)[0]
    jdata = json.loads(jdata).get("props").get("initialState").get("video").get("data")
    links = {}

    if jdata.get("isMissav"):
        links['MISSAV'] = 'https://missav.com/en/{}'.format(jdata.get("code"))

    for link in jdata.get("srcs"):
        if vp.bypass_hosters_single(link):
            continue
        if vp.resolveurl.HostedMediaFile(link).valid_url():
            links[link] = link

    videourl = utils.selector('Select link', links)
    if not videourl:
        vp.progress.close()
        return

    if 'missav.com' in videourl:
        contexturl = (utils.addon_sys
                      + "?mode=missav.Playvid"
                      + "&name=name"
                      + "&url=" + urllib_parse.quote_plus(videourl))
        xbmc.executebuiltin('RunPlugin(' + contexturl + ')')
        return
    vp.play_from_link_to_resolve(videourl)


@site.register()
def Lookupinfo(url):
    class NetflavLookup(utils.LookupInfo):
        def url_constructor(self, url):
            return site.url + url + '&page=1'

    lookup_list = [
        ("Genre", r'/(all\?genre[^"]+)"><u>([^<]+)<', ''),
        ("Actress", r'/(all\?actress[^"]+)"><u>([^<]+)<', ''),
    ]

    lookupinfo = NetflavLookup(site.url, url, 'netflav.List', lookup_list)
    lookupinfo.getinfo(headers=make_netflav_headers())

"""
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
"""

import re
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hqporner', '[COLOR hotpink]HQPorner[/COLOR]', 'https://hqporner.com', 'hqporner.png', 'hqporner')


@site.register(default_mode=True)
def HQMAIN():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + '/porn-categories.php', 'HQCAT', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + '/porn-studios.php', 'HQCAT', '', '')
    site.add_dir('[COLOR hotpink]Girls[/COLOR]', site.url + '/porn-actress.php', 'HQCAT', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '/?q=', 'HQSEARCH', site.img_search)
    HQLIST(site.url + '/hdporn/1')
    utils.eod()


@site.register()
def HQLIST(url):
    try:
        link = utils.getHtml(url, '')
    except:
        return None
    match = re.compile(r'<a\s*href="([^"]+)"\s*class="image\s*featured\s*non.+?src="([^"]+)"\s*alt="([^"]+).+?data">(\d[^<]+)', re.DOTALL | re.IGNORECASE).findall(link)
    for url, img, name, duration in match:
        name = utils.cleantext(name).title()
        videourl = urllib_parse.quote(site.url + url, safe=':/')
        if img.startswith('//'):
            img = 'https:' + img

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('hqporner.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videourl))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videourl, 'HQPLAY', img, name, duration=duration, contextm=contextmenu)
    try:
        nextp = re.compile('<a href="([^"]+)"[^>]+>Next', re.DOTALL | re.IGNORECASE).findall(link)
        nextp = "https://www.hqporner.com" + nextp[0]
        site.add_dir('Next Page', nextp, 'HQLIST', site.img_next)
    except:
        pass
    utils.eod()


@site.register()
def HQCAT(url):
    link = utils.getHtml(url, '')
    tags = re.compile(r'<a\s*href="([^"]+)"[^<]+<img\s*src="([^"]+)"\s*alt="([^"]+)', re.DOTALL | re.IGNORECASE).findall(link)
    tags = sorted(tags, key=lambda x: x[2])
    for caturl, img, catname in tags:
        caturl = site.url + caturl
        if img.startswith('//'):
            img = 'https:' + img
        site.add_dir(catname.title(), caturl, 'HQLIST', img)
    utils.eod()


@site.register()
def HQSEARCH(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'HQSEARCH')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        HQLIST(searchUrl)


@site.register()
def HQPLAY(url, name, download=None):
    videopage = utils.getHtml(url, url)
    iframeurl = re.compile(r"nativeplayer\.php\?i=([^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    if iframeurl.startswith('//'):
        iframeurl = 'https:' + iframeurl
    if 'bemywife' in iframeurl:
        videourl = getBMW(iframeurl)
    elif 'mydaddy' in iframeurl:
        videourl = getBMW(iframeurl)
    elif '5.79' in iframeurl:
        videourl = getIP(iframeurl)
    elif 'flyflv' in iframeurl:
        videourl = getFly(iframeurl)
    elif 'hqwo' in iframeurl:
        videourl = getHQWO(iframeurl)
    else:
        utils.notify('Oh oh', 'Couldn\'t find a supported videohost')
        return
    utils.playvid(videourl, name, download)


def getBMW(url):
    videopage = utils.getHtml(url, '')
    videos = re.compile(r'source\s*src=\\"([^\\]+).+?\\"([^\\\s]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    if not videos:
        videos = re.compile(r'file:\s*"([^"]+mp4)",\s*label:\s*"\d+', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videos:
        videos = {label: url for url, label in videos}
        videourl = utils.prefquality(videos, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl.startswith('//'):
            videourl = 'https:' + videourl
        return videourl


def getIP(url):
    videopage = utils.getHtml(url, '')
    videos = re.compile(r'file":\s*"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    videourl = videos[-1]
    if videourl.startswith('//'):
        videourl = 'https:' + videourl
    return videourl


def getFly(url):
    videopage = utils.getHtml(url, '')
    videos = re.compile(r'''source\s*src=['"]([^'"]+).+?label=['"]([^'"]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videos:
        videos = {label: url for url, label in videos}
        videourl = utils.prefquality(videos, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl.startswith('//'):
            videourl = 'https:' + videourl
        return videourl


def getHQWO(url):
    epage = utils.getHtml(url, '')
    eurl = re.compile(r'''<script[^\n]+src='([^']+)''', re.DOTALL | re.IGNORECASE).findall(epage)[0]
    videopage = utils.getHtml(eurl, 'https://hqwo.cc/')
    videos = re.compile(r'''file":\s*"([^"]+).+?label":\s*"([^"]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videos:
        videos = {label: url for url, label in videos}
        videourl = utils.prefquality(videos, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl.startswith('//'):
            videourl = 'https:' + videourl
        return videourl


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actor", 'href="(/actress/[^"]+)"[^>]+>([^<]+)<', ''),
        ("Tag", 'href="(/category/[^"]+)"[^>]+>([^<]+)<', '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'hqporner.HQLIST', lookup_list)
    lookupinfo.getinfo()
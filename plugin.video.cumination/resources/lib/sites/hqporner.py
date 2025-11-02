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
from six.moves import urllib_parse, urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('hqporner', '[COLOR hotpink]HQPorner[/COLOR]', 'https://hqporner.com', 'hqporner.png', 'hqporner')


@site.register(default_mode=True)
def HQMAIN():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + '/categories', 'HQCAT', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + '/studios', 'HQCAT', '', '')
    site.add_dir('[COLOR hotpink]Girls[/COLOR]', site.url + '/girls', 'HQCAT', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '/?q=', 'HQSEARCH', site.img_search)
    HQLIST(site.url + '/hdporn/1')
    utils.eod()


@site.register()
def HQLIST(url):
    try:
        link = utils.getHtml(url, '')
    except:
        return None
    soup = utils.parse_html(link)
    cards = soup.select('section.box.feature')
    for card in cards:
        anchor = card.select_one('a.image.featured[href]')
        if not anchor:
            continue
        videopage = utils.safe_get_attr(anchor, 'href')
        if not videopage:
            continue
        videourl = site.url + videopage.lstrip('/')

        img_tag = anchor.select_one('img')
        img = utils.safe_get_attr(img_tag, 'src')
        if img and img.startswith('//'):
            img = 'https:' + img

        title_link = card.select_one('.meta-data-title a') or anchor
        name = utils.cleantext(utils.safe_get_text(title_link)).title()
        duration = utils.safe_get_text(card.select_one('.icon.fa-clock-o'))

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('hqporner.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videourl))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videourl, 'HQPLAY', img, name, duration=duration, contextm=contextmenu)

    pagination = soup.select_one('ul.actions.pagination')
    if pagination:
        next_link = pagination.select_one('a.button.mobile-pagi[href]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_url = site.url + next_href.lstrip('/')
                site.add_dir('Next Page', next_url, 'HQLIST', site.img_next)
    utils.eod()


@site.register()
def HQCAT(url):
    link = utils.getHtml(url, '')
    soup = utils.parse_html(link)
    entries = []
    for heading in soup.select('h3 a[href]'):
        caturl = utils.safe_get_attr(heading, 'href')
        if not caturl or not caturl.startswith('/category'):
            continue
        name = utils.safe_get_text(heading)
        entries.append((name, site.url + caturl.lstrip('/')))

    for name, caturl in sorted(entries, key=lambda x: x[0].lower()):
        site.add_dir(name.title(), caturl, 'HQLIST', site.img_cat)
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
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videopage = utils.getHtml(url, url)
    iframeurl = re.compile(r"nativeplayer\.php\?i=([^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)[0]

    if iframeurl.startswith('//'):
        iframeurl = 'https:' + iframeurl

    if 'bemywife' in iframeurl:
        videourl = getBMW(iframeurl)
    elif '5.79' in iframeurl:
        videourl = getIP(iframeurl)
    elif 'flyflv' in iframeurl:
        videourl = getFly(iframeurl)
    elif 'hqwo' in iframeurl:
        videourl = getHQWO(iframeurl)
    else:
        videourl = iframeurl
        vp.play_from_link_to_resolve(videourl)
        return
    vp.play_from_direct_link(videourl)


def getBMW(url):
    videopage = utils.getHtml(url, '')
    vdiv = re.search(r'function do_pl\(\)\s*{(.*)};', videopage)
    if vdiv:
        vdiv = vdiv.group(1)
        s = re.search(r'replaceAll\("([^"]+)",\s*([^)]+)', vdiv)
        if s:
            var = s.group(1)
            params = s.group(2).split('+')
            repl = ''
            for param in params:
                if param.startswith('"'):
                    repl += param[1:-1]
                else:
                    repl += re.findall(r'{0}="([^"]+)'.format(param), vdiv)[0]
            vdiv = vdiv.replace(var, repl)
        videopage = vdiv
    videos = re.compile(r'source\s*src=\\"([^\\]+).+?\\"([^\\\s]+)', re.DOTALL | re.IGNORECASE).findall(videopage)
    if not videos:
        videos = re.compile(r'file:\s*"([^"]+mp4)",\s*label:\s*"\d+', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videos:
        videos = {label: url for url, label in videos}
        videourl = utils.prefquality(videos, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl and videourl.startswith('//'):
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
    try:
        videopage = utils.getHtml(url, '')
    except urllib_error.HTTPError:
        return
    videos = re.compile(r'''source\s*src=['"]([^'"]+).+?label=['"]([^'"]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videos:
        videos = {label: url for url, label in videos}
        videourl = utils.prefquality(videos, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl and videourl.startswith('//'):
            videourl = 'https:' + videourl
        return videourl


def getHQWO(url):
    videopage = utils.getHtml(url, '')
    eurl = re.compile(r'''<script[^\n]+src='([^']+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    if eurl:
        videopage = utils.getHtml(eurl[0], 'https://hqwo.cc/')
        videos = re.compile(r'''file":\s*"([^"]+).+?label":\s*"([^"]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    else:
        videos = re.compile(r'''src=\\?"([^"\\]+)\\?"\s*title=\\?"([^"\\]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    if videos:
        videos = {label: url for url, label in videos}
        videourl = utils.prefquality(videos, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if videourl and videourl.startswith('//'):
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

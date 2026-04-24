'''
    Cumination
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 NothingGnome

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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('spankbang', '[COLOR hotpink]SpankBang[/COLOR]', 'https://spankbang.party/', 'spankbang.png', 'spankbang')
filterQ = utils.addon.getSetting("spankbang_quality") or 'All'
filterL = utils.addon.getSetting("spankbang_length") or 'All'


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'pornstars_alphabet', 'Models_alphabet', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 's/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Quality: [/COLOR] [COLOR orange]{}[/COLOR]'.format(filterQ), '', 'FilterQ', '', Folder=False)
    site.add_dir('[COLOR hotpink]Length: [/COLOR] [COLOR orange]{}[/COLOR]'.format(filterL), '', 'FilterL', '', Folder=False)
    List(site.url + 'new_videos/1/')
    utils.eod()


@site.register()
def List(url):
    filtersQ = {'All': '', '4k': 'uhd', '1080p': 'fhd', '720p': 'hd'}
    filtersL = {'All': '', '10+min': 10, '20+min': 20, '40+min': 40}
    if '?' in url:
        url = url.split('?')[0]
    url += '?o=new&q={}&d={}'.format(filtersQ[filterQ], filtersL[filterL])
    listhtml = utils.getHtml(url, '')
    # new video-item markup uses relative hrefs - absolutize them so Playvid gets a full URL
    listhtml = listhtml.replace('href="/', 'href="{}'.format(site.url))
    # scope to the last video-list block - every page (home, search, model) renders a
    # trending strip above the actual results using the same video-item markup, so
    # take only the final block to avoid the trending items leaking into every listing
    blocks = list(re.finditer(r'<div[^>]*data-testid="video-list"', listhtml))
    if blocks:
        listhtml = listhtml[blocks[-1].start():]

    delimiter = 'data-testid="video-item"'
    re_videopage = r'<a\s+href="([^"]+)"'
    re_name = 'alt="([^"]+)"'
    re_img = r'src="([^"]+\.jpg[^"]*)"'
    re_duration = r'data-testid="video-item-length"\s*>\s*([^\s<]+)'
    re_quality = r'data-testid="video-item-resolution"\s*>\s*([^\s<]+)'

    utils.videos_list(site, 'spankbang.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality)
    nextp = re.compile(r'class="next"><a\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1)
        np = re.findall(r'/(\d+)/', nextp)[-1]
        lp = re.compile(r'>(\d+)<[^"]+class="next"><', re.DOTALL | re.IGNORECASE).findall(listhtml)
        if lp:
            lp = '/' + lp[0]
        else:
            lp = ''
        # nextp is already absolute thanks to the href= replace above
        site.add_dir('Next Page.. ({}{})'.format(np, lp), nextp, 'List', site.img_next)
    # elif nextps:
    #     nextp = nextps.group(1)
    #     pgtxt = re.findall(r'class="status">(.*?)</span', listhtml)[0].replace('<span>/', 'of').capitalize()
    #     site.add_dir('Next Page... (Currently in {})'.format(pgtxt), site.url[:-1] + nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title + '/'
        List(searchUrl)


@site.register()
def Tags(url):
    cathtml = utils.getHtml(url, '')
    # the full A-Z tag list still renders with the classic keyword markup - the
    # featured/popular strip at the top uses data-testid="tag" but only holds ~40 items
    match = re.compile(
        r'<a\s+href="([^"]+)"\s+class="keyword">([^<]+)<',
        re.DOTALL | re.IGNORECASE,
    ).findall(cathtml)
    # the page renders a "Top Tags" strip above the full A-Z list using the same markup,
    # so each popular tag shows up twice - dedup by href, keep first occurrence
    seen = set()
    unique = [(h, n) for h, n in match if not (h in seen or seen.add(h))]
    for catpage, name in sorted(unique, key=lambda x: x[1].lower()):
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        site.add_dir(name.strip(), catpage, 'List')
    utils.eod()


@site.register()
def Models_alphabet(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(
        r'href="([^"]+)"[^>]*data-testid="alphabet-letter"[^>]*>\s*([^\s<]+)\s*<',
        re.DOTALL | re.IGNORECASE,
    ).findall(cathtml)
    for catpage, name in match:
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        site.add_dir(name.strip(), catpage, 'Models', '', '')
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(
        r'<a\s+href="([^"]*/pornstar/[^"]*)"[^>]*>\s*([^\n<]+?)\s*<span[^>]*>\s*(\d+)\s*<',
        re.DOTALL | re.IGNORECASE,
    ).findall(cathtml)
    for catpage, name, videos in match:
        if catpage.startswith('/'):
            catpage = site.url[:-1] + catpage
        name = name.strip() + ' [COLOR hotpink]({})[/COLOR]'.format(videos)
        site.add_dir(name, catpage, 'List', '', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, '')
    sources = {}
    srcs = re.compile(r'''["'](240p|320p|480p|720p|1080p|4k)["']:\s*\[["']([^"']+)''', re.DOTALL | re.IGNORECASE).findall(html)
    for quality, videourl in srcs:
        if videourl:
            sources[quality] = videourl
    videourl = utils.prefquality(sources, sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)
    if not videourl:
        return
    videourl = videourl.replace(r'\u0026', '&')
    videourl += '|User-Agent={0}&Referer={1}'.format(utils.USER_AGENT, url)
    vp.play_from_direct_link(videourl)


@site.register()
def FilterQ():
    filters = {'All': 1, '4k': 2, '1080p': 3, '720p': 4}
    f = utils.selector('Select resolution', filters.keys(), sort_by=lambda x: filters[x])
    if f:
        utils.addon.setSetting('spankbang_quality', f)
        utils.refresh()


@site.register()
def FilterL():
    filters = {'All', '10+min', '20+min', '40+min'}
    f = utils.selector('Select length', filters, reverse=True)
    if f:
        utils.addon.setSetting('spankbang_length', f)
        utils.refresh()

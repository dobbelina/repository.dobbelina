'''
    Cumination
    Copyright (C) 2020 Cumination

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
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite('speedporn', '[COLOR hotpink]SpeedPorn[/COLOR]', 'https://speedporn.net/', 'speedporn.png', 'speedporn')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{}categories/'.format(site.url), 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR] - Loads all the pages', '{}categories/'.format(site.url), 'Categories_all', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', '{}pornstars/'.format(site.url), 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Featured movies[/COLOR]', '{}category/featured/'.format(site.url), 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', '{}all-porn-movie-studios/'.format(site.url), 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{}?s='.format(site.url), 'Search', site.img_search)
    List('{}?filter=latest'.format(site.url))
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'class="thumb" href="([^"]+)".+?data-src="([^"]+)".+?span class="title">([^<]+)</span', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('speedporn.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, contextm=contextmenu)
    next_page = re.compile(r'class="next page-link" href="([^"]+)">&raquo;<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if next_page:
        next_page = next_page[0]
        page_nr = re.findall(r'\d+', next_page)[-1]
        site.add_dir('Next Page (' + str(page_nr) + ')', next_page, 'List', site.img_next)
    utils.eod()


@site.register()
def List_all(url):
    nextpg = True
    while nextpg:
        try:
            listhtml = utils.getHtml(url)
            match = re.compile(r'class="thumb" href="([^"]+)".+?data-src="([^"]+)".+?span class="title">([^<]+)</span', re.DOTALL | re.IGNORECASE).findall(listhtml)
            for videopage, img, name in match:
                name = utils.cleantext(name)
                contextmenu = []
                contexturl = (utils.addon_sys
                                + "?mode=" + str('speedporn.Lookupinfo')
                                + "&url=" + urllib_parse.quote_plus(videopage))
                contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

                site.add_download_link(name, videopage, 'Playvid', img, contextm=contextmenu)
            if len(match) == 49:
                next_page = re.compile(r'class="next page-link" href="([^"]+)">&raquo;<', re.DOTALL | re.IGNORECASE).findall(listhtml)
                if next_page:
                    url = next_page[0]
            else:
                nextpg = False
        except:
            nextpg = False
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'class="video-block video-block-cat".+?href="([^"]+)".+?data-src="([^"]+)".+?class="title">([^<]+)<.+?class="video-datas">([^<]+)</div', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos.strip() + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    next_page = re.compile(r'class="next page-link" href="([^"]+)">&raquo;<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    if next_page:
        next_page = next_page[0]
        page_nr = re.findall(r'\d+', next_page)[-1]
        site.add_dir('Next Page (' + str(page_nr) + ')', next_page, 'Categories', site.img_next)
    utils.eod()


@site.register()
def Categories_all(url):
    nextpg = True
    while nextpg:
        try:
            cathtml = utils.getHtml(url, '')
            match = re.compile(r'class="video-block video-block-cat".+?href="([^"]+)".+?data-src="([^"]+)".+?class="title">([^<]+)<.+?class="video-datas">([^<]+)</div', re.DOTALL | re.IGNORECASE).findall(cathtml)
            for catpage, img, name, videos in match:
                name = utils.cleantext(name) + " [COLOR deeppink]" + videos.strip() + "[/COLOR]"
                site.add_dir(name, catpage, 'List_all', img)
            if len(match) == 49:
                next_page = re.compile(r'class="next page-link" href="([^"]+)">&raquo;<', re.DOTALL | re.IGNORECASE).findall(cathtml)
                if next_page:
                    url = next_page[0]
            else:
                nextpg = False
        except:
            nextpg = False
    utils.eod()


@site.register()
def Tags(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('div class="tag-item"><a href="([^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)
    videopage = videopage.split('>Watch Online')[-1]

    srcs = re.compile(r'<a title="([^"]+)" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    for title, src in srcs:
        title = utils.cleantext(title)
        title = title.split(' on ')[-1]
        src = src.split('?link=')[-1]
        if 'mangovideo' in src:
            html = utils.getHtml(src, url)
            if '=' in src:
                src = src.split('=')[-1]
            murl = re.compile(r"video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)
            if murl:
                if murl[0].startswith('function/'):
                    license = re.findall(r"license_code:\s*'([^']+)", html)[0]
                    murl = kvs_decode(murl[0], license)
            else:
                murl = re.compile(r'action=[^=]+=([^\?]+)/\?download', re.DOTALL | re.IGNORECASE).findall(html)
                if murl:
                    murl = murl[0]
            if murl:
                links[title] = murl
        elif vp.resolveurl.HostedMediaFile(src).valid_url():
            links[title] = src
    videourl = utils.selector('Select server', links, setting_valid=False)
    if not videourl:
        vp.progress.close()
        return

    vp.progress.update(90, "[CR]Loading video page[CR]")
    if 'mango' in videourl:
        vp.play_from_direct_link(videourl)
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
def Lookupinfo(url):
    lookup_list = [
        ("Genre", '(genres/[^"]+)" title="([^"]+)', ''),
        ("Studio", '(director/[^"]+)" title="([^"]+)', ''),
        ("Actor", '(pornstars/[^"]+)" title="([^"]+)', ''),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'speedporn.List', lookup_list)
    lookupinfo.getinfo()
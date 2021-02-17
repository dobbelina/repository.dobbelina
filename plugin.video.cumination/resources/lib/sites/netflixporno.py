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
import xbmcplugin, xbmcgui
from six.moves import urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

progress = utils.progress

site = AdultSite('netflixporno', '[COLOR hotpink]NetflixPorno[/COLOR]', 'https://netflixporno.net/', 'https://netflixporno.net/wp-content/uploads/2018/04/netflixporno-1.png', 'netflixporno')

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]','https://netflixporno.net/search/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]New Release[/COLOR]','https://netflixporno.net/genre/new-release/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]XXX Scenes[/COLOR]','https://netflixporno.net/genre/clips-scenes/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Parody Movies[/COLOR]','https://netflixporno.net/genre/parodies/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]','https://netflixporno.net/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]','https://netflixporno.net/', 'Studios', site.img_cat)
    List('https://netflixporno.net/')
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('<article[^>]+>.+?<a href="([^"]+)".*?src="([^"]+)".+?Title">([^"]+)</div', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, '')
    try:
        nextp=re.compile('<a class="next page-numbers" href="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        nextp = nextp[0].replace("&#038;", "&")
        site.add_dir('Next Page', nextp, 'List', site.img_next)
    except: pass
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        utils.kodilog("NetFlixPorno Searching URL: " + searchUrl)
        List(searchUrl)


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    match = re.compile(r'cat-item-\d+"><a href="([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', site.img_cat)
    utils.eod()

@site.register()
def Studios(url):
    try:
        studhtml = utils.getHtml(url, '')
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    match = re.compile('menu-category-list"><a href="(.+?)">(.+?)</a>', re.DOTALL | re.IGNORECASE).findall(studhtml)
    for studpage, name in match[2:]:
        site.add_dir(name, studpage, 'List', site.img_cat)
    utils.eod()


def url_decode(str):
    if '/goto/' not in str:
        result = str
    else:
        try:
            result = url_decode(base64.b64decode(re.search('/goto/(.+)', str).group(1)))
        except:
            result = str
    return result


@site.register()
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        html = utils.getHtml(url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return
#    html = re.compile('<center><!-- Display player -->(.+?)<center>', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    srcs = re.compile('<a title="([^"]+)" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for title, src in srcs:
        title = utils.cleantext(title)
        title = title.split(' on ')[-1]
        if '/goto/' in src:
            src = url_decode(src)
        if vp.resolveurl.HostedMediaFile(src).valid_url():
            links[title] = src
        if 'mangovideo' in src:
            title = title.replace(' - ','')
            html = utils.getHtml(src)
            murl = re.compile("video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)[0]
            if murl.startswith('function/'):
                license = re.findall(r"license_code:\s*'([^']+)", html)[0]
                murl = kvs_decode(murl, license)
            links[title] = murl
    videourl = utils.selector('Select server', links)
    if not videourl:
        return
    vp.progress.update(90, "[CR]Loading video page[CR]")
    if 'mango' in videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)

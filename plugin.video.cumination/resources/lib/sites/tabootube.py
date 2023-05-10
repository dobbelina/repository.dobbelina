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
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite('tabootube', '[COLOR hotpink]TabooTube[/COLOR]', 'https://www.tabootube.xxx/', 'https://www.tabootube.xxx/contents/other/theme/logo.png', 'tabootube')


@site.register(default_mode=True)
def Main(url):
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + '?mode=async&function=get_block&block_id=list_videos_most_recent_videos&sort_by=post_date&from=1', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile(r'class="item item-\d+\s*?">\s+<a href="https://www\.tabootube\.xxx/([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        videopage = site.url + videopage

        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('tabootube.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration)

    np = re.compile(r'class="next">.*?post_date;from:(\d+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        np = np.group(1)
        nextp = url.replace('from=' + str(page), 'from=' + np)
        site.add_dir('Next Page ({})'.format(np), nextp, 'List', site.img_next, page=np)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    srcs = re.findall(r"video_url:\s*'([^']+)'", html)
    if srcs:
        surl = srcs[0]
        vp.progress.update(50, "[CR]Video found[CR]")
        if surl.startswith('function/'):
            lcode = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, lcode)
        if 'get_file' in surl:
            surl = utils.getVideoLink(surl, site.url)
        surl = '{0}|User-Agent=iPad&Referer={1}'.format(surl, site.url)
        vp.play_from_direct_link(surl)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')
        return



@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        catpage = catpage + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, catpage, 'List', '', page=1)
    utils.eod()


@site.register()
def Tags(url):
    try:
        taghtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('/(tags/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(taghtml)
    for tagpage, name in match:
        name = utils.cleantext(name)
        tagpage = site.url + tagpage + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        site.add_dir(name, tagpage, 'List', '', page=1)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        List(searchUrl, 1)


@site.register()
def Lookupinfo(url):
    utils.kodilog(url)
    try:
        listhtml = utils.getHtml(url)
    except:
        return None

    infodict = {}

    categories = re.compile(r'Categories:\s*?<a href="([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if categories:
        for url, cat in categories:
            cat = "Cat - " + cat.strip()
            infodict[cat] = url

    actors = re.compile('/(models/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if actors:
        for url, actor in actors:
            actor = "Actor - " + actor.strip()
            infodict[actor] = site.url + url

    tags = re.compile('/(tags/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if tags:
        for url, tag in tags:
            tag = "Tag - " + tag.strip()
            infodict[tag] = site.url + url

    if infodict:
        selected_item = utils.selector('Choose item', infodict, show_on_one=True)
        if not selected_item:
            return
        selected_item + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1'
        contexturl = (utils.addon_sys
                      + "?mode=" + str('tabootube.List')
                      + "&url=" + urllib_parse.quote_plus(selected_item)
                      + "&page=1")
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    else:
        utils.notify('Notify', 'No actors, studios or genres found for this video')
    return
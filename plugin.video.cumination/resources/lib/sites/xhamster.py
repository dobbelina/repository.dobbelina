'''
    Cumination
    Copyright (C) 2022 Team Cumination

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
import json
from six.moves import urllib_parse
from kodi_six import xbmc, xbmcgui, xbmcplugin
import datetime

site = AdultSite('xhamster', '[COLOR hotpink]xHamster[/COLOR]', 'https://xhamster2.com/', 'xhamster.png', 'xhamster')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Celebrities[/COLOR]', site.url + 'celebrities', 'Celebrities', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'newest')
    utils.eod()


@site.register()
def List(url):
    url = update_url(url)

    context_category = (utils.addon_sys + "?mode=" + str('xhamster.ContextCategory'))
    context_length = (utils.addon_sys + "?mode=" + str('xhamster.ContextLength'))
    context_quality = (utils.addon_sys + "?mode=" + str('xhamster.ContextQuality'))
    contextmenu = [('[COLOR violet]Category[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('category')), 'RunPlugin(' + context_category + ')'),
                   ('[COLOR violet]Length[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('length')), 'RunPlugin(' + context_length + ')'),
                   ('[COLOR violet]Quality[/COLOR] [COLOR orange]{}[/COLOR]'.format(get_setting('quality')), 'RunPlugin(' + context_quality + ')')]

    try:
        response = utils.getHtml(url, site.url)
    except Exception as e:
        if '404' in str(e):
            site.add_dir('No videos found. [COLOR hotpink]Clear all filters.[/COLOR]', '', 'ResetFilters', Folder=False, contextm=contextmenu)
            utils.eod()
        return
    listjson = response.split('window.initials=')[-1].split(';</script>')[0]
    jdata = json.loads(listjson)
    if "trendingVideoListComponent" in jdata:
        videos = jdata["trendingVideoListComponent"]["models"]
    elif "searchResult" in jdata:
        videos = jdata["searchResult"]["models"]
    elif "pagesNewestComponent" in jdata:
        videos = jdata["pagesNewestComponent"]["videoListProps"]["models"]
    elif "pagesCategoryComponent" in jdata:
        videos = jdata["pagesCategoryComponent"]["trendingVideoListProps"]["models"]
    else:
        utils.notify('Cumination', 'No video found.')

    for video in videos:
        name = video["title"] if utils.PY3 else video["title"].encode('utf8')
        videolink = video["pageURL"]
        img = video["thumbURL"]
        if not img:
            continue
        length = str(datetime.timedelta(seconds=video["duration"]))
        if length.startswith('0:'):
            length = length[2:]
        hd = "4k" if video.get("isUHD", False) else "HD" if video.get("isHD", False) else ""
        name = '[COLOR blue][VR][/COLOR] ' + name if video.get("isVR", False) else name
        name = name + ' [COLOR blue][Full Video][/COLOR]' if video.get("hasProducerBadge", False) else name
        name = name + ' [COLOR orange][Amateur][/COLOR]' if video.get("hasAmateurBadge", False) else name
        site.add_download_link(name, videolink, 'Playvid', img, name, contextm=contextmenu, duration=length, quality=hd)

    npurl = None
    if "pagesNewestComponent" in jdata:
        if "paginationProps" in jdata["pagesNewestComponent"]:
            np = jdata["pagesNewestComponent"]["paginationProps"]["currentPageNumber"] + 1
            lp = jdata["pagesNewestComponent"]["paginationProps"]["lastPageNumber"] + 1
            if lp >= np:
                npurl = jdata["pagesNewestComponent"]["paginationProps"]["pageLinkTemplate"].replace(r'\/', '/').replace('{#}', '{}'.format(np))
    elif "pagesCategoryComponent" in jdata:
        if "paginationProps" in jdata["pagesCategoryComponent"]:
            np = jdata["pagesCategoryComponent"]["paginationProps"]["currentPageNumber"] + 1
            lp = jdata["pagesCategoryComponent"]["paginationProps"]["lastPageNumber"] + 1
            if lp >= np:
                npurl = jdata["pagesCategoryComponent"]["paginationProps"]["pageLinkTemplate"].replace(r'\/', '/').replace('{#}', '{}'.format(np))
    elif "paginationComponent" in jdata:
        np = jdata["paginationComponent"]["currentPageNumber"] + 1
        lp = jdata["paginationComponent"]["lastPageNumber"]
        if lp >= np:
            npurl = jdata["paginationComponent"]["pageLinkTemplate"].replace(r'\/', '/').replace('{#}', '{}'.format(np))
    elif "pagination" in jdata:
        np = jdata["pagination"]["next"]
        lp = jdata["pagination"]["maxPages"]
        if lp >= np:
            npurl = jdata["pagination"]["pageLinkTemplate"].replace(r'\/', '/').replace('{#}', '{}'.format(np))
    elif "page" in jdata:
        np = jdata["page"] + 1
        lp = None
        if "maxPages" in jdata:
            lp = jdata["maxPages"]
        if not lp or (np and lp >= np):
            match = re.compile(r'data-page="next"\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(response)
            if match:
                npurl = match.group(1)
    if npurl:
        npurl = npurl.replace('&#x3D;', '=').replace('&amp;', '&')
        cm_page = (utils.addon_sys + "?mode=xhamster.GotoPage&list_mode=xhamster.List&url=" + urllib_parse.quote_plus(npurl) + "&np=" + str(np) + "&lp=" + str(lp))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        npage = str(np) + '/' + str(lp) if lp else str(np)
        site.add_dir('Next Page (' + npage + ')', npurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_link_to_resolve(url)


@site.register()
def Categories(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/categories', '/gay/categories')
    elif cat == 'shemale':
        url = url.replace('/categories', '/shemale/categories')
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="item-6b822.+?href="([^"]+).+?src="([^"]+)"\s*alt="([^"]+)').findall(cathtml)
    for url, thumb, name in match:
        site.add_dir(utils.cleantext(name), url, 'List', thumb)
    utils.eod()


# @site.register()
# def Categories(url):
#     cat = get_setting('category')
#     if cat == 'gay':
#         url = url.replace('/categories', '/gay/categories')
#     elif cat == 'shemale':
#         url = url.replace('/categories', '/shemale/categories')
#     cathtml = utils.getHtml(url, site.url)
#     match = re.compile('class="root-9d8b4[^"]*" href="([^"]+)">((?:Popular|.))<').findall(cathtml)
#     for url, name in match:
#         site.add_dir(name.strip(), url, 'CategoriesA', '')
#     utils.eod()


@site.register()
def CategoriesA(url):
    cathtml = utils.getHtml(url, site.url)
    cathtml = cathtml.split('class="letter-blocks page"')[-1].split('class="search"')[0]
    match = re.compile('href="([^"]+)" data-role="tag-link"><!-- HTML_TAG_START -->([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(utils.cleantext(name.strip()), url + '/newest', 'List', '')
    utils.eod()


@site.register()
def Channels(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/channels', '/gay/channels')
    elif cat == 'shemale':
        url = url.replace('/channels', '/shemale/channels')
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'href="([^"]+)"[^>]*>(\s*\S\s*)<').findall(cathtml)
    for url, name in match:
        if '0' in name:
            continue
        site.add_dir(name.strip(), url, 'ChannelsA', '')
    utils.eod()


@site.register()
def ChannelsA(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div class="item">\s*<a href="([^"]+/channels/[^"]+)"[^>]*>([^<]+)<').findall(cathtml)
    for url, name in match:
        site.add_dir(utils.cleantext(name.strip()), url + '/newest', 'List', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Pornstars(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/pornstars', '/gay/pornstars')
    elif cat == 'shemale':
        url = url.replace('/pornstars', '/shemale/pornstars')
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'href="([^"]+/pornstars/all[^"]+)"[^>]*>(\s*\S\s*)<').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url, 'PornstarsA', '')
    utils.eod()


@site.register()
def PornstarsA(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div class="item">\s*<a href="([^"]+)">([^<]+)</a>').findall(cathtml)
    for url, name in match:
        site.add_dir(utils.cleantext(name.strip()), url + '/newest', 'List', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Celebrities(url):
    cat = get_setting('category')
    if cat == 'gay':
        url = url.replace('/celebrities', '/gay/celebrities')
    elif cat == 'shemale':
        url = url.replace('/celebrities', '/shemale/celebrities')
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<a class="" href="([^"]+)">\s*(\S)\s*</a>').findall(cathtml)
    for url, name in match:
        site.add_dir(name.strip(), url, 'CelebritiesA', '')
    utils.eod()


@site.register()
def CelebritiesA(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div class="item">\s*<a href="([^"]+)">([^<]+)</a>').findall(cathtml)
    for url, name in match:
        site.add_dir(utils.cleantext(name.strip()), url + '/newest', 'List', '')
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title + '?orientations=' + get_setting('category')
        List(searchUrl)


@site.register()
def ContextCategory():
    categories = {'straight': 1, 'gay': 2, 'shemale': 3}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamstercat', cat)
        if cat == 'straight':
            utils._getHtml('https://xhamster.com/?straight=', site.url)
        else:
            utils._getHtml('https://xhamster.com/' + cat, site.url)
        utils.refresh()


@site.register()
def ContextLength():
    categories = {'ALL': 1, '40+ min': 2, '10-40 min': 3, '0-10 min': 4}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamsterlen', cat)
        utils.refresh()


@site.register()
def ContextQuality():
    categories = {'ALL': 1, '2160p': 2, '1080p': 3, '720p': 4}
    cat = utils.selector('Select category', categories.keys(), sort_by=lambda x: categories[x])
    if cat:
        utils.addon.setSetting('xhamsterqual', cat)
        utils.refresh()


def get_setting(x):
    if x == 'category':
        ret = utils.addon.getSetting('xhamstercat') if utils.addon.getSetting('xhamstercat') else 'straight'
    if x == 'length':
        ret = utils.addon.getSetting('xhamsterlen') if utils.addon.getSetting('xhamsterlen') else 'ALL'
    if x == 'quality':
        ret = utils.addon.getSetting('xhamsterqual') if utils.addon.getSetting('xhamsterqual') else 'ALL'
    return ret


def update_url(url):
    cat = get_setting('category')
    old_cat = 'straight'
    if url.startswith(site.url + 'gay') or 'orientations=gay' in url:
        old_cat = 'gay'
    elif url.startswith(site.url + 'shemale') or 'orientations=shemale' in url:
        old_cat = 'shemale'

    if cat != old_cat:
        if '/search/' in url:
            url = re.sub(r'[\?&]page=[^\?&]+', '', url)
            url = re.sub(r'[\?&]orientations=[^\?&]+', '', url)
            if cat != 'straight':
                url += '&orientations=' + cat if '?' in url else '?orientations=' + cat
        else:
            url = re.sub(r'newest/\d+', 'newest', url)
            if old_cat == 'straight':
                url = url.replace(site.url, site.url + cat + '/')
            else:
                url = url.replace(site.url + old_cat, site.url[:-1]) if cat == 'straight' else url.replace(site.url + old_cat, site.url + cat)

    qual = get_setting('quality')
    if 'quality=720p' in url or ('hd/newest' in url and 'quality=1080p' not in url):
        old_qual = '720p'
    elif 'quality=1080p' in url:
        old_qual = '1080p'
    elif 'quality=2160p' in url or '4k/newest' in url:
        old_qual = '2160p'
    else:
        old_qual = 'ALL'

    if qual != old_qual:
        url = re.sub(r'[\?&]page=[^\?&]+', '', url)
        if 'search' in url:
            url = re.sub(r'[\?&]quality=[^\?&]+', '', url)
            if qual != 'ALL':
                url += '&quality=' + qual if '?' in url else '?quality=' + qual
        else:
            url = re.sub(r'newest/\d+', 'newest', url)
            url = url.replace('/hd/newest', 'newest').replace('/4k/newest', '/newest').replace('quality=1080p', '').replace('?&', '&').replace('&&', '&')

            url = url.split('newest')
            if qual == '720p':
                url[0] += 'hd/'
                url = 'newest'.join(url)
            elif qual == '2160p':
                url[0] += '4k/'
                url = 'newest'.join(url)
            else:
                url[0] += 'hd/'
                url = 'newest'.join(url)
                if '?' in url:
                    url += '&quality=1080p'
                else:
                    url += '?quality=1080p'
    length = get_setting('length')
    if 'max-duration=10' in url:
        old_length = '0-10 min'
    elif 'max-duration=40' in url:
        old_length = '10-40 min'
    elif 'min-duration=40' in url:
        old_length = '40+ min'
    else:
        old_length = 'ALL'

    if length != old_length:
        url = re.sub(r'[\?&]page=[^\?&]+', '', url)
        url = re.sub(r'newest/\d+', 'newest', url)
        url = re.sub(r'[\?&]min-duration=[^\?&]+', '', url)
        url = re.sub(r'[\?&]max-duration=[^\?&]+', '', url)
        if length == '0-10 min':
            url += '&max-duration=10' if '?' in url else '?max-duration=10'
        elif length == '10-40 min':
            url += '&min-duration=10' if '?' in url else '?min-duration=10'
            url += '&max-duration=40'
        elif length == '40+ min':
            url += '&min-duration=40' if '?' in url else '?min-duration=40'
    return url


@site.register()
def ResetFilters():
    utils.addon.setSetting('xhamstercat', 'straight')
    utils.addon.setSetting('xhamsterlen', 'ALL')
    utils.addon.setSetting('xhamsterqual', 'ALL')
    utils.refresh()
    return


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if lp and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        url = url.replace('newest/{}'.format(np), 'newest/{}'.format(pg))
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url) + "&page=" + str(pg))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')

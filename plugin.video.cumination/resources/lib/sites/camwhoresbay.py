"""
    Cumination site scraper
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
"""

import re
from six.moves import urllib_parse
import xbmcplugin
import xbmc
from random import randint
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode


site = AdultSite('camwhoresbay', '[COLOR hotpink]camwhoresbay[/COLOR]', 'https://www.camwhoresbay.com/', 'camwhoresbay.png', 'camwhoresbay')

getinput = utils._get_keyboard
cblogged = 'true' in utils.addon.getSetting('cblogged')


@site.register(default_mode=True)
def Main():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    cbsortorder = utils.addon.getSetting('cbsortorder') if utils.addon.getSetting('cbsortorder') else 'last_content_date'
    sortname = list(sort_orders.keys())[list(sort_orders.values()).index(cbsortorder)]

    context = (utils.addon_sys + "?mode=" + str('camwhoresbay.PLContextMenu'))
    contextmenu = [('[COLOR orange]Sort order[/COLOR]', 'RunPlugin(' + context + ')')]

    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR] [COLOR orange]{}[/COLOR]'.format(sortname), site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by={}&from=01'.format(cbsortorder), 'Playlists', site.img_cat, contextm=contextmenu)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    if not cblogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'CBLogin', '', Folder=False)
    elif cblogged:
        cbuser = utils.addon.getSetting('cbuser')
        site.add_dir('[COLOR violet]CWB Favorites[/COLOR]', site.url + 'my/favourites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_my_fav_videos=01', 'List', site.img_cat)
        site.add_dir('[COLOR hotpink]Logout {0}[/COLOR]'.format(cbuser), '', 'CBLogin', '', Folder=False)
    List(site.url + 'latest-updates/', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    listhtml = utils.getHtml(url, site.url, headers=hdr)
    if cblogged and ('>Log in<' in listhtml):
        if CBLogin(False):
            hdr['Cookie'] = get_cookies()
            listhtml = utils.getHtml(url, site.url, headers=hdr)
        else:
            return None

    match = re.compile(r'class="video-item([^"]+)".+?href="([^"]+)".+?title="([^"]+).+?(?:original|"cover"\s*src)="([^"]+)(.+?)clock\D+([\d:]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for private, videopage, name, img, hd, name2 in match:
        hd = 'HD' if '>HD<' in hd else ''
        name = utils.cleantext(name)
        if 'private' in private.lower():
            if not cblogged:
                continue
            private = "[COLOR blue] [PV][/COLOR] "
        else:
            private = ""
        name = private + name
        img = 'https:' + img if img.startswith('//') else img
        contextmenu = None
        if cblogged:
            contextadd = (utils.addon_sys
                          + "?mode=" + str('camwhoresbay.ContextMenu')
                          + "&url=" + urllib_parse.quote_plus(videopage)
                          + "&fav=add")
            contextdel = (utils.addon_sys
                          + "?mode=" + str('camwhoresbay.ContextMenu')
                          + "&url=" + urllib_parse.quote_plus(videopage)
                          + "&fav=del")
            contextmenu = [('[COLOR violet]Add to CWB favorites[/COLOR]', 'RunPlugin(' + contextadd + ')'),
                           ('[COLOR violet]Delete from CWB favorites[/COLOR]', 'RunPlugin(' + contextdel + ')')]

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=name2, quality=hd)

    if re.search(r'<li\s*class="next"><a', listhtml, re.DOTALL | re.IGNORECASE):
        lastp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lastp = '/{}'.format(lastp[0]) if lastp else ''
        if not page:
            page = 1
        npage = page + 1

        if '/categories/' in url:
            if '/{}/'.format(page) in url:
                nurl = url.replace(str(page), str(npage))
            else:
                nurl = url + '{}/'.format(npage)
        elif '/search/' in url:
            if 'from_videos={0:02d}'.format(page) in url:
                nurl = url.replace('from_videos={0:02d}'.format(page), 'from_videos={0:02d}'.format(npage))
            else:
                searchphrase = url.split('/')[-2]
                nurl = url + '?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={0}&category_ids=&sort_by=&from_videos={1:02d}'.format(searchphrase, npage)
        elif '/favourites/' in url:
            if 'from_my_fav_videos={0:02d}'.format(page) in url:
                nurl = url.replace('from_my_fav_videos={0:02d}'.format(page), 'from_my_fav_videos={0:02d}'.format(npage))
            else:
                utils.kodilog(' favorites pagination error')
                nurl = url
        elif '/playlists/' in url:
            if '?mode' not in url:
                url += '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=added2fav_date&from=1'
            if 'from={}'.format(page) in url:
                nurl = url.replace('from={}'.format(page), 'from={}'.format(npage))
            else:
                utils.kodilog(' playlist pagination error')
                nurl = url
        else:
            nurl = site.url[:-1] + re.compile(r'next"><a\s*href="(/[^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, npage)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    vpage = utils.getHtml(url, site.url, headers=hdr)

    sources = {}
    license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(vpage)[0]
    patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
    for pattern in patterns:
        items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
        for surl, qual in items:
            qual = '00' if qual == 'preview' else qual
            surl = kvs_decode(surl, license)
            sources.update({qual: surl})
    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'"item"\s*href="([^"]+)"\s*title="([^"]+)">\n\s*<div.+?src="([^"]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan][{}][/COLOR]'.format(name2)
        site.add_dir(name, catpage, 'List', img, 1)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playlists(url, page=1):
    cathtml = utils.getHtml(url, site.url)
    img = str(randint(1, 4))
    match = re.compile(r'class="item\s*".+?href="([^"]+)"\s*title="([^"]+)".+?class="thumb video' + img + '.+?data-original="([^"]+)".+?class="totalplaylist">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan][{}][/COLOR]'.format(name2)
        site.add_dir(name, catpage, 'List', img, 1)
    if re.search(r'<li\s*class="next"><a', cathtml, re.DOTALL | re.IGNORECASE):
        lastp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(cathtml)
        lastp = '/{}'.format(lastp[0]) if lastp else ''
        if not page:
            page = 1
        npage = page + 1
        if 'from={0:02d}'.format(page) in url:
            nurl = url.replace('from={0:02d}'.format(page), 'from={0:02d}'.format(npage))
        else:
            utils.kodilog(' Playlists pagination error')
            nurl = url
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'Playlists', site.img_next, npage)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl.format(title)
        List(searchUrl)


@site.register()
def CBLogin(logged=True):
    cblogged = utils.addon.getSetting('cblogged')
    if not logged:
        cblogged = False
        utils.addon.setSetting('cblogged', 'false')

    if not cblogged or 'false' in cblogged:
        cbuser = utils.addon.getSetting('cbuser') if utils.addon.getSetting('cbuser') else ''
        cbpass = utils.addon.getSetting('cbpass') if utils.addon.getSetting('cbpass') else ''
        if cbuser == '':
            cbuser = getinput(default=cbuser, heading='Input your camwhoresbay username')
            cbpass = getinput(default=cbpass, heading='Input your camwhoresbay password', hidden=True)

        loginurl = '{0}login/'.format(site.url)
        postRequest = {'action': 'login',
                       'email_link': '{0}email/'.format(site.url),
                       'format': 'json',
                       'mode': 'async',
                       'pass': cbpass,
                       'remember_me': '1',
                       'username': cbuser}
        response = utils._postHtml(loginurl, form_data=postRequest)
        if 'success' in response.lower():
            utils.addon.setSetting('cblogged', 'true')
            utils.addon.setSetting('cbuser', cbuser)
            utils.addon.setSetting('cbpass', cbpass)
            success = True
        else:
            utils.notify('Failure logging in', 'Failure, please check your username or password')
            utils.addon.setSetting('cbuser', '')
            utils.addon.setSetting('cbpass', '')
            success = False
    elif cblogged:
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('cbuser', '')
                utils.addon.setSetting('cbpass', '')
            utils.addon.setSetting('cblogged', 'false')
            utils._getHtml(site.url + 'logout/')
    if logged:
        xbmc.executebuiltin('Container.Refresh')
    else:
        return success


@site.register()
def ContextMenu(url, fav):
    id = url.split("/")[4]
    fav_addurl = url + '?mode=async&format=json&action=add_to_favourites&video_id=' + id + '&album_id=&fav_type=0&playlist_id=0'
    fav_delurl = url + '?mode=async&format=json&action=delete_from_favourites&video_id=' + id + '&album_id=&fav_type=0&playlist_id=0'
    fav_url = fav_addurl if fav == 'add' else fav_delurl

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    resp = utils.getHtml(fav_url, site.url, headers=hdr)

    if fav == 'add':
        if ('success') in resp:
            utils.notify('Favorites', 'Added to CWB Favorites')
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify('Favorites', msg)
        return
    if fav == 'del':
        if ('success') in resp:
            utils.notify('Deleted from CWB Favorites')
            xbmc.executebuiltin('Container.Refresh')
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify(msg)
        return


@site.register()
def PLContextMenu():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    order = utils.selector('Select order', sort_orders)
    if order:
        utils.addon.setSetting('cbsortorder', order)
        xbmc.executebuiltin('Container.Refresh')


def get_cookies():
    domain = site.url.split('www')[-1][:-1]
    cookiestr = 'kt_tcookie=1'
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'PHPSESSID':
            cookiestr += '; PHPSESSID=' + cookie.value
        if cookie.domain == domain and cookie.name == 'kt_ips':
            cookiestr += '; kt_ips=' + cookie.value
        if cookie.domain == domain and cookie.name == 'kt_member':
            cookiestr += '; kt_member=' + cookie.value
    if cblogged and 'kt_member' not in cookiestr:
        CBLogin(False)
    return cookiestr

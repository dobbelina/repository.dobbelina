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
import xbmcgui
import xbmc
from random import randint
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode


site = AdultSite('pornwild', '[COLOR hotpink]PornWild[/COLOR]', 'https://pornwild.com/', 'pornwild.png', 'pornwild')

getinput = utils._get_keyboard
pwlogged = 'true' in utils.addon.getSetting('pwlogged')


@site.register(default_mode=True)
def Main():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    pwsortorder = utils.addon.getSetting('pwsortorder') if utils.addon.getSetting('pwsortorder') else 'last_content_date'
    sortname = list(sort_orders.keys())[list(sort_orders.values()).index(pwsortorder)]

    context = (utils.addon_sys + "?mode=" + str('pornwild.PLContextMenu'))
    contextmenu = [('[COLOR orange]Sort order[/COLOR]', 'RunPlugin(' + context + ')')]

    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR] [COLOR orange]{}[/COLOR]'.format(sortname), site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by={}&from=01'.format(pwsortorder), 'Playlists', site.img_cat, contextm=contextmenu)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    if not pwlogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'PWLogin', '', Folder=False)
    elif pwlogged:
        pwuser = utils.addon.getSetting('pwuser')
        site.add_dir('[COLOR violet]PW Favorites[/COLOR]', site.url + 'my/favorites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_my_fav_videos=01', 'List', site.img_cat)
        site.add_dir('[COLOR hotpink]Logout {0}[/COLOR]'.format(pwuser), '', 'PWLogin', '', Folder=False)
    List(site.url + 'latest-updates/', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    listhtml = utils.getHtml(url, site.url, headers=hdr)
    if pwlogged and ('>Log in<' in listhtml):
        if PWLogin(False):
            hdr['Cookie'] = get_cookies()
            listhtml = utils.getHtml(url, site.url, headers=hdr)
        else:
            return None

    videos = listhtml.split('class="item')
    for video in videos:
        if 'class="duration"' in video:
            match = re.compile(r'^([^"]+)".+?href="([^"]+)".+?title="([^"]+).+?(?:original|"cover"\s*src)="([^"]+)(.+?)class="duration">([\d:]+)', re.DOTALL | re.IGNORECASE).findall(video)
        else:
            match = re.compile(r'^([^"]*)".+?data-playlist-item="([^"]+)".+?()data-original="([^"]+)"()\s*alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(video)
        for private, videopage, name, img, hd, name2 in match:
            if not name:
                name = name2
                name2 = ''
            hd = 'HD' if '>HD<' in hd else ''
            name = utils.cleantext(name)
            if 'private' in private.lower():
                if not pwlogged:
                    continue
                private = "[COLOR blue] [PV][/COLOR] "
            else:
                private = ""
            name = private + name
            img = 'https:' + img if img.startswith('//') else img
            contextmenu = None
            if pwlogged:
                contextadd = (utils.addon_sys
                              + "?mode=" + str('pornwild.ContextMenu')
                              + "&url=" + urllib_parse.quote_plus(videopage)
                              + "&fav=add")
                contextdel = (utils.addon_sys
                              + "?mode=" + str('pornwild.ContextMenu')
                              + "&url=" + urllib_parse.quote_plus(videopage)
                              + "&fav=del")
                contextmenu = [('[COLOR violet]Add to PW favorites[/COLOR]', 'RunPlugin(' + contextadd + ')'),
                               ('[COLOR violet]Delete from PW favorites[/COLOR]', 'RunPlugin(' + contextdel + ')')]

            site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=name2, quality=hd)

    if re.search(r'<li\s*class="next"><a', listhtml, re.DOTALL | re.IGNORECASE):
        lastp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lastp = '/{}'.format(lastp[0]) if lastp else ''

        page = 1 if not page else page
        npage = page + 1
        if '?' in url:
            nurl = re.sub(r'([&?])from([^=]*)=(\d+)', r'\1from\2={0:02d}', url).format(npage)
        else:
            nurl = url.replace('/{}/'.format(page), '/{}/'.format(npage)) if '/{}/'.format(page) in url else '{}{}/'.format(url, npage)

        cm_page = (utils.addon_sys + "?mode=pornwild.GotoPage&list_mode=pornwild.List&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&lp=" + lastp.replace('/', ''))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, npage, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        if url.endswith('/{}/'.format(np)):
            url = '/{}/'.format(pg).join(url.rsplit('/{}/'.format(np), 1))
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url) + "&page=" + str(pg))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


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
                r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)",
                r"video_url:\s*'([^']+)',\s*postfix:\s*'_([^']*)\.mp4',"]
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
    match = re.compile(r'"item\s*"\s*href="([^"]+)"\s*title="([^"]+)">\n\s*<div.+?src="([^"]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan][{}][/COLOR]'.format(name2)
        site.add_dir(name, catpage, 'List', img, 1)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playlists(url, page=1):
    cathtml = utils.getHtml(url, site.url)
    img = str(randint(1, 4))
    match = re.compile(r'class="item\s*".+?href="([^"]+)"\s*title="([^"]+)".+? video{} .+?data-original="([^"]+)".+?class="videos">([^<]+)'.format(img), re.DOTALL | re.IGNORECASE).findall(cathtml)

    for catpage, name, img, name2 in match:
        name = utils.cleantext(name) + ' [COLOR cyan][{}][/COLOR]'.format(name2)
        catpage += '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=added2fav_date&from=1'
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
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl.format(title) + '?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={}&category_ids=&sort_by=&from_videos=1'.format(title)
        List(searchUrl)


@site.register()
def PWLogin(logged=True):
    pwlogged = utils.addon.getSetting('pwlogged')
    if not logged:
        pwlogged = False
        utils.addon.setSetting('pwlogged', 'false')

    if not pwlogged or 'false' in pwlogged:
        pwuser = utils.addon.getSetting('pwuser') if utils.addon.getSetting('pwuser') else ''
        pwpass = utils.addon.getSetting('pwpass') if utils.addon.getSetting('pwpass') else ''
        if pwuser == '':
            pwuser = getinput(default=pwuser, heading='Input your pornwild username')
            pwpass = getinput(default=pwpass, heading='Input your pornwild password', hidden=True)

        loginurl = '{0}login/'.format(site.url)
        postRequest = {'action': 'login',
                       'email_link': '{0}email/'.format(site.url),
                       'format': 'json',
                       'mode': 'async',
                       'pass': pwpass,
                       'remember_me': '1',
                       'username': pwuser}
        response = utils._postHtml(loginurl, form_data=postRequest)
        if 'success' in response.lower():
            utils.addon.setSetting('pwlogged', 'true')
            utils.addon.setSetting('pwuser', pwuser)
            utils.addon.setSetting('pwpass', pwpass)
            success = True
        else:
            utils.notify('Failure logging in', 'Failure, please check your username or password')
            utils.addon.setSetting('pwuser', '')
            utils.addon.setSetting('pwpass', '')
            success = False
    elif pwlogged:
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('pwuser', '')
                utils.addon.setSetting('pwpass', '')
            utils.addon.setSetting('pwlogged', 'false')
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
            utils.notify('Favorites', 'Added to PW Favorites')
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify('Favorites', msg)
        return
    if fav == 'del':
        if ('success') in resp:
            utils.notify('Deleted from PW Favorites')
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
        utils.addon.setSetting('pwsortorder', order)
        xbmc.executebuiltin('Container.Refresh')


def get_cookies():
    domain = '.' + site.url.split('//')[-1][:-1].replace('www.', '')
    cookiestr = 'kt_tcookie=1'
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'PHPSESSID':
            cookiestr += '; PHPSESSID=' + cookie.value
        if cookie.domain == domain and cookie.name == 'kt_ips':
            cookiestr += '; kt_ips=' + cookie.value
        if cookie.domain == domain and cookie.name == 'kt_member':
            cookiestr += '; kt_member=' + cookie.value
        if cookie.domain == domain and cookie.name == '__ddg1_':
            cookiestr += '; __ddg1_=' + cookie.value
    if pwlogged and 'kt_member' not in cookiestr:
        PWLogin(False)
    return cookiestr

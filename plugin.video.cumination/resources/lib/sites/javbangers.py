"""
    Cumination site scraper
    Copyright (C) 2020 Team Cumination

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
import xbmcgui
from random import randint
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode


site = AdultSite('javbangers', '[COLOR hotpink]JAV Bangers[/COLOR]', 'https://www.javbangers.com/', 'javbangers.png', 'javbangers')

getinput = utils._get_keyboard
jblogged = 'true' in utils.addon.getSetting('jblogged')


@site.register(default_mode=True)
def Main():
    sort_orders = {'Recently updated': 'last_content_date', 'Most viewed': 'playlist_viewed', 'Top rated': 'rating', 'Most commented': 'most_commented', 'Most videos': 'total_videos'}
    jbsortorder = utils.addon.getSetting('jbsortorder') if utils.addon.getSetting('jbsortorder') else 'last_content_date'
    sortname = list(sort_orders.keys())[list(sort_orders.values()).index(jbsortorder)]

    context = (utils.addon_sys + "?mode=" + str('javbangers.PLContextMenu'))
    contextmenu = [('[COLOR orange]Sort order[/COLOR]', 'RunPlugin(' + context + ')')]

    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR] [COLOR orange]{}[/COLOR]'.format(sortname), site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by={}&from=01'.format(jbsortorder), 'Playlists', site.img_cat, contextm=contextmenu)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{0}/', 'Search', site.img_search)
    if not jblogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'JBLogin', '', Folder=False)
    elif jblogged:
        jbuser = utils.addon.getSetting('jbuser')
        site.add_dir('[COLOR violet]JB Favorites[/COLOR]', site.url + 'my/favourites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_my_fav_videos=01', 'List', site.img_cat)
        site.add_dir('[COLOR hotpink]Logout {0}[/COLOR]'.format(jbuser), '', 'JBLogin', '', Folder=False)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    listhtml = utils.getHtml(url, site.url, headers=hdr)
    if jblogged and ('>Log in<' in listhtml):
        if JBLogin(False):
            hdr['Cookie'] = get_cookies()
            listhtml = utils.getHtml(url, site.url, headers=hdr)
        else:
            return None

    match = re.compile(r'class="video-item([^"]+)".+?href="([^"]+)".+?title="([^"]+).+?(?:original|"cover"\s*src)="([^"]+)(.+?)clock\D+([\d:]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for private, videopage, name, img, hd, name2 in match:
        hd = 'HD' if '>HD<' in hd else ''
        name = utils.cleantext(name)
        if 'private' in private.lower():
            if not jblogged:
                continue
            private = "[COLOR blue] [PV][/COLOR] "
        else:
            private = ""
        name = private + name

        contextmenu = []
        contexturl = (utils.addon_sys
                      + "?mode=" + str('javbangers.Lookupinfo')
                      + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))
        if jblogged:
            contextadd = (utils.addon_sys
                          + "?mode=" + str('javbangers.ContextMenu')
                          + "&url=" + urllib_parse.quote_plus(videopage)
                          + "&fav=add")
            contextdel = (utils.addon_sys
                          + "?mode=" + str('javbangers.ContextMenu')
                          + "&url=" + urllib_parse.quote_plus(videopage)
                          + "&fav=del")
            contextmenu.append(('[COLOR violet]Add to JB favorites[/COLOR]', 'RunPlugin(' + contextadd + ')'))
            contextmenu.append(('[COLOR violet]Delete from JB favorites[/COLOR]', 'RunPlugin(' + contextdel + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=name2, quality=hd)

    match = re.search(r'class="page-current"><span>(\d+)<.+?class="next">.+?data-block-id="([^"]+)"\s+data-parameters="([^"]+)">Next', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        npage = int(match.group(1)) + 1
        block_id = match.group(2)
        params = match.group(3).replace(';', '&').replace(':', '=')
        rnd = 1000000000000 + randint(0, 999999999999)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
        lpnr, lastp = None, ''
        match = re.search(r':(\d+)">Last', listhtml, re.DOTALL | re.IGNORECASE)
        if match:
            lpnr = match.group(1)
            lastp = '/{}'.format(lpnr)
        nurl = nurl.replace('+from_albums', '')
        nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

        cm_page = (utils.addon_sys + "?mode=javbangers.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&lp=" + str(lpnr))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + lastp + ')', nurl, 'List', site.img_next, contextm=cm)
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "javbangers.List&url=" + urllib_parse.quote_plus(url))
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
    vp.play_from_direct_link(videourl + '|referer=' + url)


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
        site.add_dir(name, catpage, 'List', img)
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
def JBLogin(logged=True):
    jblogged = utils.addon.getSetting('jblogged')
    if not logged:
        jblogged = False
        utils.addon.setSetting('jblogged', 'false')

    if not jblogged or 'false' in jblogged:
        jbuser = utils.addon.getSetting('jbuser') if utils.addon.getSetting('jbuser') else ''
        jbpass = utils.addon.getSetting('jbpass') if utils.addon.getSetting('jbpass') else ''
        if jbuser == '':
            jbuser = getinput(default=jbuser, heading='Input your Javbangers username')
            jbpass = getinput(default=jbpass, heading='Input your Javbangers password', hidden=True)

        loginurl = '{0}ajax-login/'.format(site.url)
        postRequest = {'action': 'login',
                       'email_link': '{0}email/'.format(site.url),
                       'format': 'json',
                       'mode': 'async',
                       'pass': jbpass,
                       'remember_me': '1',
                       'username': jbuser}
        response = utils._postHtml(loginurl, form_data=postRequest)
        if 'success' in response.lower():
            utils.addon.setSetting('jblogged', 'true')
            utils.addon.setSetting('jbuser', jbuser)
            utils.addon.setSetting('jbpass', jbpass)
            success = True
        else:
            utils.notify('Failure logging in', 'Failure, please check your username or password')
            utils.addon.setSetting('jbuser', '')
            utils.addon.setSetting('jbpass', '')
            success = False
    elif jblogged:
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('jbuser', '')
                utils.addon.setSetting('jbpass', '')
            utils.addon.setSetting('jblogged', 'false')
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
            utils.notify('Favorites', 'Added to JB Favorites')
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify('Favorites', msg)
        return
    if fav == 'del':
        if ('success') in resp:
            utils.notify('Deleted from JB Favorites')
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
        utils.addon.setSetting('jbsortorder', order)
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
    if jblogged and 'kt_member' not in cookiestr:
        JBLogin(False)
    return cookiestr


@site.register()
def Lookupinfo(url):
    class SiteLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if 'members/' in url:
                return site.url + url + '/videos/'
            if any(x in url for x in ['models/', 'tags/', 'categories/']):
                return site.url + url

    lookup_list = [
        ("Cat", '/(categories/[^"]+)">([^<]+)<', ''),
        ("Tag", '/(tags[^"]+)">[^<]+<[^<]+</i>([^<]+)<', ''),
        ("Actor", '/(models/[^"]+)">([^<]+)<', ''),
        ("Uploader", '/(members/[^"]+)">([^<]+)<', ''),
    ]

    lookupinfo = SiteLookup(site.url, url, 'javbangers.List', lookup_list)
    lookupinfo.getinfo()

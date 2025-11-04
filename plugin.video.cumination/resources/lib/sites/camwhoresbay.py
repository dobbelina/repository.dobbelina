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
    soup = utils.parse_html(listhtml)

    seen = set()
    video_items = soup.select('.video-item')
    for item in video_items:
        classes = [cls.lower() for cls in item.get('class', [])]
        is_private = any('private' in cls for cls in classes)
        if is_private and not cblogged:
            continue

        link = item.select_one('a[href]')
        if not link:
            continue
        videopage = utils.safe_get_attr(link, 'href')
        if not videopage:
            continue
        videopage = urllib_parse.urljoin(site.url, videopage)
        if videopage in seen:
            continue
        seen.add(videopage)

        name = utils.safe_get_attr(link, 'title')
        if not name:
            title_tag = item.select_one('.title, .video-title')
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_text(link)
        name = utils.cleantext(name) if name else 'Video'

        hd = ''
        if item.select_one('.hd, .quality-hd, .label-hd, .is-hd, .video-hd'):
            hd = 'HD'
        elif ' HD' in item.get_text(' ', strip=True).upper():
            hd = 'HD'

        prefix = ""
        if is_private:
            prefix = "[COLOR blue] [PV][/COLOR] "
        name = prefix + name

        img_tag = item.select_one('img[data-original], img[data-src], img[data-lazy], img[src]')
        img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'data-lazy', 'src'])
        if img and img.startswith('//'):
            img = 'https:' + img

        duration_tag = item.select_one('.clock, .duration, .time, .video-duration')
        duration = utils.safe_get_text(duration_tag)

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

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu, duration=duration, quality=hd)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a, a.next, a[rel="next"]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                nurl = urllib_parse.urljoin(url, next_href)
                last_link = pagination.select_one('li.last a, a.last')
                lastp = ''
                if last_link:
                    last_href = utils.safe_get_attr(last_link, 'href')
                    if last_href:
                        lm = re.search(r'(\d+)(?:/)?$', last_href.rstrip('/'))
                        if lm:
                            lastp = '/{}'.format(lm.group(1))

                if not page:
                    page = 1
                npage = page + 1

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
    soup = utils.parse_html(cathtml)

    seen = set()
    for item in soup.select('a.item[href], div.item a[href]'):
        catpage = utils.safe_get_attr(item, 'href')
        if not catpage:
            continue
        catpage = urllib_parse.urljoin(site.url, catpage)
        if catpage in seen:
            continue
        seen.add(catpage)

        name = utils.safe_get_attr(item, 'title')
        if not name:
            title_tag = item.select_one('.title, .video-title')
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_text(item)
        name = utils.cleantext(name) if name else 'Category'

        parent = item
        if item.parent and hasattr(item.parent, 'select_one'):
            parent = item.parent

        img_tag = parent.select_one('img[data-original], img[data-src], img[data-lazy], img[src]')
        img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'data-lazy', 'src']) if img_tag else None
        if img and img.startswith('//'):
            img = 'https:' + img

        count_tag = parent.select_one('.videos, .totalplaylist, .count, .video-count, .videos-count')
        count = utils.safe_get_text(count_tag)
        if count:
            name += ' [COLOR cyan][{}][/COLOR]'.format(count)

        site.add_dir(name, catpage, 'List', img, 1)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playlists(url, page=1):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    seen = set()
    for item in soup.select('div.item, li.item, article.item'):
        link = item.select_one('a[href]')
        if not link:
            continue
        catpage = utils.safe_get_attr(link, 'href')
        if not catpage:
            continue
        catpage = urllib_parse.urljoin(site.url, catpage)
        if catpage in seen:
            continue
        seen.add(catpage)

        name = utils.safe_get_attr(link, 'title')
        if not name:
            title_tag = item.select_one('.title, .video-title')
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_text(link)
        name = utils.cleantext(name) if name else 'Playlist'

        img_tag = item.select_one('img[data-original], img[data-src], img[data-lazy], img[src]')
        thumb = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'data-lazy', 'src']) if img_tag else None
        if thumb and thumb.startswith('//'):
            thumb = 'https:' + thumb

        count_tag = item.select_one('.totalplaylist, .videos, .count, .video-count')
        count = utils.safe_get_text(count_tag)
        if count:
            name += ' [COLOR cyan][{}][/COLOR]'.format(count)

        site.add_dir(name, catpage, 'List', thumb, 1)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a, a.next, a[rel="next"]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                nurl = urllib_parse.urljoin(url, next_href)
                last_link = pagination.select_one('li.last a, a.last')
                lastp = ''
                if last_link:
                    last_href = utils.safe_get_attr(last_link, 'href')
                    if last_href:
                        lm = re.search(r'(\d+)(?:/)?$', last_href.rstrip('/'))
                        if lm:
                            lastp = '/{}'.format(lm.group(1))

                if not page:
                    page = 1
                npage = page + 1
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

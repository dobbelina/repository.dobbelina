'''
    Cumination
    Copyright (C) 2023 Cumination

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
from six.moves import urllib_parse
import xbmc
import xbmcgui
from random import randint
from bs4 import BeautifulSoup


site = AdultSite('whoreshub', '[COLOR hotpink]WhoresHub[/COLOR]', 'https://www.whoreshub.com/', 'whoreshub.png', 'whoreshub')

whlogged = 'true' in utils.addon.getSetting('whlogged')
getinput = utils._get_keyboard


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/?mode=async&function=get_block&block_id=list_models_models_list&sort_by=title&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR]', site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by=last_content_date&_=', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    if not whlogged:
        site.add_dir('[COLOR hotpink]Login[/COLOR]', '', 'WHLogin', '', Folder=False)
    else:
        site.add_dir('[COLOR hotpink]Logout[/COLOR]', '', 'WHLogin', '', Folder=False)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    if '?' not in url and ('/categories/' in url or '/models/' in url):
        url = url + '?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&_=' + str(1000000000000 + randint(0, 999999999999))

    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Context menu for video items
    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('whoreshub.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('whoreshub.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    # BeautifulSoup parsing for video items
    if '/playlists/' in url:
        # Playlists view - different HTML structure
        items = soup.select('div.thumb div.box')
        for item in items:
            try:
                link = item.select_one('a')
                if not link:
                    continue

                videourl = utils.safe_get_attr(link, 'href')
                if not videourl:
                    continue

                # Skip category/model/playlist links (only process actual videos)
                if '/categories/' in videourl or '/models/' in videourl or '/playlists/' in videourl:
                    continue

                img_tag = item.select_one('img')
                img = utils.safe_get_attr(img_tag, 'data-src', ['src'])
                name = utils.safe_get_attr(img_tag, 'alt')

                # Fix protocol-relative URLs
                img = 'https:' + img if img.startswith('//') else img

                # No duration or quality in playlist view
                name = utils.cleantext(name)
                site.add_download_link(name, videourl, 'Playvid', img, name, contextm=cm)
            except Exception as e:
                utils.kodilog("Error parsing playlist video item: " + str(e))
                continue
    else:
        # Standard video listing view
        items = soup.select('div.box a.item')
        for item in items:
            try:
                classes = item.get('class') or []
                if 'btn' in classes:
                    continue

                videourl = utils.safe_get_attr(item, 'href')
                if not videourl:
                    continue

                # Skip category/model/playlist links (only process actual videos)
                if '/categories/' in videourl or '/models/' in videourl or '/playlists/' in videourl or '/search/' in videourl:
                    continue

                name = utils.safe_get_attr(item, 'title')

                img_tag = item.select_one('img')
                img = utils.safe_get_attr(img_tag, 'data-src', ['src'])

                # Fix protocol-relative URLs
                img = 'https:' + img if img.startswith('//') else img

                # Duration
                duration_tag = item.select_one('div.duration')
                duration = utils.safe_get_text(duration_tag, '')

                # Quality (HD badge)
                quality_tag = item.select_one('div.is-hd')
                quality = utils.safe_get_text(quality_tag, '')

                # Build display name with quality/duration info
                display_name = utils.cleantext(name)
                if quality:
                    display_name = '[COLOR cyan]' + quality + '[/COLOR] ' + display_name
                if duration:
                    display_name = display_name + ' [COLOR yellow]' + duration + '[/COLOR]'

                site.add_download_link(display_name, videourl, 'Playvid', img, name, contextm=cm)
            except Exception as e:
                utils.kodilog("Error parsing video item: " + str(e))
                continue

    # BeautifulSoup pagination parsing
    pagination = soup.select_one('.pagination')
    if pagination:
        current_page = pagination.select_one('li.current span')
        next_link = pagination.select_one('li.next a')

        if current_page and next_link:
            try:
                npage = int(utils.safe_get_text(current_page, '0')) + 1
                block_id = utils.safe_get_attr(next_link, 'data-block-id')
                params = utils.safe_get_attr(next_link, 'data-parameters', default='')

                if block_id:
                    params = params.replace(';', '&').replace(':', '=')
                    rnd = 1000000000000 + randint(0, 999999999999)
                    nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
                    nurl = nurl.replace('+from_albums', '')
                    nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

                    cm_page = (utils.addon_sys + "?mode=whoreshub.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&listmode=whoreshub.List")
                    cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

                    site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'List', site.img_next, contextm=cm)
            except Exception as e:
                utils.kodilog("Error parsing pagination: " + str(e))

    utils.eod()


@site.register()
def GotoPage(url, np, listmode):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + listmode + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def ListPL(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # BeautifulSoup parsing for playlist videos
    items = soup.select('div.item')
    for item in items:
        try:
            # Video URL from data-item attribute
            video = utils.safe_get_attr(item, 'data-item')
            if not video:
                continue

            # Image from data-original attribute
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'data-original', ['src', 'data-src'])

            # Title from div.title
            title_tag = item.select_one('div.title')
            name = utils.safe_get_text(title_tag, '')

            if name:
                name = utils.cleantext(name)
                site.add_download_link(name, video, 'Playvid', img, name)
        except Exception as e:
            utils.kodilog("Error parsing playlist video: " + str(e))
            continue

    # BeautifulSoup pagination parsing
    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li a[data-parameters*="Next"]')
        if next_link:
            try:
                # Extract page number from the Next link text
                next_text = utils.safe_get_text(next_link, '')
                nextp_match = re.search(r':(\d+)', next_text)
                if nextp_match:
                    np = nextp_match.group(1)
                    pg = int(np) - 1

                    if 'from={0:02d}'.format(pg) in url:
                        next_page = url.replace('from={0:02d}'.format(pg), 'from={0:02d}'.format(int(np)))
                    else:
                        next_page = url + '{0}/'.format(np)

                    # Check for last page number
                    last_link = pagination.select_one('li a[data-parameters*="Last"]')
                    if last_link:
                        last_text = utils.safe_get_text(last_link, '')
                        last_match = re.search(r':(\d+)', last_text)
                        lp = '/' + last_match.group(1) if last_match else ''
                    else:
                        lp = ''

                    site.add_dir('Next Page (' + np + lp + ')', next_page, 'ListPL', site.img_next)
            except Exception as e:
                utils.kodilog("Error parsing playlist pagination: " + str(e))

    utils.eod()


@site.register()
def Playlist(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # BeautifulSoup parsing for playlists
    items = soup.select('div.item')
    for item in items:
        try:
            # Playlist link
            link = item.select_one('a')
            if not link:
                continue

            lpage = utils.safe_get_attr(link, 'href')
            if not lpage:
                continue

            # Image
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'data-original', ['src', 'data-src'])

            # Title
            title_tag = item.select_one('div.title')
            name = utils.safe_get_text(title_tag, '')

            # Video count
            count_tag = item.select_one('div.videos')
            count = utils.safe_get_text(count_tag, '0')

            if name:
                name = utils.cleantext(name) + "[COLOR deeppink] {0}[/COLOR]".format(count)
                lpage += '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=&from=01'
                site.add_dir(name, lpage, 'ListPL', img)
        except Exception as e:
            utils.kodilog("Error parsing playlist item: " + str(e))
            continue

    # BeautifulSoup pagination parsing
    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li a[data-parameters*="Next"]')
        if next_link:
            try:
                # Extract page number from the Next link text
                next_text = utils.safe_get_text(next_link, '')
                nextp_match = re.search(r':(\d+)', next_text)
                if nextp_match:
                    np = nextp_match.group(1)
                    pg = int(np) - 1

                    if 'from={0:02d}'.format(pg) in url:
                        next_page = url.replace('from={0:02d}'.format(pg), 'from={0:02d}'.format(int(np)))
                    else:
                        next_page = url + '{0}/'.format(np)

                    # Check for last page number
                    last_link = pagination.select_one('li a[data-parameters*="Last"]')
                    if last_link:
                        last_text = utils.safe_get_text(last_link, '')
                        last_match = re.search(r':(\d+)', last_text)
                        lp = '/' + last_match.group(1) if last_match else ''
                    else:
                        lp = ''

                    site.add_dir('Next Page (' + np + lp + ')', next_page, 'Playlist', site.img_next)
            except Exception as e:
                utils.kodilog("Error parsing playlist pagination: " + str(e))

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = '{}{}/'.format(searchUrl, keyword.replace(' ', '-'))
        List(searchUrl)


@site.register()
def Categories(url):
    url = url + str(1000000000000 + randint(0, 999999999999))
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # BeautifulSoup parsing for categories/models/playlists
    if '/playlists/' in url:
        # Playlists view - different HTML structure
        items = soup.select('div.box')
        for item in items:
            try:
                link = item.select_one('a')
                if not link:
                    continue

                catpage = utils.safe_get_attr(link, 'href')
                if not catpage:
                    continue

                name = utils.safe_get_attr(link, 'title')

                img_tag = item.select_one('img')
                img = utils.safe_get_attr(img_tag, 'data-src', ['src'])

                # Video count - in span.val span.text
                count_tag = item.select_one('span.val span.text')
                videos = utils.safe_get_text(count_tag, '0')

                # Clean name (models/playlists don't show count in name)
                name = utils.cleantext(name)

                # Fix protocol-relative URLs
                img = 'https:' + img if img.startswith('//') else img

                site.add_dir(name, catpage, 'List', img)
            except Exception as e:
                utils.kodilog("Error parsing playlist category item: " + str(e))
                continue
    else:
        # Categories or Models view
        items = soup.select('a.item')
        for item in items:
            try:
                catpage = utils.safe_get_attr(item, 'href')
                if not catpage:
                    continue

                name = utils.safe_get_attr(item, 'title')

                img_tag = item.select_one('img')
                img = utils.safe_get_attr(img_tag, 'src', ['data-src'])

                # Video count - in span.val span.text
                count_tag = item.select_one('span.val span.text')
                videos = utils.safe_get_text(count_tag, '0')

                # Build display name
                name = utils.cleantext(name)
                if '/models/' in url or '/playlists/' in url:
                    # Models and playlists don't show count
                    pass
                else:
                    # Categories show count
                    name = name + " [COLOR deeppink]" + videos + "[/COLOR]"

                # Fix protocol-relative URLs
                img = 'https:' + img if img.startswith('//') else img

                site.add_dir(name, catpage, 'List', img)
            except Exception as e:
                utils.kodilog("Error parsing category item: " + str(e))
                continue

    # BeautifulSoup pagination parsing
    pagination = soup.select_one('.pagination')
    if pagination:
        current_page = pagination.select_one('li.current span')
        next_link = pagination.select_one('li.next a')

        if current_page and next_link:
            try:
                npage = int(utils.safe_get_text(current_page, '0')) + 1
                block_id = utils.safe_get_attr(next_link, 'data-block-id')
                params = utils.safe_get_attr(next_link, 'data-parameters', default='')

                if block_id:
                    params = params.replace(';', '&').replace(':', '=')
                    rnd = 1000000000000 + randint(0, 999999999999)
                    nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))
                    nurl = nurl.replace('+from_albums', '')
                    nurl = re.sub(r'&from([^=]*)=\d+', r'&from\1={}'.format(npage), nurl)

                    cm_page = (utils.addon_sys + "?mode=whoreshub.GotoPage" + "&url=" + urllib_parse.quote_plus(nurl) + "&np=" + str(npage) + "&listmode=whoreshub.Categories")
                    cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

                    site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + str(npage) + ')', nurl, 'Categories', site.img_next, contextm=cm)
            except Exception as e:
                utils.kodilog("Error parsing category pagination: " + str(e))

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    videohtml = utils.getHtml(url, site.url, headers=hdr)

    match = re.compile(r"video(?:_|_alt_)url\d*: '([^']+)'.+?video(?:_|_alt_)url\d*_text: '([^']+)'", re.DOTALL | re.IGNORECASE).findall(videohtml)

    sources = {}
    if match:
        for video in match:
            if 'login' in video[0].lower():
                continue
            sources[video[1]] = video[0]

    utils.kodilog("whoreshub sources found: " + str(sources))
    vp.progress.update(75, "[CR]Video found[CR]")

    if sources:
        # Custom sort function that handles various quality text formats
        def quality_sort(quality_text):
            try:
                # Extract numeric value from quality text (e.g., "1080p" -> 1080, "720 p" -> 720)
                import re
                match = re.search(r'(\d+)', quality_text)
                if match:
                    return int(match.group(1))
                return 0
            except:
                return 0

        videourl = utils.prefquality(sources, sort_by=quality_sort, reverse=True)
        if videourl:
            videourl = videourl + '|Cookie=' + get_cookies()
            vp.play_from_direct_link(videourl)
    else:
        utils.kodilog("No video sources found for whoreshub")


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Category", r'(categories/[^"]+)"\sclass="btn">([^<]+)<', ''),
        ("Tag", r'(tags/[^"]+)"\sclass="btn">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'whoreshub.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('whoreshub.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def WHLogin(logged=True):
    whlogged = utils.addon.getSetting('whlogged')
    if not logged:
        whlogged = False
        utils.addon.setSetting('whlogged', 'false')

    if not whlogged or 'false' in whlogged:
        whuser = utils.addon.getSetting('whuser') or ''
        whpass = utils.addon.getSetting('whpass') or ''
        if whuser == '':
            whuser = getinput(default=whuser, heading='Input your Whorehub username')
            whpass = getinput(default=whpass, heading='Input your Whorehub password', hidden=True)

        loginurl = '{0}login/'.format(site.url)
        postRequest = {'action': 'login',
                       'email_link': '{0}email/'.format(site.url),
                       'format': 'json',
                       'mode': 'async',
                       'pass': whpass,
                       'remember_me': '1',
                       'username': whuser}
        response = utils._postHtml(loginurl, form_data=postRequest)
        if 'success' in response.lower():
            utils.addon.setSetting('whlogged', 'true')
            utils.addon.setSetting('whuser', whuser)
            utils.addon.setSetting('whpass', whpass)
            success = True
        else:
            utils.notify('Failure logging in', 'Failure, please check your username or password')
            utils.addon.setSetting('whuser', '')
            utils.addon.setSetting('whpass', '')
            success = False
    else:
        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear:
            if clear == 'Yes':
                utils.addon.setSetting('whuser', '')
                utils.addon.setSetting('whpass', '')
            utils.addon.setSetting('whlogged', 'false')
            utils._getHtml(site.url + 'logout/')
            contexturl = (utils.addon_sys + "?mode=whoreshub.Main")
            xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    if logged:
        xbmc.executebuiltin('Container.Refresh')
    else:
        return success


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
    if whlogged and 'kt_member' not in cookiestr:
        WHLogin(False)
    return cookiestr

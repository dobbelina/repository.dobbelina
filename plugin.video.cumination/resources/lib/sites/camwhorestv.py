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
from urllib.parse import quote
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('camwhorestv', '[COLOR hotpink]CamWhores.tv[/COLOR]', 'https://www.camwhores.tv/', 'camwhorestv.jpg', 'camwhorestv')

camwhores_logged = 'true' in utils.addon.getSetting('camwhores_logged')
cwtvhdr = utils.base_hdrs.copy()
cwtvhdr['User-Agent'] = 'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_models)
    if camwhores_logged:
        site.add_dir('[COLOR fuchsia]Logout[/COLOR]', '', 'logout_camwhores', site.img_logout, Folder=False)
    else:
        site.add_dir('[COLOR red]Login[/COLOR]', '', 'login_camwhores', site.img_login, Folder=False)

    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/1/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url, headers=cwtvhdr)

    # Extraction des blocs d'items
    items = re.findall(
        r'<div class="item[^"]*".*?</div>',
        listhtml,
        re.DOTALL | re.IGNORECASE
    )

    # Extraction des données vidéo
    match = re.compile(
        r'<div class="item[^"]*".+?href="([^"]+)".+?'          # link
        r'title="([^"]+)".+?'                                  # title
        r'data-original="([^"]+)".+?'                          # thumbnail
        r'duration">([^<]+)<.+?'                               # duration
        r'views">([^<]+)<',                                    # views
        re.DOTALL | re.IGNORECASE
    ).findall(listhtml)

    results = []
    for block, (videopage, name, img, duration, views) in zip(items, match):
        is_private = 'class="ico-private"' in block
        results.append({
            "href": videopage,
            "title": name,
            "img": img,
            "duration": duration,
            "views": views,
            "private": is_private
        })

    for item in results:
        videopage = item["href"]
        name = utils.cleantext(item["title"])
        img = item["img"]
        utils.kodilog(img)
        duration = item["duration"]
        views = item["views"]
        private = item["private"]

        label = "[COLOR blue][PV] [/COLOR]" if private else ""
        label += f"{name}"  # [COLOR yellow][{views} views][/COLOR]"

        parts = img.rstrip("/").split("/")
        img_preview = "/".join(parts[:-2]) + "/preview.jpg"

        site.add_download_link(
            label,
            videopage,
            "Playvid",
            img_preview,
            label,
            duration=duration
        )

    # Pagination avec gestion d'erreurs
    try:
        if '/search/' in url or '/categories/' in url or '/models/' in url:
            # Pagination async pour search/categories/models
            np_match = re.search(
                r'<li class="next">.*?(?:from_albums|from):(\d+)">Next',
                listhtml, re.DOTALL | re.IGNORECASE
            )

            lp_match = re.search(
                r'<li class="last">.*?(?:from_albums|from):(\d+)">Last',
                listhtml, re.DOTALL | re.IGNORECASE
            )

            if np_match:
                re_npnr = np_match.group(1)
                re_lpnr = lp_match.group(1) if lp_match else "?"

                # Extraction des paramètres pour l'URL async
                np = re.search(
                    r'>\.\.\.<.*?data-parameters="([^"]+):([^:]+)">.*?(?:from_albums|from):(\d+)">.*Next',
                    listhtml, re.DOTALL | re.IGNORECASE
                )

                if np:
                    npurl = np.group(1).replace(':', '=').replace(';', '&').replace('+', '={}&'.format(re_npnr))

                    if '/search/' in url:
                        block = '&block_id=list_videos_videos_list_search_result&'
                    else:
                        block = '&block_id=list_videos_common_videos_list&'

                    base_url = url.split('?')[0] if '?' in url else url
                    re_npurl = base_url + '?mode=async&function=get_block' + block + npurl + '=' + re_npnr

                    site.add_dir('Next Page... ({0}/{1})'.format(re_npnr, re_lpnr), re_npurl, 'List', site.img_next)
        else:
            # Pagination standard pour les autres pages
            re_npurl = r'class="next"><a href="([^"]+)"'
            re_npnr = r'class="next"><a href="[^"]*/(\d+)/"'
            re_lpnr = r'class="last"><a href="[^"]*/(\d+)/"'
            utils.next_page(site, 'camwhorestv.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr)

    except Exception as e:
        utils.kodilog("Pagination error: {0}".format(str(e)))

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        # Encodage URL propre pour éviter les problèmes avec caractères spéciaux
        keyword_clean = keyword.strip().replace(' ', '-')
        keyword_encoded = quote(keyword_clean, safe='-')
        search_url = url + keyword_encoded + '/'
        List(search_url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, headers=cwtvhdr)
    if 'class="message"' in html:
        message = re.search(r'span class="message">\s*(.+?)\s+Only', html, re.IGNORECASE)
        if message:
            utils.notify('', message.group(1).strip())
        return
    vp.play_from_kt_player(html, user_agent=cwtvhdr['User-Agent'])


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url, headers=cwtvhdr)
    match = re.compile(
        r'<a\s+class="item"\s+href="([^"]+)"\s+title="([^"]+)".+?'
        r'<img[^>]+src="([^"]+)".+?'
        r'<div class="videos">([^<]+)<',
        re.DOTALL | re.IGNORECASE
    ).findall(listhtml)

    for cat_url, cat_title, cat_img, cat_count in match:
        site.add_dir('[COLOR hotpink]' + cat_title + ' [/COLOR][COLOR yellow][{}][/COLOR]'.format(cat_count), cat_url, 'List', cat_img)

    # Pagination pour catégories
    try:
        re_npurl = r'class="next"><a href="([^"]+)"'
        re_npnr = r'class="next"><a href="[^"]*/(\d+)/"'
        re_lpnr = r'class="last"><a href="[^"]*/(\d+)/"'
        utils.next_page(site, 'camwhorestv.Categories', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='camwhorestv.GotoPage')
    except:
        pass

    utils.eod()


@site.register()
def Models(url):
    listhtml = utils.getHtml(url, headers=cwtvhdr)
    match = re.compile(
        r'a class="item.+?href="([^"]+)".+?title="([^"]+)".+?src="([^"]+)".+?videos">([^>]+)<',
        re.DOTALL | re.IGNORECASE
    ).findall(listhtml)

    for cat_url, cat_title, cat_img, cat_count in match:
        site.add_dir(cat_title + ' [COLOR yellow][{}][/COLOR]'.format(cat_count), cat_url, 'List', cat_img)

    # Pagination pour modèles
    try:
        re_npurl = r'class="next"><a href="([^"]+)"'
        re_npnr = r'class="next"><a href="[^"]*/(\d+)/"'
        re_lpnr = r'class="last"><a href="[^"]*/(\d+)/"'
        utils.next_page(site, 'camwhorestv.Models', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='camwhorestv.GotoPage')
    except:
        pass

    utils.eod()


def get_camwhores_session():
    domain = ".camwhores.tv"
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'PHPSESSID':
            return cookie.value
    return ""


@site.register()
def login_camwhores():
    import json
    global camwhores_logged

    sessionid = utils.addon.getSetting('camwhores_sessionid')
    if sessionid:
        current = get_camwhores_session()
        if sessionid == current:
            utils.addon.setSetting('camwhores_logged', 'true')
            camwhores_logged = True
            return True

        if sessionid and sessionid != current:
            cookie_structure = {
                'solution': {
                    "cookies": [{
                        'name': "PHPSESSID",
                        'domain': ".www.camwhores.tv",
                        'value': sessionid,
                        'path': '/',
                        'secure': True,
                        'expiry': None,
                        'httpOnly': True
                    }],
                    "userAgent": cwtvhdr['User-Agent']
                }
            }
            utils.savecookies(cookie_structure)
            utils.addon.setSetting('camwhores_logged', 'true')
            camwhores_logged = True
            utils.refresh()
            return True

    cw_user = utils.addon.getSetting('camwhores_user') or ''
    cw_pass = utils.addon.getSetting('camwhores_pass') or ''

    if not cw_user:
        cw_user = utils._get_keyboard(default=cw_user, heading='Input your CamWhores username')
        if not cw_user:
            return False

        cw_pass = utils._get_keyboard(default=cw_pass, heading='Input your CamWhores password', hidden=True)
        if not cw_pass:
            return False

    login_url = '{}login/'.format(site.url)

    payload_dict = {
        "username": cw_user,
        "pass": cw_pass,
        "remember_me": "1",
        "action": "login",
        "email_link": "{}email/".format(site.url),
        "format": "json",
        "mode": "async"
    }

    headers = {
        "Accept": "*/*",
        "Origin": site.url[:-1],
        "Referer": site.url,
        "User-Agent": cwtvhdr['User-Agent'],
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        response_html = utils._postHtml(login_url, form_data=payload_dict, headers=headers)
        response_json = json.loads(response_html)
        status = response_json.get('status', '')
        if status != 'success':
            utils.notify('CamWhores', 'Login failed')
            utils.addon.setSetting('camwhores_logged', 'false')
            camwhores_logged = False
            return False

        display_name = response_json.get('username') or cw_user
        utils.addon.setSetting('camwhores_display_name', display_name)

        new_session_id = get_camwhores_session()
        if new_session_id:
            utils.notify('CamWhores', u'Login successful for {}'.format(display_name))
            utils.addon.setSetting('camwhores_sessionid', new_session_id)
            utils.addon.setSetting('camwhores_logged', 'true')
            utils.addon.setSetting('camwhores_user', cw_user)
            utils.addon.setSetting('camwhores_pass', cw_pass)

            camwhores_logged = True

            cookie_structure = {
                'solution': {
                    "cookies": [{
                        'name': "PHPSESSID",
                        'domain': ".www.camwhores.tv",
                        'value': new_session_id,
                        'path': '/',
                        'secure': True,
                        'expiry': None,
                        'httpOnly': True
                    }],
                    "userAgent": cwtvhdr['User-Agent']
                }
            }
            utils.savecookies(cookie_structure)
            utils.refresh()
            return True

    except Exception as e:
        utils.kodilog("Error on utils._postHtml for Login CamWhores: {e}".format(e=e))
        utils.notify('CamWhores', 'Authentication error')

    utils.addon.setSetting('camwhores_logged', 'false')
    camwhores_logged = False
    return False


@site.register()
def logout_camwhores():
    logout_url = '{}logout/'.format(site.url)

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": site.url,
        "User-Agent": cwtvhdr['User-Agent']
    }

    try:
        utils.getHtml(logout_url, headers=headers)
        utils.notify('CamWhores', u'Session ended successfully.')

        clear = utils.selector('Clear stored user & password?', ['Yes', 'No'], reverse=True)
        if clear == 'Yes':
            utils.addon.setSetting('camwhores_user', '')
            utils.addon.setSetting('camwhores_pass', '')

        utils.addon.setSetting('camwhores_sessionid', '')
        utils.addon.setSetting('camwhores_logged', 'false')

        global camwhores_logged
        camwhores_logged = False

        utils.refresh()
        return True

    except Exception as e:
        utils.kodilog("Error on utils.getHtml for Logout CamWhores: {e}".format(e=e))
        return False

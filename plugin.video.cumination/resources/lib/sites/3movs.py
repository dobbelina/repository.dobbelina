'''
    Cumination
    Copyright (C) 2026 Team Cumination

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
import html as html_module

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('3movs', '[COLOR hotpink]3Movs[/COLOR]', 'https://www.3movs.com/', '3movs.png', '3movs')

# Headers personnalisés
movs_headers = utils.base_hdrs.copy()
movs_headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.3movs.com/',
})


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search_videos/?q=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'most-viewed/all-time/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/all-time/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Longest[/COLOR]', site.url + 'longest/', 'List', site.img_cat)
    # Vidéos récentes directement à la racine
    List(site.url + 'videos/')
    utils.eod()


@site.register()
def List(url, page=1):
    # Gérer le cas où page est None ou une chaîne
    if page is None:
        page = 1
    else:
        try:
            page = int(page)
        except:
            page = 1

    # Gestion de la pagination
    current_url = url
    if page > 1:
        if '/search_videos/' in url and '?' in url:
            base, query_str = url.split('?', 1)
            current_url = f"{base.rstrip('/')}/{page}/?{query_str}"
        else:
            current_url = f"{url.rstrip('/')}/{page}/"

    try:
        html = utils.getHtml(current_url, site.url, headers=movs_headers)
    except:
        utils.notify('Error', 'Failed to load page')
        utils.eod()
        return

    if not html:
        utils.notify('Error', 'No content found')
        utils.eod()
        return

    # Extraction des vidéos - pattern 3movs
    blocks = re.split(r'<div[^>]+class=["\'][^"\']*item thumb', html)[1:]

    for block in blocks:
        v_url_match = re.search(r'href=["\'](https?://www\.3movs\.com/videos/[^"\']+)["\']', block)
        v_title_match = re.search(r'title=["\']([^"\']+)["\']', block)
        v_thumb_match = re.search(r'data-src=["\']([^"\']+)["\']', block)
        v_duration_match = re.search(r'<div[^>]+time[^>]*>([^<]+)</div>', block)

        if v_url_match and v_title_match:
            v_url = v_url_match.group(1)
            v_title = html_module.unescape(v_title_match.group(1))
            v_thumb = v_thumb_match.group(1) if v_thumb_match else site.img_cat
            v_duration = v_duration_match.group(1).strip() if v_duration_match else ""

            # # Ajouter la durée au titre
            # name = v_title
            # if v_duration:
            #     name += ' [COLOR hotpink][' + v_duration + '][/COLOR]'

            site.add_download_link(v_title, v_url, 'Playvid', v_thumb, v_title, duration=v_duration)

    # Pagination
    if 'Next' in html or 'icon-arrow-right' in html:
        site.add_dir('[COLOR hotpink]Next Page >>[/COLOR]', url, 'List', site.img_next, page=page + 1)

    utils.eod()


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, site.url, headers=movs_headers)
    except:
        utils.notify('Error', 'Failed to load categories')
        utils.eod()
        return

    # Pattern pour les catégories 3movs
    cat_pattern = r'<div[^>]+thumb_cat item[^>]*>.*?<a[^>]+href=["\'](https?://www\.3movs\.com/categories/[^"\']+)["\'][^>]+title=["\']([^"\']+)["\'].*?data-src=["\']([^"\']+)["\'].*?<div[^>]+title[^>]*>(.*?)</div>'
    cats = re.findall(cat_pattern, cathtml, re.DOTALL)

    for c_url, c_title, c_thumb, c_inner_html in cats:
        count_match = re.search(r'<span>([^<]+)</span>', c_inner_html)
        count = count_match.group(1) if count_match else ""
        display_title = f"{html_module.unescape(c_title)} [COLOR hotpink]({count})[/COLOR]"
        site.add_dir(display_title, c_url, 'List', c_thumb)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        search_url = site.url + 'search_videos/?q=' + keyword.replace(' ', '+')
        List(search_url, 1)  # Ajoute juste le paramètre page ici


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        page_html = utils.getHtml(url, site.url, headers=movs_headers)
    except:
        vp.progress.close()
        utils.notify('Error', 'Failed to load video page')
        return

    # Extraction du flux vidéo - pattern KVS flashvars
    player_config = re.search(r'var\s+flashvars\s*=\s*({.*?});', page_html, re.DOTALL)
    stream_url = None

    if player_config:
        config_json = player_config.group(1)
        # Chercher video_url (HQ) et video_alt_url (LQ)
        hq_match = re.search(r'video_url:\s*[\'"](.*?)[\'"]', config_json)
        lq_match = re.search(r'video_alt_url:\s*[\'"](.*?)[\'"]', config_json)

        hq_url = hq_match.group(1) if hq_match else None
        lq_url = lq_match.group(1) if lq_match else None

        # Préférer la qualité HQ
        stream_url = hq_url or lq_url

    if stream_url:
        # Ajouter headers pour la lecture
        stream_url += '|User-Agent={0}&Referer={1}'.format(
            utils.USER_AGENT,
            site.url
        )
        vp.play_from_direct_link(stream_url)
        vp.progress.close()
    else:
        vp.progress.close()
        utils.notify('Error', 'Could not extract video URL')

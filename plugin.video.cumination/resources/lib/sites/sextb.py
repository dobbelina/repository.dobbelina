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
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('sextb', '[COLOR hotpink]SexTB[/COLOR]', 'https://sextb.net/', 'sextb.png', 'sextb')
enames = {
    'VV': 'VideoVard',
    'TV': 'TurboVIPlay',
    'TB': 'TurboVIPlay',
    'JP': 'JAVPoll',
    'ST': 'StreamTape',
    'DD': 'DoodStream',
    'VS': 'Voe',
    'SW': 'StreamWish',
    'NJ': 'NinjaStream',
    'NT': 'Netu',
    'FL': 'FileLions',
    'US': 'UPN',
    'VG': 'Vidguard'
}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Amateur[/COLOR]', site.url + 'amateur/pg-1', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Censored[/COLOR]', site.url + 'censored/pg-1', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Uncensored Leaked[/COLOR]', site.url + 'genre/uncensored-leaked/pg-1', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Reducing Mosaic[/COLOR]', site.url + 'genre/reducing-mosaic/pg-1', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Subtitle[/COLOR]', site.url + 'subtitle/pg-1', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Genres[/COLOR]', site.url + 'genres', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Actress[/COLOR]', site.url + 'list-actress/pg-1', 'Actress', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'list-studios', 'Studios', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'uncensored/pg-1')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)

    if 'No Video were found that matched your search query' in html or len(html) < 10:
        utils.eod()
        return
    match = re.compile(r'<div class="tray-item(?:\s*tray|").+?href="([^"]+)".+?data-src="([^"]+).+?title">([^<]+).+?time">([^<]+)', re.DOTALL | re.IGNORECASE).findall(html)

    thumbnails = utils.Thumbnails(site.name)
    for videopage, img, name, duration in match:
        img = thumbnails.cache_img(img)
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    nextp = re.compile(r'''href=["']([^'"]+)["']>Next''', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        np = nextp.group(1)
        if np.startswith('/'):
            np = urllib_parse.urljoin(site.url, np)
        pgtxt = re.compile(r'''class=['"]current['"]\s*id[^>]+>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(html)[0]
        site.add_dir('Next Page... (Currently in Page {0})'.format(pgtxt), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="fas fa-folder".+?href="([^"]+)"\s*title="([^"]+)".+?>\((\d+)\)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink](' + str(count) + ')[/COLOR]'
        name = name.replace('Genre ', '').replace('Studio ', '')
        if caturl.startswith('/'):
            caturl = urllib_parse.urljoin(site.url, caturl)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Studios(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'<div class="tray-item\s*tray.+?href="([^"]+).+?/i>\s*([^<]+).+?total">([^<]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, name, count in match:
        name = utils.cleantext(name) + ' [COLOR hotpink]' + count + '[/COLOR]'
        if caturl.startswith('/'):
            caturl = urllib_parse.urljoin(site.url, caturl)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Actress(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="tray-item-actress".+?href="([^"]+)".+?data-src="([^"]+)".+?actress-title">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    thumbnails = utils.Thumbnails(site.name)
    for caturl, img, name in match:
        img = thumbnails.cache_img(img)
        name = utils.cleantext(name)
        if caturl.startswith('/'):
            caturl = urllib_parse.urljoin(site.url, caturl)
        site.add_dir(name, caturl, 'List', img)
    nextp = re.compile(r'''href=["']([^'"]+)["']>Next''', re.DOTALL | re.IGNORECASE).search(cathtml)
    if nextp:
        np = nextp.group(1)
        if np.startswith('/'):
            np = urllib_parse.urljoin(site.url, np)
        pgtxt = re.compile(r'''class=['"]current['"]\s*id[^>]+>([^<]+)''', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        site.add_dir('Next Page... (Currently in Page {0})'.format(pgtxt), np, 'Actress', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '-'))
        List(url)


def xor_decrypt(encoded, key):
    import base64
    decoded = base64.b64decode(encoded)
    key_bytes = key.encode('utf-8')
    key_len = len(key_bytes)
    return "".join(chr(decoded[i] ^ key_bytes[i % key_len]) for i in range(len(decoded)))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    if url.startswith('/'):
        url = urllib_parse.urljoin(site.url, url)
    video_page = utils.getHtml(url, site.url)
    videourl = ''
    ajaxurl = 'https://sextb.net/ajax/player'
    embeds = re.compile(r'class="btn-player.+?data-source="([^"]+).+?data-id="([^"]+).+?/i>\s*([^<]+)', re.DOTALL | re.IGNORECASE).findall(video_page)
    sources = {}
    for vid, embed, hoster in embeds:
        if 'VIP' not in hoster:
            option = ''
            if '#' in hoster:
                hoster, option = hoster.split(' ')
            sources.update({(enames[hoster.strip()] + option) if hoster.strip() in enames.keys() else (hoster + option): vid + '$$' + embed})
    source = utils.selector('Select Hoster', sources)
    if source:
        filmid, episode = source.split('$$')

        match = re.compile(r'window.__pt = "([^"]+)";\s+window.__pk = "([^"]+)";', re.DOTALL | re.IGNORECASE).search(video_page)
        if match:
            pt, pk = match.groups()

            form_data = {'filmId': filmid, 'episode': episode, 'pt': pt}

            player_html = utils._postHtml(ajaxurl, form_data=form_data, headers={'Referer': url, 'X-Requested-With': 'XMLHttpRequest'})
            data = json.loads(player_html)
            player_enc = data.get('player_enc')

            decrypted_html = xor_decrypt(player_enc, pk)
            iframe_match = re.search(r'src="([^"]+)"', decrypted_html)

            if iframe_match:
                iframe_url = iframe_match.group(1)
                if iframe_url.startswith('//'):
                    iframe_url = 'https:' + iframe_url

                vp.progress.update(75, "[CR]Resolving video...[/CR]")

                videourl = iframe_url + '$$' + url
                vp.play_from_link_to_resolve(videourl)

    if not videourl:
        vp.progress.close()
        return

    vp.play_from_link_to_resolve(videourl)

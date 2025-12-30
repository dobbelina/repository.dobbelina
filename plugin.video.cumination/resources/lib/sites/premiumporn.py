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
import xbmcgui
from resources.lib import utils
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite
import json
import base64
try:
    from Cryptodome.Cipher import AES
except Exception as error:
    utils.kodilog('Import Error Cryptodome: {}'.format(error))

site = AdultSite('premiumporn', '[COLOR hotpink]PremiumPorn[/COLOR]', 'https://premiumporn.org/', 'premiumporn.png', 'premiumporn')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Actors[/COLOR]', site.url + 'actors/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'studios/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'page/1?filter=latest')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if 'It looks like nothing was found for this search' in listhtml:
        utils.notify('No results found', 'Try a different search term')
        return

    delimiter = 'data-post-id="'
    re_videopage = 'href="([^"]+)"'
    re_name = '"title">([^<]+)<'
    re_img = 'data-src="([^"]+)"'
    re_duration = 'duration">([^<]+)<'

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=premiumporn.Lookupinfo&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=premiumporn.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'premiumporn.Play', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, contextm=cm)

    re_npurl = r'class="next page-link" href="([^"]+)"'
    re_npnr = r'class="next page-link".+?/page/(\d+)/'
    re_lpnr = r'>(\d+)</a>\s*</li>\s*<li class="page-item ">\s*<a class="next'

    utils.next_page(site, 'premiumporn.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='premiumporn.GotoPage')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    match = re.compile(r'class="thumb" href="([^"]+)" title="([^"]+)">.+?data-src="([^"]+)".+?class="video-datas">\s*(\d+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for siteurl, name, img, videos in match:
        name = utils.cleantext(name) + '[COLOR hotpink] (' + videos + ' videos)[/COLOR]'
        site.add_dir(name, siteurl, 'List', img)
    match = re.search(r'class="next page-link" href="([^"]+)"', cathtml, re.IGNORECASE | re.DOTALL)
    if match:
        site.add_dir('Next Page', match.group(1), 'Categories', site.img_next)
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}/'.format(np), '/page/{}/'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)


def base64_url_decode(data):
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    data = data.replace('-', '+').replace('_', '/')
    return base64.b64decode(data)


def decrypt_aes_gcm(payload, key, iv):
    try:
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        plaintext = cipher.decrypt_and_verify(payload[:-16], payload[-16:])
        return plaintext.decode('utf-8')
    except Exception as e:
        return "Decryption failed: {}".format(str(e))


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url)
    match = re.compile(r'itemprop="embedURL" content="(https://[^/]+/e/([^/]+)/[^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if match:
        embed_url = match[0][0]
        id = match[0][1]
        details_url = 'https://bysewihe.com/api/videos/{}/embed/details'.format(id)
        details_data = utils.getHtml(details_url, url)
        details_json = json.loads(details_data)
        embed = details_json.get('embed_frame_url', '')

        api_url = 'https://g9r6.com/api/videos/{}/embed/playback'.format(id)
        hdr = utils.base_hdrs.copy()
        hdr['X-Embed-Origin'] = 'premiumporn.org'
        hdr['X-Embed-Parent'] = embed_url
        hdr['X-Embed-Referer'] = site.url

        api_data = utils.getHtml(api_url, embed, headers=hdr)
        encrypted_data = json.loads(api_data)

        playback = encrypted_data["playback"]

        iv = base64_url_decode(playback["iv"])
        payload = base64_url_decode(playback["payload"])

        key_part1 = base64_url_decode(playback["key_parts"][0])
        key_part2 = base64_url_decode(playback["key_parts"][1])
        combined_key = key_part1 + key_part2

        result = decrypt_aes_gcm(payload, combined_key, iv)
        src = {}
        for source in json.loads(result).get('sources', []):
            video_url = source.get('url', '').replace('\\u0026', '&')
            label = source.get('label', '')
            src[label] = video_url

        video_url = utils.prefquality(src, sort_by=lambda x: 2160 if x == '4k' else int(x[:-1]), reverse=True)
        if video_url:
            vp.play_from_direct_link(video_url)

    else:
        utils.notify('Oh oh', 'No video found')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('premiumporn.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actors", r'<a href="(https://premiumporn.org/actor/[^"]+)" title="([^"]+)">', ''),
        ("Studios", r'<a href="(https://premiumporn.org/[^/]+/)" title="([^"]+)">', ''),
    ]
    lookupinfo = utils.LookupInfo('', url, 'premiumporn.List', lookup_list)
    lookupinfo.getinfo()

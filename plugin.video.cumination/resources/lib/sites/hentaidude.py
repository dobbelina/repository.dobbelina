"""
    Cumination
    Copyright (C) 2020 Whitecream

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import base64
import json
import xbmc


site = AdultSite("hentaidude", "[COLOR hotpink]Hentaidude[/COLOR]", 'https://hentaidude.xxx/', "https://hentaidude.xxx/wp-content/uploads/2021/03/Hentai-Dude.png", "hentaidude")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Uncensored[/COLOR]', site.url + 'genre/uncensored-hentai/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]3D[/COLOR]', site.url + 'genre/3d-hentai/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Anal[/COLOR]', site.url + 'genre/anal/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]BBw[/COLOR]', site.url + 'genre/bbw/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]BDSM[/COLOR]', site.url + 'genre/bdsm/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Femdom[/COLOR]', site.url + 'genre/femdom/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Furry[/COLOR]', site.url + 'genre/furry/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Futanari[/COLOR]', site.url + 'genre/gender-bender-heantai/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Harem[/COLOR]', site.url + 'genre/harem/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Horror[/COLOR]', site.url + 'genre/horror/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Incest[/COLOR]', site.url + 'genre/incest-hentai/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]MILF[/COLOR]', site.url + 'genre/milf/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Monster[/COLOR]', site.url + 'genre/monster/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Romance[/COLOR]', site.url + 'genre/romance/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]School[/COLOR]', site.url + 'genre/hentai-school/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Shota[/COLOR]', site.url + 'genre/shota/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Shotacon[/COLOR]', site.url + 'genre/shotocon/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Softcore[/COLOR]', site.url + 'genre/softcore/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Tentacle[/COLOR]', site.url + 'genre/tentacle/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Tsundere[/COLOR]', site.url + 'genre/tsundere/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Teen[/COLOR]', site.url + 'genre/teen-hentai/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Young[/COLOR]', site.url + 'genre/young-hentai/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Yuri[/COLOR]', site.url + 'genre/yuri/page/1/?m_orderby=latest', 'List', site.img_cat, 1)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'page/1/?s=', 'Search', site.img_search)
    List(site.url + 'page/1/?m_orderby=latest')


@site.register()
def List(url, page=1):
    listhtml = utils.getHtml(url, site.url)
    if 'Page not found' in listhtml or 'No matches found.' in listhtml:
        utils.notify('Notify', 'No videos found')
        return

    if '?s=' in url:
        match = re.compile(r'class="tab-thumb.+?href="([^"]+)"\s+title="([^"]+)".+?src="([^"]+)".+?chapter"><a href="[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    else:
        match = re.compile(r'class="page-item-detail.+?href="([^"]+)"\s+title="([^"]+)".+?<img src="([^"]+)".+?class="btn-link"[^>]*>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, name, img, ep in match:
        name = utils.cleantext(name)
        img = img.replace(' ', '%20')
        name += "" if '?s=' in url else " [COLOR pink][I]{}[/I][/COLOR]".format(ep.strip())
        site.add_dir(name, video, 'EpList', img)

    if 'class="wp-pagenavi"' in listhtml or ('?s=' in url and len(match) == 20):
        npage = page + 1
        url = url.replace('page/{0}/'.format(page), 'page/{0}/'.format(npage))
        site.add_dir('Next Page ({})'.format(npage), url, 'List', site.img_next, npage)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+') + '&post_type=wp-manga'
        List(url, 1)


@site.register()
def Playvid(url, name, download=None):
    # vp = utils.VideoPlayer(name, download=download)
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'<iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        iframehtml = utils.getHtml(match[0], site.url)
        match = re.compile(r'<meta name="x-secure-token" content="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(iframehtml)
        if match:
            token = match[0]

            ROT13_TABLE = str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
            )

            def decode(encoded):
                try:
                    e = encoded.replace("sha512-", "")
                    e = e.translate(ROT13_TABLE)
                    e = base64.b64decode(e).decode("utf-8")
                    e = e.translate(ROT13_TABLE)
                    e = base64.b64decode(e).decode("utf-8")
                    e = e.translate(ROT13_TABLE)
                    e = base64.b64decode(e).decode("utf-8")
                    return json.loads(e)
                except Exception:
                    return None

            decoded_token = decode(token)

            en = decoded_token.get("en")
            iv = decoded_token.get("iv")
            uri = decoded_token.get("uri")
            uri = 'https:' + uri if uri.startswith('//') else uri

            data = '''------geckoformboundarybfec28fb1c2316e132ff23ab04e3d114
Content-Disposition: form-data; name="action"

zarat_get_data_player_ajax
------geckoformboundarybfec28fb1c2316e132ff23ab04e3d114
Content-Disposition: form-data; name="a"

{}
------geckoformboundarybfec28fb1c2316e132ff23ab04e3d114
Content-Disposition: form-data; name="b"

{}
------geckoformboundarybfec28fb1c2316e132ff23ab04e3d114--
'''.format(en, iv)

            headers = utils.base_hdrs.copy()
            headers['Content-Type'] = 'multipart/form-data; boundary=----geckoformboundarybfec28fb1c2316e132ff23ab04e3d114'

            import requests
            response = requests.post(uri + 'api.php', data=data.encode("utf-8"), headers=headers)
            jdata = json.loads(response.text)

            video_url = jdata.get("data", {}).get("sources", [])[0].get("src")

            subtitle = []
            if video_url.endswith('.m3u8'):
                try:
                    video_file = utils.getHtml(video_url, url)

                    query = {
                        "jsonrpc": "2.0",
                        "method": "Settings.GetSettingValue",
                        "params": {"setting": "subtitles.languages"},
                        "id": 1
                    }
                    response = xbmc.executeJSONRPC(json.dumps(query))
                    value = json.loads(response)
                    langs = value["result"]["value"]
                    lang_codes = [
                        xbmc.convertLanguage(name, xbmc.ISO_639_1)
                        for name in langs
                    ]

                    match = re.compile(r'URI="([^"]+)",TYPE=SUBTITLES,GROUP-ID="subs",LANGUAGE="([^"]+)"').findall(video_file)
                    if match:
                        for sub_url, lang in match:
                            if lang in lang_codes:
                                subtitle.append(video_url.rsplit('/', 1)[0] + '/' + sub_url)
                except Exception:
                    pass
            utils.playvid(video_url, name, subtitle=subtitle)
            # vp.play_from_direct_link(video_url)


@site.register()
def EpList(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile(r'data-chapter="\d+">\s+<a href="([^"]+)".+?<img src="([^"]+)".+?<div>(Ep[^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        for video, img, ep in match:
            site.add_download_link(ep.strip(), video, 'Playvid', img)
        utils.eod()
    else:
        utils.notify('Notify', 'No episodes found')

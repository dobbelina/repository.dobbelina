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
import json
import base64
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.sites.soup_spec import SoupSiteSpec


def _title_with_episode(title, item):
    episode = utils.safe_get_text(item.select_one(".btn-link"), default="")
    if episode:
        return f"{title} [COLOR pink][I]{episode}[/I][/COLOR]"
    return title


site = AdultSite(
    "hentaidude",
    "[COLOR hotpink]Hentaidude[/COLOR]",
    "https://hentaidude.xxx/",
    "hentaidude.png",
    "hentaidude",
)


VIDEO_LIST_SPEC = SoupSiteSpec(
    selectors={
        "items": [".page-item-detail", ".tab-thumb"],
        "url": {"selector": "a", "attr": "href"},
        "title": {
            "selector": "a",
            "attr": "title",
            "text": True,
            "clean": True,
            "fallback_selectors": [".post-title", None],
            "transform": _title_with_episode,
        },
        "thumbnail": {
            "selector": "img",
            "attr": "src",
            "fallback_attrs": ["data-src", "data-original"],
        },
        "description": {"selector": ".btn-link", "text": True, "clean": True},
        "pagination": {
            "selectors": [
                {"query": 'link[rel="next"]', "scope": "soup"},
                {"query": "a.page-numbers.next, a.next", "scope": "soup"},
            ],
            "attr": "href",
            "label": "Next Page",
            "mode": "List",
        },
    },
    play_mode="EpList",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Uncensored[/COLOR]",
        site.url + "genre/uncensored-hentai/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]3D[/COLOR]",
        site.url + "genre/3d-hentai/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Anal[/COLOR]",
        site.url + "genre/anal/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]BBw[/COLOR]",
        site.url + "genre/bbw/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]BDSM[/COLOR]",
        site.url + "genre/bdsm/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Femdom[/COLOR]",
        site.url + "genre/femdom/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Furry[/COLOR]",
        site.url + "genre/furry/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Futanari[/COLOR]",
        site.url + "genre/gender-bender-heantai/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Harem[/COLOR]",
        site.url + "genre/harem/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Horror[/COLOR]",
        site.url + "genre/horror/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Incest[/COLOR]",
        site.url + "genre/incest-hentai/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]MILF[/COLOR]",
        site.url + "genre/milf/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Monster[/COLOR]",
        site.url + "genre/monster/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Romance[/COLOR]",
        site.url + "genre/romance/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]School[/COLOR]",
        site.url + "genre/hentai-school/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Shota[/COLOR]",
        site.url + "genre/shota/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Shotacon[/COLOR]",
        site.url + "genre/shotocon/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Softcore[/COLOR]",
        site.url + "genre/softcore/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Tentacle[/COLOR]",
        site.url + "genre/tentacle/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Tsundere[/COLOR]",
        site.url + "genre/tsundere/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Teen[/COLOR]",
        site.url + "genre/teen-hentai/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Young[/COLOR]",
        site.url + "genre/young-hentai/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Yuri[/COLOR]",
        site.url + "genre/yuri/page/1/?m_orderby=latest",
        "List",
        site.img_cat,
        1,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "page/1/?s=",
        "Search",
        site.img_search,
    )
    List(site.url + "page/1/?m_orderby=latest")


@site.register()
def List(url, page=1):
    listhtml = utils.getHtml(url, site.url)
    if not listhtml or "Page not found" in listhtml or "No matches found." in listhtml:
        utils.notify("Notify", "No videos found")
        return

    soup = utils.parse_html(listhtml)
    VIDEO_LIST_SPEC.run(site, soup, base_url=site.url)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url += keyword.replace(" ", "+") + "&post_type=wp-manga"
        List(url, 1)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    iframe = soup.select_one("iframe[src]")
    if not iframe:
        vp.progress.close()
        utils.notify("Oh Oh", "No Videos found")
        return

    iframe_url = utils.safe_get_attr(iframe, "src", default="")
    iframe_html = utils.getHtml(iframe_url, site.url)
    
    token_meta = utils.parse_html(iframe_html).select_one('meta[name="x-secure-token"]')
    if token_meta:
        token = utils.safe_get_attr(token_meta, "content", default="")
        
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
        if decoded_token:
            en = decoded_token.get("en")
            iv = decoded_token.get("iv")
            uri = decoded_token.get("uri")

            boundary = "----geckoformboundarybfec28fb1c2316e132ff23ab04e3d114"
            data = (
                "--{0}\r\n"
                'Content-Disposition: form-data; name="action"\r\n\r\n'
                "zarat_get_data_player_ajax\r\n"
                "--{0}\r\n"
                'Content-Disposition: form-data; name="a"\r\n\r\n'
                "{1}\r\n"
                "--{0}\r\n"
                'Content-Disposition: form-data; name="b"\r\n\r\n'
                "{2}\r\n"
                "--{0}--\r\n"
            ).format(boundary, en, iv)

            headers = utils.base_hdrs.copy()
            headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary

            import requests
            response = requests.post(uri + 'api.php', data=data.encode("utf-8"), headers=headers)
            jdata = response.json()

            video_url = jdata.get("data", {}).get("sources", [])[0].get("src")

            subtitle = []
            if video_url and video_url.endswith('.m3u8'):
                try:
                    video_file = utils.getHtml(video_url, url)

                    query = {
                        "jsonrpc": "2.0",
                        "method": "Settings.GetSettingValue",
                        "params": {"setting": "subtitles.languages"},
                        "id": 1
                    }
                    rpc_response = xbmc.executeJSONRPC(json.dumps(query))
                    value = json.loads(rpc_response)
                    langs = value.get("result", {}).get("value", [])
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
            
            if video_url:
                utils.playvid(video_url, name, download=download, subtitle=subtitle)
                return

    # Fallback to direct resolution if token logic fails
    vp.play_from_link_to_resolve(iframe_url)


@site.register()
def EpList(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)
    if not soup:
        utils.notify("Notify", "No episodes found")
        return

    for chapter in soup.select("[data-chapter]"):
        link = chapter.select_one("a[href]")
        if not link:
            continue

        episode = utils.safe_get_text(chapter.select_one("div"), default="").strip()
        chapter_num = chapter.get("data-chapter")
        episode_name = episode or (
            f"Episode {chapter_num}"
            if chapter_num
            else utils.safe_get_attr(link, "href", default="")
        )
        img = utils.safe_get_attr(
            chapter.select_one("img"), "src", ["data-src", "data-original"]
        )
        site.add_download_link(
            episode_name, utils.safe_get_attr(link, "href", default=""), "Playvid", img
        )

    utils.eod()

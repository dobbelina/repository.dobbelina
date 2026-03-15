"""
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
"""

from __future__ import annotations

import re
import json
import hashlib
import random
import string
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.sites.soup_spec import SoupSiteSpec

site = AdultSite(
    "pornhd3x",
    "[COLOR hotpink]PornHD3x[/COLOR]",
    "https://pornhd3x.tv/",
    "pornhd3x.png",
    "pornhd3x",
)

_SOURCE_SECRET = "98126avrbi6m49vd7shxkn985"
_TOKEN_SEED = (
    "n1sqcua67bcq9826avrbi6m49vd7shxkn985mhodk06twz87wwxtp3dqiicks2dfy"
    "ud213k6ygiomq01s94e4tr9v0k887bkyud213k6ygiomq01s94e4tr9v0k887bkqocxzw"
    "39esdyfhvtkpzq9n4e7at4kc6k8sxom08bl4dukp16h09oplu7zov4m5f8"
)


VIDEO_LIST_SPEC = SoupSiteSpec(
    selectors={
        "items": ".ml-item.item",
        "url": {"selector": "a.ml-mask", "attr": "href"},
        "title": {"selector": "h2", "text": True, "clean": True},
        "thumbnail": lambda item, soup: utils.get_thumbnail(item.select_one("img")),
        "quality": {"selector": ".mli-quality", "text": True},
        "pagination": {
            "selector": ".pagination li.active + li a",
            "attr": "href",
            "mode": "List",
        },
    }
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Movies[/COLOR]",
        site.url + "porn-hd-free-full-1080p",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]RealityKings[/COLOR]",
        site.url + "studio/realitykings",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]NaughtyAmerica[/COLOR]",
        site.url + "studio/naughtyamerica",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Brazzers[/COLOR]",
        site.url + "studio/brazzers",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    if not listhtml:
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    VIDEO_LIST_SPEC.run(site, soup, base_url=url)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # PornHD3x uses /search/%QUERY%
        search_url = site.url + "search/" + urllib_parse.quote_plus(keyword)
        List(search_url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, IA_check="IA")
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    # Pattern 1: dynamic source API.
    soup = utils.parse_html(html)
    episode = soup.select_one("a[episode-id]")
    episode_id = utils.safe_get_attr(episode, "episode-id")
    
    # Fallback to movie.id JavaScript variable
    if not episode_id:
        match = re.search(r'id\s*:\s*["\']([^"\']+)["\']', html)
        if match:
            episode_id = match.group(1)

    if episode_id:
        seed = "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(6)
        )
        token = hashlib.md5(
            (episode_id + seed + _SOURCE_SECRET).encode("utf-8")
        ).hexdigest()
        cookie_name = "{}{}{}".format(
            _TOKEN_SEED[13:37], episode_id, _TOKEN_SEED[40:64]
        )
        ajax_url = "{}ajax/get_sources/{}/{}?count=1&mobile=false".format(
            site.url, episode_id, token
        )
        headers = {
            "User-Agent": utils.USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": "{}={}".format(cookie_name, seed),
        }
        payload = utils.getHtml(ajax_url, url, headers=headers)
        if payload:
            try:
                source_json = json.loads(payload)
                sources = {}
                for item in source_json.get("playlist", []):
                    for source in item.get("sources", []):
                        source_url = source.get("file")
                        if not source_url:
                            continue
                        label = source.get("label") or source.get("type") or "Video"
                        sources[label] = source_url
                if sources:
                    stream_url = (
                        utils.selector("Select quality", sources)
                        if len(sources) > 1
                        else next(iter(sources.values()))
                    )
                    if stream_url:
                        # Stream URLs are pre-signed with md5+expires tokens; adding
                        # Referer/User-Agent via | would cause inputstream.adaptive to
                        # append them as query params (stream_params) to every segment
                        # URL, making them malformed (curl error 3).
                        vp.play_from_direct_link(stream_url)
                        return
            except Exception:
                pass

    # Pattern 2: inline sources array.
    match = re.search(r"sources\s*:\s*(\[[^\]]+\])", html)
    if match:
        try:
            sources_list = json.loads(match.group(1))
            sources = {
                s.get("label", "Video"): s.get("file")
                for s in sources_list
                if s.get("file")
            }
            if sources:
                best_url = utils.selector("Select quality", sources)
                if best_url:
                    vp.play_from_direct_link(best_url)
                    return
        except Exception:
            pass

    # Pattern 3: direct file pattern.
    match = re.search(r"file:\s*[\"']([^\"']+\.(?:mp4|m3u8)[^\"']*)[\"']", html)
    if match:
        vp.play_from_direct_link(match.group(1))
        return

    # Pattern 4: KVS-like video_url.
    match = re.search(r"video_url\s*[:=]\s*[\"']([^\"']+)[\"']", html)
    if match:
        vp.play_from_direct_link(match.group(1))
        return

    # Pattern 5: video tag source.
    video_tag = soup.find("video")
    if video_tag:
        source = video_tag.find("source")
        if source and source.get("src"):
            vp.play_from_direct_link(source["src"])
            return

    # Pattern 6: iframe fallback.
    iframe = soup.find("iframe")
    if iframe and iframe.get("src"):
        iframe_url = urllib_parse.urljoin(url, iframe["src"])
        vp.play_from_link_to_resolve(iframe_url)
        return

    vp.play_from_link_to_resolve(url)

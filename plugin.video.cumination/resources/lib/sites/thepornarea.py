"""
Cumination
Copyright (C) 2026 Team Cumination

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from __future__ import annotations

import re
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

site = AdultSite(
    "thepornarea",
    "[COLOR hotpink]ThePornArea[/COLOR]",
    "https://thepornarea.com/",
    "cum-sites.png",
)


def _absolute_url(url):
    if not url:
        return ""
    return urllib_parse.urljoin(site.url, url)


def _extract_video_id(url):
    match = re.search(r"/videos/(\d+)/", url)
    return match.group(1) if match else ""


def _play_embed_stream(vp, html, referer):
    stream_url = _extract_player_stream(html)
    if not stream_url:
        return False

    vp.play_from_direct_link(
        "{}|Referer={}&User-Agent={}".format(stream_url, referer, utils.USER_AGENT)
    )
    return True


def _extract_player_stream(html):
    if not html:
        return ""

    match = re.search(r"video_url:\s*'([^']+)'", html)
    if not match:
        return ""

    stream_url = match.group(1)
    if not stream_url.startswith("function/0/"):
        return stream_url

    license_match = re.search(r"license_code:\s*'(\$\d+)", html)
    if not license_match:
        return ""

    return kvs_decode(stream_url, license_match.group(1))


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Latest[/COLOR]",
        site.url + "latest-updates/",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/?q=",
        "Search",
        site.img_search,
    )
    List(site.url + "latest-updates/")


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    for item in soup.select(".th.item"):
        link = item.select_one("a[href]")
        if not link:
            continue

        video_url = _absolute_url(utils.safe_get_attr(link, "href"))
        title = utils.cleantext(
            utils.safe_get_attr(link, "title", default="")
            or utils.safe_get_text(item.select_one(".title"))
        )
        thumb = utils.safe_get_attr(item.select_one("img"), "data-original", ["src"])
        duration = utils.safe_get_text(item.select_one(".time"))

        if title and video_url:
            site.add_download_link(title, video_url, "Playvid", thumb, title, duration=duration)

    next_link = soup.select_one('.next a[href], link[rel="next"]')
    if next_link:
        next_url = _absolute_url(utils.safe_get_attr(next_link, "href"))
        if next_url:
            site.add_dir("Next Page", next_url, "List", site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
        return
    List(url + urllib_parse.quote_plus(keyword))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    video_id = _extract_video_id(url)
    if video_id:
        embed_url = "{}embed/{}".format(site.url, video_id)
        embed_html = utils.getHtml(embed_url, url)
        if embed_html:
            if _play_embed_stream(vp, embed_html, url):
                return
            if "kt_player('kt_player'" in embed_html:
                vp.play_from_kt_player(embed_html, url)
                return

    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    play_url = _extract_player_stream(html)
    if play_url:
        vp.play_from_direct_link("{}|Referer={}".format(play_url, url))
        return

    embed_match = re.search(r"src=\"(https://thepornarea\.com/embed/\d+)\"", html)
    if embed_match:
        vp.play_from_link_to_resolve(embed_match.group(1))
        return

    vp.play_from_link_to_resolve(url)

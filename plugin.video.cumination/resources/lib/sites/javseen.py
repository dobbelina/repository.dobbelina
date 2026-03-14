"""
Cumination
Copyright (C) 2026 Team Cumination

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from __future__ import annotations

import base64
import re
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "javseen",
    "[COLOR hotpink]JAVSeen[/COLOR]",
    "https://javseen.tv/",
    testing=True,
)


def _absolute_url(url):
    if not url:
        return ""
    return urllib_parse.urljoin(site.url, url)


def _extract_next_page(soup):
    next_link = soup.select_one('link[rel="next"]')
    if next_link:
        href = utils.safe_get_attr(next_link, "href")
        if href:
            return _absolute_url(href)

    for link in soup.select(".pagination a[href]"):
        href = utils.safe_get_attr(link, "href")
        if href and href != "#" and "next" in utils.safe_get_text(link).lower():
            return _absolute_url(href)
    return ""


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Recent[/COLOR]", site.url + "recent/", "List", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/video/?s=",
        "Search",
        site.img_search,
    )
    List(site.url + "recent/")


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    for item in soup.select(".video"):
        link = item.select_one("a.thumbnail[href]")
        if not link:
            continue

        video_url = _absolute_url(utils.safe_get_attr(link, "href"))
        title = utils.cleantext(
            utils.safe_get_attr(link, "title", default="")
            or utils.safe_get_text(item.select_one(".video-title"))
        )
        thumb = utils.safe_get_attr(item.select_one("img"), "src")
        duration = utils.safe_get_text(item.select_one(".video-overlay.badge.transparent"))
        duration_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", duration)
        duration = duration_match.group(1) if duration_match else ""

        if title and video_url:
            site.add_download_link(title, video_url, "Playvid", thumb, title, duration=duration)

    next_url = _extract_next_page(soup)
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
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    embed_match = re.search(r'<iframe[^>]+src="([^"]+/embed/\d+/?)"', html, re.IGNORECASE)
    if embed_match:
        embed_url = _absolute_url(embed_match.group(1))
        embed_html = utils.getHtml(embed_url, url)
        if embed_html:
            play_match = re.search(r"playEmbed\('([^']+)'\)", embed_html)
            if play_match:
                vp.play_from_link_to_resolve(play_match.group(1))
                return

            server_match = re.search(r'data-embed="([^"]+)"', embed_html)
            if server_match:
                try:
                    decoded = base64.b64decode(server_match.group(1)).decode("utf-8")
                    vp.play_from_link_to_resolve(decoded)
                    return
                except Exception:
                    pass

        vp.play_from_link_to_resolve(embed_url)
        return

    vp.play_from_link_to_resolve(url)

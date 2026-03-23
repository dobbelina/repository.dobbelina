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

site = AdultSite(
    "analdin",
    "[COLOR hotpink]Analdin[/COLOR]",
    "https://www.analdin.com/",
    "cum-sites.png",
    testing=True,
)


def _absolute_url(url):
    if not url:
        return ""
    return urllib_parse.urljoin(site.url, url)


def _extract_next_page(soup):
    next_link = soup.select_one(".pagination li.next a[href], .pagination li a[href]")
    if next_link:
        href = utils.safe_get_attr(next_link, "href")
        if href and href != "#search":
            return _absolute_url(href)
    return ""


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
        site.url + "search/",
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
    for item in soup.select(".list-videos .item"):
        link = item.select_one("a.popup-video-link[href]")
        if not link:
            continue

        video_url = _absolute_url(utils.safe_get_attr(link, "href"))
        title = utils.cleantext(utils.safe_get_text(item.select_one(".title")))
        img_tag = item.select_one("img")
        thumb = (
            utils.safe_get_attr(img_tag, "data-original", ["src"])
            or utils.safe_get_attr(link, "thumb")
        )

        if title and video_url:
            site.add_download_link(title, video_url, "Playvid", thumb, title)

    next_url = _extract_next_page(soup)
    if next_url:
        site.add_dir("Next Page", next_url, "List", site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
        return
    List(site.url + "search/{}/".format(urllib_parse.quote(keyword)))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    match = re.search(r"video_alt_url:\s*'([^']+)'", html, re.IGNORECASE)
    if not match:
        match = re.search(r"video_url:\s*'([^']+)'", html, re.IGNORECASE)

    if match:
        vp.play_from_direct_link(
            "{}|User-Agent={}&Referer={}".format(match.group(1), utils.USER_AGENT, url)
        )
        return

    if "kt_player(" in html:
        vp.play_from_kt_player(html, url)
        return

    vp.play_from_html(html, url)

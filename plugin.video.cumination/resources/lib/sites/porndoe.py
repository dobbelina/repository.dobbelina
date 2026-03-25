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
    "porndoe",
    "[COLOR hotpink]PornDoe[/COLOR]",
    "https://porndoe.com/",
    "cum-sites.png",
    testing=True,
)


def _absolute_url(url):
    if not url:
        return ""
    return urllib_parse.urljoin(site.url, url)


def _extract_thumb(item):
    svg_el = item.select_one(".video-item-svg")
    if svg_el:
        thumb = utils.safe_get_attr(svg_el, "data-src")
        if thumb:
            return thumb
        style = utils.safe_get_attr(svg_el, "style", default="")
        match = re.search(r'background-image:\s*url\((?:"|\')?([^"\')]+)', style)
        if match:
            return match.group(1)
    img = item.find("img")
    if img:
        return (
            utils.safe_get_attr(img, "data-src")
            or utils.safe_get_attr(img, "src")
            or ""
        )
    return ""


def _extract_direct_stream(html):
    if not html:
        return ""

    source_match = re.search(
        r'<source[^>]+src=["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']',
        html,
        re.IGNORECASE,
    )
    if source_match:
        return source_match.group(1)

    js_match = re.search(
        r"""["'](https?://[^"']+\.(?:mp4|m3u8)[^"']*)["']""",
        html,
        re.IGNORECASE,
    )
    if js_match:
        return js_match.group(1)

    return ""


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Newest[/COLOR]", site.url, "List", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search?keywords=",
        "Search",
        site.img_search,
    )
    List(site.url)


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    for item in soup.select(".video-item[data-video-item], .video-item"):
        link = (
            item.select_one("a.video-item-link[href]")
            or item.select_one(".video-item-block a[href]")
            or item.select_one(".video-item-thumb a[href]")
        )
        if not link:
            continue

        video_url = _absolute_url(utils.safe_get_attr(link, "href"))
        title = utils.cleantext(
            utils.safe_get_attr(link, "aria-label", default="")
            or utils.safe_get_text(item.select_one(".video-item-title"))
        )
        thumb = _extract_thumb(item)
        duration = utils.safe_get_attr(item, "data-duration")

        if title and video_url:
            site.add_download_link(
                title, video_url, "Playvid", thumb, title, duration=duration
            )

    next_link = soup.select_one('link[rel="next"], a[rel="next"], a.pager-item[href]')
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
    List(site.url + "search?keywords=" + urllib_parse.quote_plus(keyword))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    stream_url = _extract_direct_stream(html)
    if stream_url:
        vp.play_from_direct_link(
            "{}|User-Agent={}&Referer={}".format(stream_url, utils.USER_AGENT, url)
        )
        return

    vp.play_from_html(html, url)

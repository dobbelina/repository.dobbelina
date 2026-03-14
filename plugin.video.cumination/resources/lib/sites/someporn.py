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
    "someporn",
    "[COLOR hotpink]SomePorn[/COLOR]",
    "https://some.porn/",
    testing=True,
)


def _absolute_url(url):
    if not url:
        return ""
    return urllib_parse.urljoin(site.url, url)


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Latest[/COLOR]", site.url, "List", site.img_cat)
    site.add_dir("[COLOR hotpink]Search[/COLOR]", site.url + "?q=", "Search", site.img_search)
    List(site.url)


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    for item in soup.select("article.videocard"):
        link = item.select_one("a.js-rc-video-link[href]")
        if not link:
            continue

        video_url = _absolute_url(utils.safe_get_attr(link, "href"))
        title = utils.cleantext(
            utils.safe_get_attr(link.select_one("img"), "alt", default="")
            or utils.safe_get_text(link)
        )
        thumb = utils.get_thumbnail(item.select_one("picture img"))
        duration = utils.safe_get_text(item.select_one(".absolute.bottom-2.right-2 span"))
        if thumb.startswith("//"):
            thumb = "https:" + thumb

        if title and video_url:
            site.add_download_link(title, video_url, "Playvid", thumb, title, duration=duration)

    next_link = soup.select_one('a[rel="next"], link[rel="next"]')
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
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    source_match = re.search(r'<source[^>]+src="([^"]+get-playlist[^"]+)"', html, re.IGNORECASE)
    if source_match:
        play_url = source_match.group(1)
        if play_url.startswith("//"):
            play_url = "https:" + play_url
        vp.play_from_direct_link("{}|Referer={}".format(play_url, url))
        return

    embed_match = re.search(r'<iframe[^>]+src="([^"]+/embed/\d+)"', html, re.IGNORECASE)
    if embed_match:
        vp.play_from_link_to_resolve(_absolute_url(embed_match.group(1)))
        return

    vp.play_from_link_to_resolve(url)

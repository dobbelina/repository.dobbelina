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
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.sites.soup_spec import SoupSiteSpec

site = AdultSite(
    "heavyr",
    "[COLOR hotpink]Heavy-R[/COLOR]",
    "https://www.heavy-r.com/",
    "heavyr.png",
    "heavyr",
)

VIDEO_LIST_SPEC = SoupSiteSpec(
    selectors={
        "items": ".item",
        "url": {"attr": "href"},
        "title": {"selector": ".title", "text": True, "clean": True},
        "thumbnail": {"selector": "img", "attr": "src", "fallback_attrs": ["data-src"]},
        "pagination": {
            "selector": ".pagination a",
            "text_matches": ["next", "»"],
            "attr": "href",
            "mode": "List",
        },
    }
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Videos[/COLOR]", site.url + "videos/", "List", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "index.php?page=videos&section=search",
        "Search",
        site.img_search,
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
        # Heavy-R uses a POST search or query param
        search_url = (
            site.url
            + "index.php?page=videos&section=search&query="
            + urllib_parse.quote_plus(keyword)
        )
        List(search_url)


@site.register()
def Categories(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    # Categories are in .tags or similar lists
    cat_items = soup.select(".tags a, .categories-list a, a[href*='/free_porn/']")

    entries = []
    for anchor in cat_items:
        href = utils.safe_get_attr(anchor, "href")
        if not href:
            continue

        name = utils.safe_get_text(anchor).replace("#", "")
        if not name:
            name = utils.safe_get_attr(anchor, "title")
        if not name:
            continue

        entries.append((name, urllib_parse.urljoin(site.url, href)))

    for name, cat_url in sorted(entries):
        site.add_dir(name, cat_url, "List", "")

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    # Check for direct sources in script
    # var video_url = "..."
    match = re.search(r"video_url\s*[:=]\s*[\"']([^\"']+)[\"']", html)
    if not match:
        match = re.search(r"['\"]file['\"]\s*[:=]\s*['\"]([^'\"]+)['\"]", html)
    
    if match:
        video_url = match.group(1).replace("\\/", "/")
        if not video_url.startswith("http"):
            video_url = urllib_parse.urljoin(site.url, video_url)
        vp.play_from_direct_link(video_url + "|Referer=" + url)
        return

    # Look for fluidplayer or similar sources array
    match = re.search(r"src\s*:\s*[\"']([^\"']+\.mp4[^\"']*)[\"']", html)
    if match:
        video_url = match.group(1).replace("\\/", "/")
        vp.play_from_direct_link(video_url + "|Referer=" + url)
        return

    # Check for quality sources
    match = re.search(r"['\"](?:720|480|360|240)['\"]\s*:\s*['\"]([^'\"]+)['\"]", html)
    if match:
        video_url = match.group(1).replace("\\/", "/")
        vp.play_from_direct_link(video_url + "|Referer=" + url)
        return

    vp.play_from_link_to_resolve(url)

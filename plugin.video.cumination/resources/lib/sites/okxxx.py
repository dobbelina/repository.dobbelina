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
    "okxxx",
    "[COLOR hotpink]OK.XXX[/COLOR]",
    "https://ok.xxx/",
    "okxxx.png",
    "okxxx",
)

VIDEO_LIST_SPEC = SoupSiteSpec(
    selectors={
        "items": ".item",
        "url": {"selector": ".thumb a", "attr": "href"},
        "title": {"selector": ".thumb a", "attr": "title", "clean": True},
        "thumbnail": {
            "selector": "img",
            "attr": "data-original",
            "fallback_attrs": ["src"],
        },
        "duration": {"selector": ".video-meta li:first-child span", "text": True},
        "pagination": {
            "selector": ".pagination a",
            "text_matches": ["next", "»"],
            "attr": "href",
            "mode": "List",
        },
    }
)


def _extract_best_video_url(html):
    candidates = []

    for match in re.finditer(
        r"""<source[^>]+src=["']([^"']+)["'][^>]*(?:label|title)=["']([^"']+)["']""",
        html,
        re.IGNORECASE,
    ):
        source_url = match.group(1)
        quality = match.group(2)
        score_match = re.search(r"(\d+)", quality or "")
        score = int(score_match.group(1)) if score_match else 0
        candidates.append((score, source_url))

    if candidates:
        return max(candidates, key=lambda item: item[0])[1]

    for pattern in (
        r"""video_url:\s*["']([^"']+)["']""",
        r"""videoUrl\s*=\s*["']([^"']+)["']""",
        r"""let\s+url\s*=\s*["']([^"']+)["']""",
    ):
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    return None


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Trending[/COLOR]", site.url + "trending/", "List", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Newest[/COLOR]",
        site.url,
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Top Rated[/COLOR]",
        site.url + "top-rated/",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Most Viewed[/COLOR]",
        site.url + "most-popular/",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
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
        # OK.XXX uses /search/%QUERY%/
        search_url = site.url + "search/" + urllib_parse.quote_plus(keyword) + "/"
        List(search_url)


@site.register()
def Categories(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    cat_items = soup.select(".list-categories .item, .list-categories a")

    entries = []
    for anchor in cat_items:
        if anchor.name != "a":
            anchor = anchor.select_one("a")
        if not anchor:
            continue

        href = utils.safe_get_attr(anchor, "href")
        if not href:
            continue

        name = utils.safe_get_text(anchor)
        if not name:
            name = utils.safe_get_attr(anchor, "title")
        if not name:
            continue

        img_tag = anchor.select_one("img")
        img = utils.safe_get_attr(img_tag, "data-src", ["src"])

        entries.append((name, urllib_parse.urljoin(site.url, href), img))

    for name, cat_url, img in sorted(entries):
        site.add_dir(name, cat_url, "List", img)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    video_url = _extract_best_video_url(html)
    if video_url:
        vp.play_from_direct_link(video_url + "|Referer=" + url)
        return

    vp.play_from_link_to_resolve(url)

"""
Cumination
Copyright (C) 2022 Team Cumination

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

import json
import re
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite(
    "pornkai",
    "[COLOR hotpink]PornKai[/COLOR]",
    "https://pornkai.com/",
    "pornkai.png",
    "pornkai",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "all-categories",
        "Categories",
        site.img_search,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "videos?q={}&sort=best&page=1",
        "Search",
        site.img_search,
    )
    # The API is currently returning 500/504 errors; use the HTML list instead.
    List(site.url + "videos?q=&sort=new&page=1")
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    video_items = soup.select("div.thumbnail")

    for item in video_items:
        link_tag = item.select_one("a.thumbnail_link")
        if not link_tag:
            continue

        videopage = link_tag.get("href")
        if not videopage or not _is_video_link(videopage):
            continue
        videopage = utils.fix_url(videopage, site.url)

        title_tag = item.select_one("a.thumbnail_title")
        title = title_tag.get_text(strip=True) if title_tag else ''
        if not title:
            title = link_tag.get('title', '')
        if not title:
            img_tag = item.select_one('img')
            if img_tag:
                title = img_tag.get('alt', '')
        title = utils.cleantext(title)
        if not title:
            continue

        img_tag = item.select_one("img.slideshow")
        img = _extract_thumbnail(img_tag)
        img = utils.fix_url(img, site.url)

        duration = ""
        duration_tag = item.select_one(".thumbnail_video_length")
        if duration_tag:
            duration = duration_tag.get_text(strip=True)

        context_url = (
            utils.addon_sys
            + "?mode="
            + str("pornkai.Related")
            + "&url="
            + urllib_parse.quote_plus(videopage)
        )
        context_menu = [
            ("[COLOR violet]Related videos[/COLOR]", "RunPlugin(" + context_url + ")")
        ]

        site.add_download_link(
            title,
            videopage,
            "Playvid",
            img,
            title,
            duration=duration,
            contextm=context_menu,
        )

    next_page_tag = soup.select_one('a.prev_next_link:-soup-contains("Next")')
    if next_page_tag:
        next_url = next_page_tag.get('href')
        if next_url:
            next_url = utils.fix_url(next_url, site.url)
            site.add_dir("Next Page", next_url, "List", site.img_next)
    
    utils.eod()


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("pornkai.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = url.format(keyword.replace(" ", "%20"))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    if not cathtml:
        utils.eod()
        return

    soup = utils.parse_html(cathtml)

    category_links = soup.select("a.thumbnail_link, div.thumbnail a[href]")
    for link in category_links:
        caturl = utils.safe_get_attr(link, "href")
        if not caturl:
            continue

        img_tag = link.select_one("img")
        img = _extract_thumbnail(img_tag)
        img = utils.fix_url(img, site.url)

        name_tag = link.select_one(".title, .name, span, strong")
        name = (
            utils.safe_get_text(name_tag)
            or utils.safe_get_attr(link, "title")
            or utils.safe_get_text(link)
        )
        name = utils.cleantext(name)
        if not name:
            continue

        query = ""
        if "?q=" in caturl:
            query = caturl.split("?q=")[-1]
        if query:
            catpage = site.url + "api?query={}&sort=best&page=0&method=search".format(
                query
            )
        else:
            catpage = utils.fix_url(caturl, site.url)

        site.add_dir(name, catpage, "List", img)
    utils.eod()








@site.register()
def Playvid(url, name, download=None):
    videohtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(videohtml)
    iframe = soup.select_one('.if_cont iframe, #video_container iframe, #player_container iframe')

    vp = utils.VideoPlayer(name, download)
    if iframe:
        vid_url = iframe.get('src', '')
        if vid_url:
            if 'xvideos.com' in vid_url or 'xh.video' in vid_url:
                vp.play_from_link_to_resolve(vid_url)
                return

    # Fallback to the original method if iframe not found or src is not a direct link
    vp.play_from_html(videohtml, url)


def _is_video_link(url):
    if not url:
        return False

    parsed = urllib_parse.urlparse(url)
    path = parsed.path or ""

    if path.startswith("/cam"):
        return False
    if path.startswith("/videos") and parsed.query:
        return False

    return path.startswith("/videos/") or path.startswith("/view")


def _extract_thumbnail(img_tag):
    if not img_tag:
        return ""

    # Preference order for attributes
    attrs = [
        "data-src",
        "data-original",
        "data-lazy",
        "data-lazy-src",
        "data-thumbnail",
        "data-srcset",
        "srcset",
        "src",
    ]

    for attr in attrs:
        val = img_tag.get(attr)
        if not val:
            continue

        # Handle srcset (take first/highest resolution if multiple)
        if "srcset" in attr and "," in val:
            # Try to get the largest one (usually last in list)
            parts = [p.strip().split(" ")[0] for p in val.split(",")]
            if parts:
                val = parts[-1]

        # Ignore obvious placeholders/tracking pixels
        if (
            val
            and "data:image" not in val
            and not val.endswith(".gif")
            and len(val) > 10
        ):
            return val

    # Final fallback to src if all else failed or was filtered
    return img_tag.get("src", "")

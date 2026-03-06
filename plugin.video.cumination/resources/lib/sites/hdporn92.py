"""
Cumination
Copyright (C) 2023 Team Cumination

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.http_timeouts import HTTP_TIMEOUT_CONNECT
import requests
import json

site = AdultSite(
    "hdporn92",
    "[COLOR hotpink]Hdporn92[/COLOR]",
    "https://hdporn92.com/",
    "hdporn92.png",
    "hdporn92",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Actors[/COLOR]",
        site.url + "actors/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]", site.url + "tags/", "Tags", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url + "?filter=latest")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, "")
    if ">Nothing found</h1>" in listhtml:
        utils.notify(msg="Nothing found")
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    video_items = soup.select("article")

    for item in video_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title")

            img_tag = item.select_one("img")
            img = utils.safe_get_attr(img_tag, "poster", ["src"])

            if not videopage or not name:
                continue

            name = utils.cleantext(name)

            contextmenu = []
            contexturl = (
                utils.addon_sys
                + "?mode="
                + str("hdporn92.Lookupinfo")
                + "&url="
                + urllib_parse.quote_plus(videopage)
            )
            contextmenu.append(
                ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
            )

            site.add_download_link(
                name, videopage, "Playvid", img, name, contextm=contextmenu
            )

        except Exception as e:
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Handle pagination
    pagination = soup.select_one(".pagination")
    if pagination:
        current = pagination.select_one(".current")
        if current:
            next_link = current.find_next("a")
            if next_link and next_link.get("href"):
                next_url = next_link.get("href")
                page_number = next_url.split("/")[-2] if "/" in next_url else ""
                site.add_dir(
                    "Next Page (" + page_number + ")", next_url, "List", site.img_next
                )

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    playhtml = utils.getHtml(url)
    match = re.compile(
        r'<iframe.+?src="([^"]+)"[^>]+allowfullscreen', re.DOTALL | re.IGNORECASE
    ).findall(playhtml)
    if match:
        link = match[0]
        if vp.resolveurl.HostedMediaFile(link):
            try:
                response = requests.head(
                    link, allow_redirects=True, timeout=HTTP_TIMEOUT_CONNECT
                )
                link = response.url or link
            except requests.RequestException as e:
                utils.kodilog("hdporn92: redirect probe failed: {}".format(str(e)))
            vp.play_from_link_to_resolve(link)
            return
        else:
            embedhtml = utils.getHtml(link, url)
            unpacked = utils.get_packed_data(embedhtml)
            jsondata = unpacked.split("var links=")[1].split("}")[0] + "}"
            jsondata = json.loads(jsondata)
            videolink = jsondata.get("hls2", "")
            if videolink:
                vp.play_from_direct_link(videolink)
            return
    else:
        utils.notify("Oh Oh", "No Videos found")


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    categories = []
    articles = soup.select("article")
    for article in articles:
        try:
            link = article.select_one("a[href]")
            if not link:
                continue

            catpage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title")

            img_tag = article.select_one("img")
            img = utils.safe_get_attr(img_tag, "poster", ["src"])

            if name and catpage:
                name = utils.cleantext(name.strip())
                categories.append((name, catpage + "?filter=latest", img))

        except Exception as e:
            utils.kodilog("Error parsing category: " + str(e))
            continue

    # Sort by name and add directories
    for name, catpage, img in sorted(categories, key=lambda x: x[0].lower()):
        site.add_dir(name, catpage, "List", img)

    # Handle pagination for categories
    pagination = soup.select_one(".pagination")
    if pagination:
        current = pagination.select_one(".current")
        if current:
            next_link = current.find_next("a")
            if next_link and next_link.get("href"):
                next_url = next_link.get("href")
                page_number = next_url.split("/")[-2] if "/" in next_url else ""
                site.add_dir(
                    "Next Page (" + page_number + ")",
                    next_url,
                    "Categories",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Look for tag links with aria-label
    tag_links = soup.select('a[href*="/tag/"][aria-label]')
    for link in tag_links:
        try:
            href = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "aria-label")

            if href and name:
                # Extract the tag part from the full URL
                if "/tag/" in href:
                    tag_part = href[href.find("/tag/") :]
                    name = utils.cleantext(name.strip())
                    site.add_dir(
                        name, site.url + tag_part + "?filter=latest", "List", ""
                    )

        except Exception as e:
            utils.kodilog("Error parsing tag: " + str(e))
            continue

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'(category/[^"]+)"\s*?class="label"\s*?title="([^"]+)"', ""),
        ("Model", r'(actor/[^"]+)"\s*?title="([^"]+)"', ""),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, "hdporn92.List", lookup_list)
    lookupinfo.getinfo()

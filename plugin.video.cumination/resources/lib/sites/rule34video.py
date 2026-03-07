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
import time
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from urllib.parse import urljoin

site = AdultSite(
    "rule34video",
    "[COLOR hotpink]Rule34 Video[/COLOR]",
    "https://rule34video.com/",
    "rule34video.png",
    "rule34video",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Cats",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]", site.url + "tags/", "TagMenu", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    # Find all video items - they have class="item" and contain a link with "open-popup"
    items = soup.select(".item")

    for item in items:
        # Get video link with "open-popup" class
        link = item.select_one("a.open-popup")
        if not link:
            continue

        videopage = utils.safe_get_attr(link, "href")
        if not videopage:
            continue

        # Normalize URL
        videopage = urljoin(site.url, videopage)

        # Get thumbnail - look for img with "original" attribute (lazy-load)
        img_tag = item.select_one("img")
        img = utils.get_thumbnail(img_tag)

        # Get title from img alt
        name = utils.safe_get_attr(img_tag, "alt")
        name = utils.cleantext(name.strip()) if name else ""

        # Check for HD badge
        hd_badge = item.select_one('.is-hd, [class*="hd"]')
        hd = " [COLOR orange]HD[/COLOR]" if hd_badge else ""

        # Get duration
        duration_tag = item.select_one('.time, [class*="time"]')
        duration = utils.safe_get_text(duration_tag, default="")

        if videopage and name:
            site.add_download_link(
                name, videopage, "Playvid", img, name, duration=duration, quality=hd
            )

    # Handle pagination using BeautifulSoup
    pager_next = soup.select_one(".pager.next")

    if pager_next:
        # Extract block_id and parameters from next page link
        block_id = utils.safe_get_attr(pager_next, "data-block-id")
        params_raw = utils.safe_get_attr(pager_next, "data-parameters")

        if block_id and params_raw:
            # Parse parameters (format: "key1:value1;key2:value2")
            params = params_raw.replace(":", "=").replace(";", "&")
            if "+" in params:
                params = params.replace(
                    "+", "={0}&".format(params.split("=")[-1].zfill(2))
                )
            params = params.replace("%20", "+")

            # Get current and last page numbers
            active_page = soup.select_one(".pagination .item.active")
            currpg = "1"
            if active_page:
                active_link = active_page.select_one("a")
                if active_link:
                    params_match = re.search(
                        r"from(?:_albums)?:(\d+)",
                        utils.safe_get_attr(active_link, "data-parameters"),
                    )
                    if params_match:
                        currpg = params_match.group(1)

            # Get last page
            last_page_items = soup.select(".pagination .item a")
            lastpg = currpg
            for last_item in last_page_items:
                params_text = utils.safe_get_attr(last_item, "data-parameters")
                if params_text:
                    last_match = re.search(r"from(?:_albums)?:(\d+)", params_text)
                    if last_match:
                        lastpg = last_match.group(1)

            nextpg = "{0}?mode=async&function=get_block&block_id={1}&{2}".format(
                url.split("?")[0], block_id, params
            )
            site.add_dir(
                "Next Page... (Currently in Page {} of {})".format(currpg, lastpg),
                nextpg,
                "List",
                site.img_next,
            )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "-")
        searchUrl = "{0}{1}/".format(searchUrl, title)
        List(searchUrl)


@site.register()
def TagMenu(url):
    taghtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(taghtml)

    # Find all tag menu items with data-block-id="list_tags_tags_list"
    tag_links = soup.select('a[data-block-id="list_tags_tags_list"]')

    for link in tag_links:
        # Get section from data-parameters attribute
        params = utils.safe_get_attr(link, "data-parameters")
        if not params:
            continue

        # Extract section from "section:value" format
        section_match = re.search(r"section:([^;,\s]+)", params)
        if not section_match:
            continue

        section = section_match.group(1)
        name = utils.safe_get_text(link, default="")

        if section and name:
            tagurl = "{0}?mode=async&function=get_block&block_id=list_tags_tags_list&section={1}&from=1&_={2}".format(
                url, section, int(time.time() * 1000)
            )
            site.add_dir(name, tagurl, "Tag", page=1)

    utils.eod()


@site.register()
def Tag(url, page=1):
    taghtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(taghtml)

    # Find all tag items
    tag_items = soup.select(".item")

    for item in tag_items:
        # Get the tag link
        link = item.select_one("a")
        if not link:
            continue

        tagpage = utils.safe_get_attr(link, "href")
        if not tagpage:
            continue

        # Normalize URL
        tagpage = urljoin(site.url, tagpage)

        # Get tag name - it's the text before the <span>
        name = utils.safe_get_text(link, default="").strip()

        # Get video count from SVG sibling or span
        video_count_elem = item.select_one("svg ~ *")
        if not video_count_elem:
            # Try finding any text after SVG
            svg = item.select_one("svg")
            if svg and svg.next_sibling:
                video_count = str(svg.next_sibling).strip()
            else:
                video_count = ""
        else:
            video_count = utils.safe_get_text(video_count_elem, default="").strip()

        # Format name with video count
        if name:
            if video_count:
                name = "{} [COLOR orange]{}[/COLOR]".format(name, video_count)
            site.add_dir(name, tagpage, "List")

    # Pagination - if we got 120 items, there might be more
    if len(tag_items) == 120:
        nextpg = url.replace("from={}".format(page), "from={}".format(page + 1))
        site.add_dir("Next Page", nextpg, "Tag", site.img_next, page=page + 1)

    utils.eod()


@site.register()
def Cats(url):
    if "?" not in url:
        url = "{0}?mode=async&function=get_block&block_id=list_categories_categories_list&sort_by=title&_={1}".format(
            url, int(time.time() * 1000)
        )
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    # Find all category items
    items = soup.select(".item")

    for item in items:
        # Get category link with class "th" (thumbnail)
        link = item.select_one("a.th")
        if not link:
            continue

        catpage = utils.safe_get_attr(link, "href")
        if not catpage:
            continue

        # Normalize URL
        catpage = urljoin(site.url, catpage)

        # Get thumbnail image
        img_tag = item.select_one("img")
        img = utils.get_thumbnail(img_tag)

        # Get category title
        title_elem = item.select_one('.title, [class*="title"]')
        name = utils.safe_get_text(title_elem, default="")
        name = utils.cleantext(name) if name else ""

        if catpage and name:
            site.add_dir(name, catpage, "List", img)

    # Handle pagination using BeautifulSoup
    pager_next = soup.select_one(".item.pager.next")

    if pager_next:
        # Extract parameters from next page
        params = utils.safe_get_attr(pager_next, "data-parameters")
        if params:
            # Extract "from" value from parameters
            from_match = re.search(r"from:(\d+)", params)
            if from_match:
                from_value = from_match.group(1)

                # Get current page
                active_item = soup.select_one(".item.active")
                currpg = "1"
                if active_item:
                    active_params = utils.safe_get_attr(active_item, "data-parameters")
                    if active_params:
                        curr_match = re.search(r"from:0?(\d+)", active_params)
                        if curr_match:
                            currpg = curr_match.group(1)

                # Get last page
                last_items = soup.select(".item a")
                lastpg = currpg
                for last_item in last_items:
                    last_text = utils.safe_get_text(last_item, default="")
                    if "Last" in last_text:
                        last_params = utils.safe_get_attr(last_item, "data-parameters")
                        if last_params:
                            last_match = re.search(r"from:0?(\d+)", last_params)
                            if last_match:
                                lastpg = last_match.group(1)
                                break

                # Build next page URL
                nextpg = re.sub(r"([?&])from=\d+&?", r"\1", url)
                if nextpg.endswith("?") or nextpg.endswith("&"):
                    nextpg = nextpg[:-1]

                connector = "&" if "?" in nextpg else "?"
                nextpg = re.sub(
                    r"&_=\d+",
                    "{0}from={1}&_={2}".format(
                        connector if "&_=" not in nextpg else "",
                        from_value,
                        int(time.time() * 1000),
                    ),
                    nextpg,
                )
                if "&_=" not in nextpg:
                    nextpg += "{0}from={1}&_={2}".format(
                        connector, from_value, int(time.time() * 1000)
                    )
                site.add_dir(
                    "Next Page... (Currently in Page {} of {})".format(currpg, lastpg),
                    nextpg,
                    "Cats",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, site.url)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)

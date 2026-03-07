"""
Cumination
Copyright (C) 2025 Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc
import xbmcgui


site = AdultSite(
    "longvideos",
    "[COLOR hotpink]LongVideos.xxx[/COLOR]",
    "https://www.longvideos.xxx/",
    "longvideos.png",
    "longvideos",
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
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/{}/relevance/",
        "Search",
        site.img_search,
    )
    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if "There is no data in this list." in listhtml:
        utils.notify(msg="No videos found!")
        return

    soup = utils.parse_html(listhtml)

    cm = []
    cm_lookupinfo = utils.addon_sys + "?mode=" + str("longvideos.Lookupinfo") + "&url="
    cm.append(
        ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + cm_lookupinfo + ")")
    )
    cm_related = utils.addon_sys + "?mode=" + str("longvideos.Related") + "&url="
    cm.append(
        ("[COLOR deeppink]Related videos[/COLOR]", "RunPlugin(" + cm_related + ")")
    )

    # Find all video items
    items = soup.select(".item")
    for item in items:
        try:
            # Get video link
            link = item.select_one('a[href*="/videos/"]')
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            if not videopage or site.url + "videos/" not in videopage:
                continue

            name = utils.safe_get_attr(link, "title")
            if not name:
                name = utils.safe_get_text(link, "").strip()
            if not name and videopage:
                name = videopage.rstrip("/").split("/")[-1]
            name = utils.cleantext(name)

            # Get image (must be jpg)
            img_tag = item.select_one("img[src], img[data-src]")
            img = ""
            if img_tag:
                img_src = utils.safe_get_attr(img_tag, "src", ["data-src"])
                if img_src and img_src.endswith("jpg"):
                    img = img_src

            # Get duration
            duration_tag = item.select_one(".duration")
            duration = ""
            if duration_tag:
                duration_text = utils.safe_get_text(duration_tag, "").strip()
                # Extract just the time digits/colons
                duration = re.sub(r"[^\d:]", "", duration_text) if duration_text else ""

            # Check for quality (k4 or FHD class)
            quality = ""
            if item.select_one(".k4, .FHD"):
                quality = "FHD"

            site.add_download_link(
                name,
                videopage,
                "Playvid",
                img,
                name,
                duration=duration,
                quality=quality,
                contextm=cm,
            )
        except Exception as e:
            utils.kodilog("longvideos List: Error processing video - {}".format(e))
            continue

    # Pagination
    next_link = soup.select_one('a[aria-label="Next"][href]')
    if next_link:
        next_url = utils.safe_get_attr(next_link, "href")
        if next_url:
            # Extract page number from URL
            next_page_match = re.search(r"/(\d+)/", next_url)
            next_page = next_page_match.group(1) if next_page_match else ""

            # Find last page number
            last_page = ""
            pagination_items = soup.select(".pagination li")
            for item in reversed(pagination_items):
                if "next" in utils.safe_get_attr(item, "class", default=""):
                    # Get previous sibling for last page number
                    prev_item = item.find_previous_sibling("li")
                    if prev_item:
                        last_link = prev_item.select_one("a[href]")
                        if last_link:
                            last_page_match = re.search(
                                r"/(\d+)/", utils.safe_get_attr(last_link, "href")
                            )
                            last_page = (
                                last_page_match.group(1) if last_page_match else ""
                            )
                    break

            # Add next page directory with goto page context menu
            cm_goto = []
            if next_page and last_page:
                cm_goto_url = (
                    utils.addon_sys
                    + "?mode=longvideos.GotoPage&url="
                    + urllib_parse.quote_plus(next_url)
                    + "&np="
                    + next_page
                    + "&lp="
                    + last_page
                )
                cm_goto.append(
                    (
                        "[COLOR hotpink]Goto Page[/COLOR]",
                        "RunPlugin(" + cm_goto_url + ")",
                    )
                )

            site.add_dir(
                "Next Page ({})".format(next_page) if next_page else "Next Page",
                next_url,
                "List",
                site.img_next,
                contextm=cm_goto if cm_goto else None,
            )

    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg="Out of range!")
            return
        url = url.replace("/{}/".format(np), "/{}/".format(pg))
        contexturl = (
            utils.addon_sys
            + "?mode="
            + "longvideos.List&url="
            + urllib_parse.quote_plus(url)
        )
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        List(url.format(keyword.replace(" ", "-")))


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # Find all category links
    cat_links = soup.select("a.item[href][title]")
    for link in cat_links:
        try:
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue

            name = utils.safe_get_attr(link, "title")
            if not name:
                name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            site.add_dir(name, catpage, "List", "")
        except Exception as e:
            utils.kodilog("longvideos Categories: Error processing category - {}".format(e))
            continue

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(videohtml)

    # Find all video source tags with type="video/mp4" and label attributes
    source_tags = soup.select('source[src][type="video/mp4"][label]')
    sources = {}
    for source in source_tags:
        try:
            src = utils.safe_get_attr(source, "src")
            label = utils.safe_get_attr(source, "label")
            if src and label:
                # Replace 2160p with 1080p in label
                label = label.replace("2160p", "1080p")
                sources[label] = src
        except Exception as e:
            utils.kodilog("longvideos Playvid: Error processing source - {}".format(e))
            continue

    if sources:
        vp.progress.update(50, "[CR]Loading video[CR]")
        videourl = utils.prefquality(
            sources, sort_by=lambda x: int(x[:-1]), reverse=True
        )
        if videourl:
            vp.play_from_direct_link(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Channel", r'href="https://www.longvideos.xxx/(sites[^"]+)">([^<]+)<', ""),
        # ("Network", r'href="https://www.longvideos.xxx/(networks[^"]+)">([^<]+)<', ''),
        # ("Categories", r'href="https://www.longvideos.xxx/(categories[^"]+)">([^<]+)<', ''),
        ("Models", r'href="https://www.longvideos.xxx/(models[^"]+)">([^<]+)<', ""),
    ]
    lookupinfo = utils.LookupInfo(site.url, url, "longvideos.List", lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("longvideos.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")

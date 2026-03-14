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
    "freepornvideos",
    "[COLOR hotpink]FreePornVideos[/COLOR]",
    "https://www.freepornvideos.xxx/",
    "freepornvideos.png",
    "freepornvideos",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/{}/",
        "Search",
        site.img_search,
    )
    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    def add_img_headers(img_url):
        if not img_url:
            return img_url
        if "|" in img_url:
            return img_url
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        if not img_url.startswith("http"):
            return img_url
        if "freepornvideos" in img_url:
            return "{}|Referer={}&User-Agent={}".format(
                img_url, site.url, utils.USER_AGENT
            )
        return img_url

    listhtml = utils.getHtml(url)
    if "There is no data in this list." in listhtml:
        utils.notify(msg="No videos found!")
        return
    listhtml = listhtml.replace('<div class="k4">', '<div class="FHD">')

    soup = utils.parse_html(listhtml)
    video_items = soup.select("div.item")

    cm = []
    cm_lookupinfo = (
        utils.addon_sys + "?mode=" + str("freepornvideos.Lookupinfo") + "&url="
    )
    cm.append(
        ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + cm_lookupinfo + ")")
    )
    cm_related = utils.addon_sys + "?mode=" + str("freepornvideos.Related") + "&url="
    cm.append(
        ("[COLOR deeppink]Related videos[/COLOR]", "RunPlugin(" + cm_related + ")")
    )

    for item in video_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            name = utils.safe_get_attr(link, "title")
            if not name:
                continue

            img_tag = item.select_one("img")
            img = utils.safe_get_attr(
                img_tag, "data-src", ["data-lazy-src", "data-original", "src"]
            )
            img = add_img_headers(img)
            if not img:
                continue

            name = utils.cleantext(name)

            # Get duration
            duration_tag = item.select_one(".duration")
            duration = utils.safe_get_text(duration_tag) if duration_tag else ""

            # Get quality
            quality_tag = item.select_one(".FHD")
            quality = "FHD" if quality_tag else ""

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
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one("a.page[href]:not(.page-current)")
    if next_link:
        next_url = utils.safe_get_attr(next_link, "href")
        if next_url:
            # Extract page numbers
            page_match = re.search(r"/(\d+)/", next_url)
            np = page_match.group(1) if page_match else ""

            # Find last page
            last_link = soup.select_one("a.page[href*='Last']")
            lp = ""
            if last_link:
                last_match = re.search(r'/(\d+)/">Last', str(last_link))
                lp = last_match.group(1) if last_match else ""

            page_label = "Next Page"
            if np:
                page_label += " ({})".format(np)
                if lp:
                    page_label += "/{}".format(lp)

            cm_page = (
                utils.addon_sys
                + "?mode=freepornvideos.GotoPage&list_mode=freepornvideos.List&url="
                + urllib_parse.quote_plus(next_url)
                + "&np="
                + str(np)
                + "&lp="
                + str(lp)
            )
            cm = [("[COLOR violet]Goto Page #[/COLOR]", "RunPlugin(" + cm_page + ")")]

            site.add_dir(page_label, next_url, "List", site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg="Out of range!")
            return
        url = re.sub(r"/\d+/$", r"/{}/".format(pg), url, count=0, flags=re.IGNORECASE)
        contexturl = (
            utils.addon_sys
            + "?mode="
            + "freepornvideos.List&url="
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
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)

    # Try multiple patterns for video source extraction
    sources = {}

    # Pattern 1: <source src='...' label="..."> (original pattern with single quotes)
    match = re.compile(
        r"<source\s+src='([^']+)'[^>]+?label=\"([^\"]+)\"", re.DOTALL | re.IGNORECASE
    ).findall(videopage)
    if match:
        for videourl, quality in match:
            quality = "1080p" if quality == "2160p" else quality
            sources[quality] = videourl

    # Pattern 2: <source src="..." label="..."> (double quotes for both)
    if not sources:
        match = re.compile(
            r"<source\s+src=\"([^\"]+)\"[^>]+?label=\"([^\"]+)\"",
            re.DOTALL | re.IGNORECASE,
        ).findall(videopage)
        if match:
            for videourl, quality in match:
                quality = "1080p" if quality == "2160p" else quality
                sources[quality] = videourl

    # Pattern 3: <source label="..." src="..."> (reversed attribute order)
    if not sources:
        match = re.compile(
            r"<source\s+label=[\"']([^\"']+)[\"'][^>]+?src=[\"']([^\"']+)[\"']",
            re.DOTALL | re.IGNORECASE,
        ).findall(videopage)
        if match:
            for quality, videourl in match:
                quality = "1080p" if quality == "2160p" else quality
                sources[quality] = videourl

    # Pattern 4: General <source> tag with src and label/res/data-res attributes
    if not sources:
        # Find all source tags and extract both src and quality indicators
        source_tags = re.findall(r"<source[^>]+>", videopage, re.IGNORECASE)
        for tag in source_tags:
            src_match = re.search(r'src=["\']([^"\']+)["\']', tag, re.IGNORECASE)
            quality_match = re.search(
                r'(?:label|res|data-res|title)=["\']([^"\']+)["\']', tag, re.IGNORECASE
            )
            if src_match:
                videourl = src_match.group(1)
                quality = quality_match.group(1) if quality_match else "Unknown"
                if not quality.endswith("p"):
                    quality = quality + "p"
                quality = "1080p" if quality == "2160p" else quality
                sources[quality] = videourl

    if sources:
        videourl = utils.selector(
            "Select quality",
            sources,
            setting_valid="qualityask",
            sort_by=lambda x: 1081
            if x == "4k"
            else (int(x[:-1]) if x[:-1].isdigit() else 0),
            reverse=True,
        )
        if videourl:
            vp.progress.update(75, "[CR]Video found[CR]")
            vp.play_from_direct_link(videourl)
    else:
        utils.kodilog("FreePornVideos: No video sources found, trying resolveurl")
        vp.play_from_link_to_resolve(url)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        (
            "Channel",
            r'<a class="btn_sponsor" href="https://www.freepornvideos.xxx/(sites/[^"]+)">([^<]+)<',
            "",
        ),
        (
            "Pornstar",
            r'<a class="btn_model" href="https://www.freepornvideos.xxx/(models/[^"]+)">([^<]+)<',
            "",
        ),
        (
            "Network",
            r'<a class="btn_sponsor_group" href="https://www.freepornvideos.xxx/(networks/[^"]+)">([^<]+)<',
            "",
        ),
        (
            "Tags",
            r'<a class="btn_tag" class="link" href="https://www.freepornvideos.xxx/(categories/[^"]+)">([^<]+)<',
            "",
        ),
    ]
    lookupinfo = utils.LookupInfo(site.url, url, "freepornvideos.List", lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("freepornvideos.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")

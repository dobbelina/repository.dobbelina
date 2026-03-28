"""
Cumination
Copyright (C) 2021 Team Cumination

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
import json

site = AdultSite(
    "eroticage",
    "[COLOR hotpink]EroticAge[/COLOR]",
    "https://www.eroticage.net/",
    "eroticage.png",
    "eroticage",
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
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url + "?filter=latest")
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, "")
    if ">Nothing found<" in html:
        utils.notify(msg="Nothing found")
        utils.eod()
        return

    soup = utils.parse_html(html)
    video_items = soup.select("article[data-video-id]")

    for item in video_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title") or utils.safe_get_text(link)

            img_tag = item.select_one("img")
            img = utils.safe_get_attr(img_tag, "data-src", ["src", "poster"])

            if not videopage or not name:
                continue

            name = utils.cleantext(name)
            site.add_download_link(name, videopage, "Playvid", img, name)
        except Exception as e:
            utils.kodilog("Error parsing video item in eroticage: " + str(e))
            continue

    # Handle pagination
    pagination = soup.select_one(".pagination")
    if pagination:
        next_tag = pagination.select_one("a.next, a:-soup-contains('Next')")
        if next_tag:
            next_url = utils.safe_get_attr(next_tag, "href")
            if next_url:
                # Extract page numbers
                page_num = ""
                m = re.search(r"/(\d+)/", next_url)
                if m:
                    page_num = m.group(1)

                lp = ""
                last_tag = pagination.select_one("a.last, a:-soup-contains('Last')")
                if last_tag:
                    m_last = re.search(
                        r"/(\d+)/", utils.safe_get_attr(last_tag, "href", "")
                    )
                    if m_last:
                        lp = "/" + m_last.group(1)

                site.add_dir(
                    "Next Page ({}{})".format(page_num, lp),
                    next_url,
                    "List",
                    site.img_next,
                )
        else:
            # Fallback for some page layouts
            current = pagination.select_one(".current")
            if current:
                next_node = current.find_next("a")
                if next_node:
                    next_url = utils.safe_get_attr(next_node, "href")
                    if next_url:
                        site.add_dir("Next Page", next_url, "List", site.img_next)

    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    cat_items = soup.select('article[id^="post"]')
    for item in cat_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            caturl = utils.safe_get_attr(link, "href")
            img_tag = item.select_one("img")
            img = utils.safe_get_attr(img_tag, "src", ["data-src"])

            name_tag = item.select_one(".cat-title")
            name = utils.safe_get_text(name_tag) or utils.safe_get_attr(link, "title")

            if name and caturl:
                name = utils.cleantext(name)
                site.add_dir(name, caturl, "List", img)
        except Exception as e:
            utils.kodilog("Error parsing category in eroticage: " + str(e))
            continue

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = "{0}{1}".format(url, keyword.replace(" ", "%20"))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    videohtml = utils.getHtml(url)
    if not videohtml:
        vp.play_from_link_to_resolve(url)
        return

    # Try standard iframe data-src first
    match = re.search(r'<iframe[^>]+data-src="([^"]+)"', videohtml, re.IGNORECASE)
    if not match:
        match = re.search(r'<iframe[^>]+src="([^"]+)"', videohtml, re.IGNORECASE)

    if match:
        videourl = match.group(1)
        if "xhamster" in videourl.lower():
            from resources.lib.sites.xhamster import Playvid as xhamsterPlayvid
            xhamsterPlayvid(videourl, name, download)
            return
        if vp.resolveurl.HostedMediaFile(videourl):
            vp.play_from_link_to_resolve(videourl)
            return

    # Check for script-based direct links (common in newer players)
    match = re.search(r'["\']file["\']\s*:\s*["\']([^"\']+\.mp4[^"\']*)["\']', videohtml, re.IGNORECASE)
    if not match:
        match = re.search(r'["\']contentProviderUrl["\']\s*:\s*["\']([^"\']+)["\']', videohtml, re.IGNORECASE)

    if match:
        video_url = match.group(1).replace("\\/", "/")
        if not video_url.startswith("http"):
            video_url = urllib_parse.urljoin(site.url, video_url)
        vp.play_from_direct_link(video_url + "|Referer=" + url)
        return

    # Original metadata-based extraction
    match = re.findall(r'itemprop="embedURL" content="([^"]+)"', videohtml, re.IGNORECASE)
    if match:
        iframehtml = utils.getHtml(match[0])
        if iframehtml:
            match = re.findall(r"iframeElement\.src\s*=\s*['\"]([^'\"]+)['\"]", iframehtml, re.IGNORECASE)
            if match:
                playerurl = "https:" + match[0] if match[0].startswith("//") else match[0]
                playerhtml = utils.getHtml(playerurl)
                if playerhtml:
                    match = re.findall(r'"contentProviderUrl":"([^"]+)"', playerhtml, re.IGNORECASE)
                    if match:
                        contenturl = match[0].replace(r"\/", "/")
                        vp.play_from_direct_link(contenturl + "|Referer=" + playerurl)
                        return

    vp.play_from_link_to_resolve(url)

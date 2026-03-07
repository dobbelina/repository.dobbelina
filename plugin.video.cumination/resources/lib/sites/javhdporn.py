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

import re
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "javhdporn",
    "[COLOR hotpink]JavHD Porn[/COLOR]",
    "https://www4.javhdporn.net/",
    "javhdporn.png",
    "javhdporn",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Cat",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Actress[/COLOR]", site.url + "pornstars/", "Cat", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Find all article elements with video items
    articles = soup.select("article")
    for article in articles:
        try:
            # Get video link and title
            link = article.select_one("a[href][title]")
            if not link:
                continue
            video = utils.safe_get_attr(link, "href")
            if not video:
                continue

            name = utils.safe_get_attr(link, "title", default="")
            name = utils.cleantext(name)
            if not name:
                continue

            # Get image - try data-lazy-src first, then src
            img_tag = article.select_one("img")
            if not img_tag:
                continue
            img = utils.safe_get_attr(img_tag, "data-lazy-src", ["src"])

            # Check for HD badge
            hd = (
                "HD"
                if article.find(
                    string=lambda text: text and ">HD<" in text if text else False
                )
                or article.select_one('.hd, [class*="hd"]')
                else ""
            )

            # Get duration
            duration_elem = article.select_one('.duration, [class*="duration"]')
            duration = ""
            if duration_elem:
                duration_text = utils.safe_get_text(duration_elem, "").strip()
                # Extract time pattern (digits and colons)
                time_match = re.search(r"[\d:]+", duration_text)
                duration = time_match.group(0) if time_match else ""

            site.add_download_link(
                name, video, "Play", img, name, duration=duration, quality=hd
            )
        except Exception as e:
            utils.kodilog("javhdporn List: Error processing video - {}".format(e))
            continue

    # Pagination
    pagination = soup.select_one('.pagination, [class*="pagination"]')
    if pagination:
        # Find next link
        next_link = pagination.find(
            "a", string=lambda text: text and "Next" in text if text else False
        )
        if next_link:
            npage = utils.safe_get_attr(next_link, "href")

            # Find current page
            current = pagination.select_one(".current")
            currpg = utils.safe_get_text(current, "").strip() if current else ""

            # Find last page link
            last_link = pagination.find(
                "a", string=lambda text: text and "Last" in text if text else False
            )
            lastpg = ""
            if last_link:
                last_href = utils.safe_get_attr(last_link, "href")
                # Extract last page number from URL
                last_match = (
                    re.search(r"/(\\d+)/[^/]*$", last_href) if last_href else None
                )
                lastpg = last_match.group(1) if last_match else ""

            if npage:
                page_info = (
                    " (Currently in Page {0} of {1})".format(currpg, lastpg)
                    if currpg and lastpg
                    else ""
                )
                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR]" + page_info,
                    npage,
                    "List",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # Find all article elements with category items
    articles = soup.select("article")
    for article in articles:
        try:
            # Get category link
            link = article.select_one("a[href]")
            if not link:
                continue
            caturl = utils.safe_get_attr(link, "href")
            if not caturl:
                continue

            # Get image with lazy-src
            img_tag = article.select_one("img[data-lazy-src], img[src]")
            if not img_tag:
                continue
            img = utils.safe_get_attr(img_tag, "data-lazy-src", ["src"])

            # Get name from title element
            title_elem = article.select_one('.title, [class*="title"]')
            if not title_elem:
                continue
            name = utils.safe_get_text(title_elem, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            site.add_dir(name, caturl, "List", img)
        except Exception as e:
            utils.kodilog("javhdporn Cat: Error processing category - {}".format(e))
            continue

    # Pagination
    pagination = soup.select_one('.pagination, [class*="pagination"]')
    if pagination:
        # Find next link
        next_link = pagination.find(
            "a", string=lambda text: text and "Next" in text if text else False
        )
        if next_link:
            npage = utils.safe_get_attr(next_link, "href")

            # Find current page
            current = pagination.select_one(".current")
            currpg = utils.safe_get_text(current, "").strip() if current else ""

            # Find last page link
            last_link = pagination.find(
                "a", string=lambda text: text and "Last" in text if text else False
            )
            lastpg = ""
            if last_link:
                last_href = utils.safe_get_attr(last_link, "href")
                # Extract last page number from URL
                last_match = re.search(r"/(\\d+)/", last_href) if last_href else None
                lastpg = last_match.group(1) if last_match else ""

            if npage:
                page_info = (
                    " (Currently in Page {0} of {1})".format(currpg, lastpg)
                    if currpg and lastpg
                    else ""
                )
                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR]" + page_info,
                    npage,
                    "Cat",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = "{0}{1}/".format(url, keyword.replace(" ", "%20"))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    m = re.compile(
        r'video-id="([^"]+).+?(?:mpu-data|data-mpu)="([^"]+).+?data-ver="([^"]+)',
        re.DOTALL | re.IGNORECASE,
    ).search(videohtml)
    if m:
        pdata = {"sources": dex(m.group(1), m.group(2), m.group(3), True), "ver": 2}
        vp.progress.update(50, "[CR]Loading video page[CR]")
        hdr = utils.base_hdrs
        hdr.update({"Origin": site.url[:-1], "Referer": site.url})
        r = utils.postHtml(
            "https://video.javhdporn.net/api/play/", form_data=pdata, headers=hdr
        )
        jd = json.loads(r)
        eurl = dex(m.group(1), jd.get("data"), jd.get("ver"))
        eurl = "https:" + eurl if eurl.startswith("//") else eurl
        hdr.pop("Origin")
        vp.progress.update(75, "[CR]Loading embed page[CR]")
        try:
            r = utils.getHtml(eurl, headers=hdr)
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in javhdporn: " + str(e))
            vp.progress.close()
            return
        match = re.compile(r'data-fb5c9="([^"]+)', re.DOTALL | re.IGNORECASE).search(r)
        if match:
            purl = urllib_parse.urlsplit(eurl)
            key = utils._bencode(purl.path + "?" + purl.query)[8:24]
            ehost = urllib_parse.urljoin(eurl, "/")
            sources = json.loads(utils._bdecode(dex(key, match.group(1), "0", mtype=0)))
            sources = {x.get("label"): x.get("file") for x in sources}
            link = utils.selector(
                "Select quality",
                sources,
                sort_by=lambda x: int(x[:-1] if x[:-1].isdigit() else 0),
                reverse=True,
            )
            vp.play_from_direct_link(
                "{0}|Referer={1}&Origin={2}&User-Agent={3}".format(
                    link, ehost, ehost[:-1], utils.USER_AGENT
                )
            )
            return
    vp.progress.close()
    utils.notify("Oh oh", "No video found")
    return


def dex(key, data, dver, use_alt=False, mtype=1):
    part = "_0x58a0e3" if mtype == 0 else "_0x58fe15"
    if dver == "1" and use_alt:
        part = "QxLUF1bgIAdeQX"
    elif dver == "2":
        part = "SyntaxError"

    mid = utils._bencode(key + part)[::-1]
    x = 0
    ct = ""
    y = list(range(256))

    for r in range(256):
        x = (x + y[r] + ord(mid[r % len(mid)])) % 256
        y[r], y[x] = y[x], y[r]

    s = 0
    x = 0
    ddata = utils._bdecode(data, binary=True)
    for r, item in enumerate(ddata):
        s = (s + 1) % 256
        x = (x + y[s]) % 256
        y[s], y[x] = y[x], y[s]
        ct += chr(
            (item if isinstance(item, int) else ord(item)) ^ y[(y[s] + y[x]) % 256]
        )
    return utils._bdecode(ct)

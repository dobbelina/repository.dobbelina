"""
Cumination
Copyright (C) 2015 Whitecream

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
from urllib.parse import urljoin

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "poldertube",
    "[COLOR hotpink]Poldertube.nl[/COLOR] [COLOR orange](Dutch)[/COLOR]",
    "https://www.poldertube.nl/",
    "poldertube.png",
    "poldertube",
)
site2 = AdultSite(
    "sextube",
    "[COLOR hotpink]Sextube.nl[/COLOR] [COLOR orange](Dutch)[/COLOR]",
    "https://www.sextube.nl/",
    "sextube.png",
    "sextube",
)
site3 = AdultSite(
    "12milf",
    "[COLOR hotpink]12Milf[/COLOR] [COLOR orange](Dutch)[/COLOR]",
    "https://www.12milf.com/nl/",
    "12milf.png",
    "12milf",
)
site4 = AdultSite(
    "porntubenl",
    "[COLOR hotpink]PornTube.nl[/COLOR] [COLOR orange](Dutch)[/COLOR]",
    "https://www.porntube.nl/",
    "porntubenl.png",
    "porntubenl",
)


def getBaselink(url):
    if "poldertube.nl" in url:
        siteurl = "https://www.poldertube.nl/"
    elif "sextube.nl" in url:
        siteurl = "https://www.sextube.nl/"
    elif "12milf.com" in url:
        siteurl = "https://www.12milf.com/nl/"
    elif "porntube.nl" in url:
        siteurl = "https://www.porntube.nl/"
    return siteurl


@site.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
def NLTUBES(url):
    siteurl = getBaselink(url)
    if "12milf" not in siteurl:
        site.add_dir(
            "[COLOR hotpink]Categories[/COLOR]",
            siteurl + "categorieen/",
            "NLCAT",
            site.img_cat,
        )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", siteurl + "?s=", "NLSEARCH", site.img_search
    )
    NLVIDEOLIST(url + "?filter=latest")


@site.register()
def NLVIDEOLIST(url):
    siteurl = getBaselink(url)
    html = utils.getHtml(url, "")
    soup = utils.parse_html(html)

    if "poldertube" in siteurl or "12milf" in siteurl:
        cards = soup.select("article a[href][title]")
        for card in cards:
            surl = utils.safe_get_attr(card, "href")
            surl = surl if surl.startswith("http") else urljoin(siteurl, surl)
            name = utils.cleantext(utils.safe_get_attr(card, "title"))
            img_tag = card.select_one("img")
            img = utils.safe_get_attr(img_tag, "src", ["data-src", "data-lazy"])
            if img and img.startswith("//"):
                img = "https:" + img
            duration = utils.safe_get_text(
                card.select_one(".duration, .time"), default=""
            )
            site.add_download_link(
                name, surl, "NLPLAYVID", img, name, duration=duration
            )
        
        # Robust pagination
        nextp = soup.select_one(".pagination .current ~ a")
        if not nextp:
            # Fallback to general next link
            nextp = soup.select_one('.pagination a[href]:-soup-contains("Next"), .pagination a[href]:-soup-contains(">")')
            
        if nextp:
            next_url = utils.safe_get_attr(nextp, "href")
            next_url = (
                next_url if next_url.startswith("http") else urljoin(siteurl, next_url)
            )
            # Try to get page number from text or url
            page_text = utils.safe_get_text(nextp)
            if page_text.isdigit():
                page_nr = page_text
            else:
                match = re.search(r"page/(\d+)", next_url) or re.search(r"p=(\d+)", next_url)
                page_nr = match.group(1) if match else "Next"
                
            site.add_dir(
                "Next Page ({})".format(page_nr), next_url, "NLVIDEOLIST", site.img_next
            )
    else:
        cards = soup.select("[data-post-id]")
        for card in cards:
            link = card.select_one("a[href][title]")
            if not link:
                continue
            surl = utils.safe_get_attr(link, "href")
            surl = surl if surl.startswith("http") else urljoin(siteurl, surl)
            name = utils.cleantext(utils.safe_get_attr(link, "title"))
            img_tag = card.select_one("img")
            img = utils.safe_get_attr(img_tag, "data-src", ["src", "data-original"])
            duration = utils.safe_get_text(
                card.select_one(".duration, .time, .video-datas"), default=""
            )
            site.add_download_link(
                name, surl, "NLPLAYVID", img, name, duration=duration
            )
        nextp = soup.select_one("a.next.page-link")
        if nextp:
            next_url = utils.safe_get_attr(nextp, "href")
            next_url = (
                next_url if next_url.startswith("http") else urljoin(siteurl, next_url)
            )
            page_nr = "".join([c for c in next_url if c.isdigit()])
            site.add_dir(
                "Next Page ({})".format(page_nr), next_url, "NLVIDEOLIST", site.img_next
            )
    utils.eod()


@site.register()
def NLPLAYVID(url, name, download=None):
    siteurl = getBaselink(url)
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    hdr = utils.base_hdrs.copy()
    hdr["Cookie"] = "pageviews=1; postviews=1"
    videopage = utils.getHtml(url, siteurl, hdr)
    soup = utils.parse_html(videopage)
    meta = soup.find("meta", attrs={"property": "contentURL"}) or soup.find(
        "meta", attrs={"itemprop": "contentURL"}
    )
    videourl = utils.safe_get_attr(meta, "content") if meta else None
    if not videourl:

        matches = re.findall(
            r'contentURL"\s*content="([^"]+)"', videopage, re.IGNORECASE
        )
        videourl = matches[0] if matches else None
    if not videourl:
        vp.progress.close()
        return
    videourl = videourl + "|Referer={}".format(siteurl)
    vp.play_from_direct_link(videourl)


@site.register()
def NLSEARCH(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "NLSEARCH")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl + title
        NLVIDEOLIST(searchUrl)


@site.register()
def NLCAT(url):
    siteurl = getBaselink(url)
    link = utils.getHtml(url, "")
    soup = utils.parse_html(link)
    if "poldertube.nl" in siteurl:
        tags = soup.select("article a[href][title]")
        for cat in tags:
            caturl = utils.safe_get_attr(cat, "href")
            catimg = utils.safe_get_attr(
                cat.select_one("img"), "src", ["data-src", "data-original"]
            )
            catname = utils.safe_get_text(
                cat.select_one(".title, .name"),
                default=utils.safe_get_attr(cat, "title"),
            )
            catimg = catimg if catimg.startswith("http") else urljoin(siteurl, catimg)
            site.add_dir(catname, caturl, "NLVIDEOLIST", catimg)
    else:
        tags = soup.select(".video-block a[href][title]")
        for cat in tags:
            caturl = utils.safe_get_attr(cat, "href")
            catname = utils.safe_get_attr(cat, "title")
            catimg = utils.safe_get_attr(
                cat.select_one("img"), "src", ["data-src", "data-original"]
            )
            videos = utils.safe_get_text(
                cat.select_one(".video-datas, .count"), default=""
            )
            catname = catname.replace("sex films", "").replace(
                "porn videos", ""
            ) + "[COLOR hotpink] ({})[/COLOR]".format(videos)
            catimg = catimg if catimg.startswith("http") else urljoin(siteurl, catimg)
            site.add_dir(catname, caturl, "NLVIDEOLIST", catimg)
    utils.eod()

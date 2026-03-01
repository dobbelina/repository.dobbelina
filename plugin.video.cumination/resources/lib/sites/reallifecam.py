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
from resources.lib.jsunpack import unpack
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "rlc",
    "[COLOR hotpink]Reallifecam.to[/COLOR]",
    "https://reallifecam.to/",
    "rlc.png",
    "rlc",
)
site2 = AdultSite(
    "vhlife",
    "[COLOR hotpink]Voyeur-house.cc[/COLOR]",
    "https://www.voyeur-house.cc/",
    "vhlife.png",
    "vhlife",
)
site3 = AdultSite(
    "vhlife1",
    "[COLOR hotpink]Reallifecams[/COLOR]",
    "https://www.reallifecams.in/",
    "vhlife1.png",
    "vhlife1",
)
site4 = AdultSite(
    "camcaps",
    "[COLOR hotpink]Camcaps.tv (SimpVids)[/COLOR]",
    "https://camcaps.tv/",
    "camcaps.png",
    "camcapsto",
)


def getBaselink(url):
    if "reallifecam.to" in url:
        siteurl = site.url
    elif "voyeur-house.cc" in url:
        siteurl = site2.url
    elif "reallifecams." in url:
        # Use the actual domain from the URL if it's a reallifecams variant
        parsed = urlparse(url)
        siteurl = "{0}://{1}/".format(parsed.scheme, parsed.netloc)
    elif "camcaps.to" in url or "simpvids.com" in url or "camcaps.tv" in url:
        siteurl = site4.url
    else:
        parsed = urlparse(url)
        siteurl = "{0}://{1}/".format(parsed.scheme, parsed.netloc)
    return siteurl


@site.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        siteurl + "categories",
        "Categories",
        site.img_cat,
    )
    if "camcaps.to" in url or "simpvids.com" in url:
        site.add_dir(
            "[COLOR hotpink]Search[/COLOR]",
            siteurl + "search/videos/",
            "Search",
            site.img_search,
        )
    else:
        site.add_dir(
            "[COLOR hotpink]Search[/COLOR]",
            siteurl + "search/videos?search_query=",
            "Search",
            site.img_search,
        )
    List(siteurl + "videos?o=mr")


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, "")

    soup = utils.parse_html(listhtml)

    seen = set()
    cards = soup.select(".col-sm-6, .video-item, .item")
    for card in cards:
        link = card.select_one("a[href]")
        if not link:
            continue

        videopage = utils.safe_get_attr(link, "href")
        if not videopage:
            continue
        videopage = urllib_parse.urljoin(siteurl, videopage)
        if videopage in seen:
            continue
        seen.add(videopage)

        # Try to get title from content-title span (for simpvids.com/camcaps.to)
        name = ""
        title_tag = card.select_one(".content-title")
        if title_tag:
            name = utils.safe_get_text(title_tag)

        # Fallback to other common title locations
        if not name:
            name = utils.safe_get_attr(link, "title")
        if not name:
            title_tag = card.select_one(".title-truncate, .title, h3, h4")
            name = utils.safe_get_text(title_tag)
        if not name:
            # Try img alt attribute
            img_tag = card.select_one("img[alt]")
            if img_tag:
                name = utils.safe_get_attr(img_tag, "alt")

        name = utils.cleantext(name)
        if name.replace(":", "").isdigit():
            name = "Video"
        if not name:
            name = "Video"

        img_tag = card.select_one("img[data-src], img[data-original], img[src]")
        img = (
            utils.safe_get_attr(img_tag, "data-src", ["data-original", "src"])
            if img_tag
            else None
        )
        if img and img.startswith("//"):
            img = "https:" + img
        elif img and img.startswith("/"):
            img = urllib_parse.urljoin(siteurl, img)

        duration_tag = card.select_one(
            ".duration, .time, .video-duration, .clock, .label-duration"
        )
        duration = utils.safe_get_text(duration_tag)

        hd = ""
        quality_tag = card.select_one(".badge, .label, .quality, .hd, .label-hd")
        if quality_tag and "HD" in quality_tag.get_text().upper():
            hd = "HD"

        site.add_download_link(
            name, videopage, "Playvid", img, name, duration=duration, quality=hd
        )

    next_link = soup.select_one(
        'a.prevnext[href], .pagination li.next a, a[rel="next"]'
    )
    if next_link:
        next_page = utils.safe_get_attr(next_link, "href")
        if next_page:
            next_page = urllib_parse.urljoin(siteurl, next_page)
            page_nr = ""
            match = re.findall(r"\d+", next_page)
            if match:
                page_nr = match[-1]
            label = "Next Page ({})".format(page_nr) if page_nr else "Next Page"
            site.add_dir(label, next_page, "List", site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "%20")
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, "")
    soup = utils.parse_html(cathtml)

    seen = set()
    containers = soup.select(
        ".col-sm, .col-sm-6, .category, .category-item, .list-group-item"
    )
    for container in containers:
        link = container.select_one("a[href]")
        if not link:
            continue

        catpage = utils.safe_get_attr(link, "href")
        if not catpage:
            continue
        catpage = urllib_parse.urljoin(siteurl, catpage)
        if catpage in seen:
            continue
        seen.add(catpage)

        img_tag = container.select_one("img[data-src], img[data-original], img[src]")
        img = (
            utils.safe_get_attr(img_tag, "data-src", ["data-original", "src"])
            if img_tag
            else site.img_cat
        )
        if img and img.startswith("//"):
            img = "https:" + img
        elif img and img.startswith("/"):
            img = urllib_parse.urljoin(siteurl, img)

        name_tag = container.select_one(".title-truncate, .title, h4, h3, .name")
        if name_tag:
            name = utils.safe_get_text(name_tag)
        else:
            name = utils.safe_get_attr(link, "title")
            if not name:
                name = utils.safe_get_text(link)
        name = utils.cleantext(name.strip()).title()
        if not name:
            name = "Category"

        count_tag = container.select_one(
            ".badge, .float-right, .videos, .video-count, .count"
        )
        videos = utils.safe_get_text(count_tag)
        if videos:
            name = name + " [COLOR deeppink]" + videos + "[/COLOR]"

        site.add_dir(name, catpage, "List", img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)

    soup = utils.parse_html(videopage)

    # Find ALL iframes and filter out ads
    iframes = soup.select(".video-embedded iframe, iframe[src]")
    refurl = None
    for iframe in iframes:
        src = utils.safe_get_attr(iframe, "src")
        if src and "a-ads.com" not in src:
            refurl = src
            break

    if refurl:
        if refurl.startswith("//"):
            refurl = "https:" + refurl
        elif refurl.startswith("/"):
            refurl = urllib_parse.urljoin(url, refurl)

        # Handle camcaps.tv / camcaps.to / simpvids.com which often lead to vidello
        if "vidello.net" in refurl or "camcaps.tv" in refurl:
            # If it's a camcaps.tv embed, it might contain another iframe for vidello
            if "camcaps.tv/embed/" in refurl:
                embed_page = utils.getHtml(refurl)
                embed_soup = utils.parse_html(embed_page)
                vidello_iframe = embed_soup.select_one('iframe[src*="vidello.net"]')
                if vidello_iframe:
                    refurl = utils.safe_get_attr(vidello_iframe, "src")

            # Extract video ID from vidello: https://vidello.net/embed-e14kle5qmavq.html
            # To construct clean URL: https://vidello.net/e14kle5qmavq.html
            video_id_match = re.search(
                r"vidello\.net/(?:embed-)?([^/]+)\.html", refurl
            )
            if video_id_match:
                video_id = video_id_match.group(1)
                vidello_url = "https://vidello.net/{}.html".format(video_id)
                if vp.resolveurl.HostedMediaFile(vidello_url):
                    vp.play_from_link_to_resolve(vidello_url)
                    return

        if "/vtplayer.net/" in refurl:
            refurl = refurl.replace("embed-", "")

        if vp.resolveurl.HostedMediaFile(refurl):
            vp.play_from_link_to_resolve(refurl)
            return

        refpage = utils.getHtml(refurl)
        if "/playerz/" in refurl:
            videourl = re.compile(
                r'"src":"\.([^"]+)"', re.DOTALL | re.IGNORECASE
            ).findall(refpage)[0]
            videourl = refurl.split("/ss.php")[0] + videourl
            videourlpage = utils.getHtml(videourl)
            vp.direct_regex = '{"file":"([^"]+)"'
            vp.play_from_html(videourlpage)
        else:
            # More flexible packed script detection (handles cases without > before eval)
            packed_match = re.compile(
                r"(eval\s*\(function\(p,a,c,k,e,d\).+?)\s*<\/script>", 
                re.DOTALL | re.IGNORECASE
            ).findall(refpage)
            
            if packed_match:
                videourl = unpack(packed_match[0])
                videolink = re.compile(
                    '(?:src|file):"([^"]+)"', re.DOTALL | re.IGNORECASE
                ).findall(videourl)
                if videolink:
                    videolink = videolink[0] + "|Referer=" + refurl + "&verifypeer=false"
                    if videolink.startswith("/") and "vidello" in refurl:
                        videolink = "https://oracle.vidello.net" + videolink
                    vp.play_from_direct_link(videolink)
                    return
            
            # If not packed, look for direct file/src links in the iframe page
            videolinks = re.compile(
                r'(?:src|file)\s*:\s*"([^"]+?\.m3u8[^"]*)"', 
                re.IGNORECASE
            ).findall(refpage)
            if not videolinks:
                videolinks = re.compile(
                    r'(?:src|file)\s*:\s*"([^"]+?\.mp4[^"]*)"', 
                    re.IGNORECASE
                ).findall(refpage)
            
            if videolinks:
                videolink = videolinks[0]
                if videolink.startswith("//"):
                    videolink = "https:" + videolink
                elif videolink.startswith("/"):
                    videolink = urllib_parse.urljoin(refurl, videolink)
                
                videolink = videolink + "|Referer=" + refurl + "&verifypeer=false"
                vp.play_from_direct_link(videolink)
                return

    # Fallback to direct page scraping
    vp.play_from_html(videopage)

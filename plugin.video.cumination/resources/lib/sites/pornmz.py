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

import xbmc
from resources.lib import utils
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "pornmz",
    "[COLOR hotpink]Pornmz[/COLOR]",
    "https://pornmz.com/",
    "pornmz.png",
    "pornmz",
)

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]", site.url + "tags/", "Tags", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Best[/COLOR]",
        site.url + "page/1?filter=popular",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Most Viewed[/COLOR]",
        site.url + "page/1?filter=most-viewed",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Longest[/COLOR]",
        site.url + "page/1?filter=longest",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url + "page/1?filter=latest")


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    cm = []
    cm_lookupinfo = utils.addon_sys + "?mode=pornmz.Lookupinfo&url="
    cm.append(
        ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + cm_lookupinfo + ")")
    )
    cm_related = utils.addon_sys + "?mode=pornmz.Related&url="
    cm.append(
        ("[COLOR deeppink]Related videos[/COLOR]", "RunPlugin(" + cm_related + ")")
    )

    # Find all video articles
    articles = soup.select("article[data-video-id]")
    if not articles:
        # Fallback to any article or div that looks like a video container
        articles = soup.select("article, .video-item, .item")

    for article in articles:
        try:
            # Get video link
            link = article.select_one('a[href*="/video/"]') or article.select_one("a[href]")
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            if not videopage or "/video/" not in videopage:
                continue

            # Ensure absolute URL
            if videopage.startswith("/"):
                videopage = site.url[:-1] + videopage
            elif not videopage.startswith("http"):
                videopage = site.url + videopage

            name = utils.safe_get_attr(link, "title")
            if not name:
                name = utils.safe_get_text(link, "").strip()
            if not name and videopage:
                slug = videopage.rstrip("/").split("/")[-1]
                name = slug
            name = utils.cleantext(name)

            # Get image - check img src, img data-src, or poster attribute
            img = ""
            img_tag = article.select_one("img")
            if img_tag:
                img = utils.safe_get_attr(img_tag, "src", ["data-src"])
            if not img:
                # Check for poster attribute on video tag
                video_tag = article.select_one("video[poster]")
                if video_tag:
                    img = utils.safe_get_attr(video_tag, "poster")

            # Get duration
            duration_tag = article.select_one(".duration")
            duration = (
                utils.safe_get_text(duration_tag, "").strip() if duration_tag else ""
            )

            # Check for HD quality
            hd = "HD" if "HD" in article.get_text().upper() else ""

            site.add_download_link(
                name,
                videopage,
                "Play",
                img,
                name,
                duration=duration,
                quality=hd,
                contextm=cm,
            )
        except Exception as e:
            utils.kodilog("pornmz List: Error processing video - {}".format(e))
            continue

    # Pagination - find current page and next inactive link
    pagination_container = soup.select_one(".pagination")
    if pagination_container:
        current = pagination_container.select_one(".current")
        next_link = (
            current.find_next("a") if current else pagination_container.select_one("a")
        )
        if next_link:
            next_url = utils.safe_get_attr(next_link, "href")
            next_page = utils.safe_get_text(next_link, "").strip()
            if next_url and next_page:
                site.add_dir(
                    "Next Page... ({0})".format(next_page),
                    next_url,
                    "List",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Categories(url):
    while True:
        cathtml = utils.getHtml(url, site.url)
        soup = utils.parse_html(cathtml)

        # Find all category articles
        articles = soup.select("article")
        for article in articles:
            try:
                link = article.select_one("a[href][title]")
                if not link:
                    continue

                sitepage = utils.safe_get_attr(link, "href")
                if not sitepage:
                    continue

                name = utils.safe_get_attr(link, "title")
                name = utils.cleantext(name)
                if not name:
                    continue

                # Get image
                img_tag = article.select_one("img[src]")
                img = (
                    utils.safe_get_attr(img_tag, "src", ["data-src"]) if img_tag else ""
                )

                siteurl = sitepage + "/page/1?filter=latest"
                site.add_dir(name, siteurl, "List", img)
            except Exception as e:
                utils.kodilog("pornmz Categories: Error processing category - {}".format(e))
                continue

        # Check for next page - find current page, then next link
        pagination = soup.select(".pagination a, .pagination li")
        next_url = None
        current_found = False
        for item in pagination:
            if "current" in utils.safe_get_attr(item, "class", default=""):
                current_found = True
            elif current_found:
                # Next item after current should be the next page
                next_link = item if item.name == "a" else item.select_one("a")
                if next_link:
                    next_url = utils.safe_get_attr(next_link, "href")
                break

        if next_url:
            url = next_url
        else:
            break

    utils.eod()


@site.register()
def Tags(url):
    taghtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(taghtml)

    # Find all tag items
    tag_items = soup.select(".tag-item a[href]")
    for link in tag_items:
        try:
            tagpage = utils.safe_get_attr(link, "href")
            if not tagpage:
                continue

            name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            tagpage = tagpage + "/page/1?filter=latest"
            site.add_dir(name, tagpage, "List", "")
        except Exception as e:
            utils.kodilog("pornmz Tags: Error processing tag - {}".format(e))
            continue

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url += keyword.replace(" ", "+")
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url)
    soup = utils.parse_html(html)

    # Find iframe
    iframe_tag = soup.select_one("iframe[src]")
    if iframe_tag:
        iframe = utils.safe_get_attr(iframe_tag, "src")
        if iframe:
            html = utils.getHtml(iframe, site.url)
            iframe_soup = utils.parse_html(html)

            # Find video source
            source_tag = iframe_soup.select_one("source[src]")
            if source_tag:
                videourl = utils.safe_get_attr(source_tag, "src")
                if videourl:
                    videourl = videourl + "|Referer={}".format(site.url)
                    vp.play_from_direct_link(videourl)
                    return

    utils.notify("Oh oh", "No video found")


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("pornmz.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'href="([^"]+)"[^>]+><i class="fa\s+fa-folder"></i>([^<]+)<', ""),
        ("Pornstar", r'href="([^"]+)"[^>]+><i class="fa\s+fa-star"></i>([^<]+)<', ""),
        ("Tag", r'href="([^"]+)"[^>]+><i class="fa\s+fa-tag"></i>([^<]+)<', ""),
    ]

    lookupinfo = utils.LookupInfo("", url, "pornmz.List", lookup_list)
    lookupinfo.getinfo()

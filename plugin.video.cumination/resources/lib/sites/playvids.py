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

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "playvids",
    "[COLOR hotpink]PlayVids[/COLOR]",
    "https://www.playvids.com/",
    "playvids.png",
    "playvids",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories",
        "Cat",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Channels[/COLOR]",
        site.url + "channels?page=1",
        "Channels",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]",
        site.url + "pornstars?page=1",
        "Pornstars",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Trending[/COLOR]",
        site.url + "Trending-Porn",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "videos?q=",
        "Search",
        site.img_search,
    )
    List(site.url + "?page=1")

    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    # Remove carousel sections
    for carousel in soup.select(".item-carousel"):
        carousel.decompose()

    items = soup.select(".card.thumbs, .card")
    for item in items:
        try:
            img_tag = item.select_one("img")
            img = utils.get_thumbnail(img_tag)

            info_section = item.select_one(".info")
            if not info_section:
                continue

            duration_tag = info_section.select_one(".duration")
            duration = utils.safe_get_text(duration_tag, "")

            title_tag = info_section.select_one(".title")
            link = title_tag.select_one("a") if title_tag else None
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                name = utils.safe_get_attr(link, "title")
            name = utils.cleantext(name)

            # Check for HD badge
            hd = (
                "HD"
                if info_section.select_one('.badge:-soup-contains("HD")')
                or ">HD<" in str(info_section)
                else ""
            )

            if videopage.startswith("/"):
                videopage = site.url[:-1] + videopage

            site.add_download_link(
                name,
                videopage,
                "Playvid",
                img,
                name,
                noDownload=True,
                duration=duration,
                quality=hd,
            )
        except Exception as e:
            utils.kodilog("playvids List: Error processing item - {}".format(e))
            continue

    # Pagination
    next_link = soup.select_one("li a.next[href]")
    if next_link:
        nextp = utils.safe_get_attr(next_link, "href")
        if nextp:
            if nextp.startswith("/"):
                nextp = site.url[:-1] + nextp
            page_num = nextp.split("=")[-1] if "=" in nextp else ""
            site.add_dir(
                "Next Page... ({0})".format(page_num), nextp, "List", site.img_next
            )

    utils.eod()


@site.register()
def PList(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    # Remove carousel sections
    for carousel in soup.select(".item-carousel"):
        carousel.decompose()

    items = soup.select(".card.thumbs, .card")
    for item in items:
        try:
            img_tag = item.select_one("img")
            img = utils.get_thumbnail(img_tag)

            info_section = item.select_one(".info")
            if not info_section:
                continue

            duration_tag = info_section.select_one(".duration")
            duration = utils.safe_get_text(duration_tag, "")

            title_tag = info_section.select_one(".title")
            link = title_tag.select_one("a") if title_tag else None
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                name = utils.safe_get_attr(link, "title")
            name = utils.cleantext(name)

            # Check for HD badge
            hd = (
                "HD"
                if info_section.select_one('.badge:-soup-contains("HD")')
                or ">HD<" in str(info_section)
                else ""
            )

            if videopage.startswith("/"):
                videopage = site.url[:-1] + videopage

            site.add_download_link(
                name,
                videopage,
                "Playvid",
                img,
                name,
                noDownload=True,
                duration=duration,
                quality=hd,
            )
        except Exception as e:
            utils.kodilog("playvids PList: Error processing item - {}".format(e))
            continue

    # Pagination
    next_link = soup.select_one("li a.next[href]")
    if next_link:
        nextp = utils.safe_get_attr(next_link, "href")
        if nextp:
            if nextp.startswith("/"):
                nextp = site.url[:-1] + nextp
            page_num = nextp.split("=")[-1] if "=" in nextp else ""
            site.add_dir(
                "Next Page... ({0})".format(page_num), nextp, "PList", site.img_next
            )

    utils.eod()


@site.register()
def CList(url, page=1):
    listhtml = utils.getHtml(url + "?page={0}".format(page), site.url)
    soup = utils.parse_html(listhtml)

    items = soup.select('[id^="row_item"]')
    for item in items:
        try:
            img_tag = item.select_one("img")
            img = utils.get_thumbnail(img_tag)

            info_section = item.select_one(".info")
            if not info_section:
                continue

            duration_tag = info_section.select_one(".duration")
            duration = utils.safe_get_text(duration_tag, "")

            title_tag = info_section.select_one(".title")
            link = title_tag.select_one("a") if title_tag else None
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                name = utils.safe_get_attr(link, "title")
            name = utils.cleantext(name)

            # Check for HD badge
            hd = (
                "HD"
                if info_section.select_one('.badge:-soup-contains("HD")')
                or ">HD<" in str(info_section)
                else ""
            )

            if videopage.startswith("/"):
                videopage = site.url[:-1] + videopage

            site.add_download_link(
                name,
                videopage,
                "Playvid",
                img,
                name,
                noDownload=True,
                duration=duration,
                quality=hd,
            )
        except Exception as e:
            utils.kodilog("playvids CList: Error processing item - {}".format(e))
            continue

    # Check for "show more" button
    show_more = soup.select_one("#channel_show_more")
    if show_more:
        page = page + 1
        site.add_dir(
            "Next Page... ({0})".format(page), url, "CList", site.img_next, page=page
        )

    utils.eod()


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    # Find category links within list items
    cat_items = soup.select("li a[href]")
    for link in cat_items:
        try:
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                continue

            if catpage.startswith("/"):
                catpage = site.url[:-1] + catpage

            site.add_dir(name, catpage, "List", "")
        except Exception as e:
            utils.kodilog("playvids Cat: Error processing category - {}".format(e))
            continue

    utils.eod()


@site.register()
def Channels(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    items = soup.select(".card")
    for item in items:
        try:
            # Look for channel-specific content
            channel_section = item.select_one(".channel")
            if not channel_section:
                continue

            img_tag = item.select_one("img")
            img = utils.get_thumbnail(img_tag)

            title_section = item.select_one(".title")
            if not title_section:
                continue

            link = title_section.select_one("a[href]")
            if not link:
                continue

            chpage = utils.safe_get_attr(link, "href")
            if not chpage:
                continue

            name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)

            # Get video count
            videos_tag = item.select_one(".videos")
            vids = utils.safe_get_text(videos_tag, "").strip()
            if vids:
                name += " [COLOR hotpink]{0}[/COLOR]".format(vids)

            if chpage.startswith("/"):
                chpage = site.url[:-1] + chpage

            site.add_dir(name, chpage, "CList", img, page=1)
        except Exception as e:
            utils.kodilog("playvids Channels: Error processing channel - {}".format(e))
            continue

    # Pagination
    next_link = soup.select_one("li a.next[href]")
    if next_link:
        nextp = utils.safe_get_attr(next_link, "href")
        if nextp:
            if nextp.startswith("/"):
                nextp = site.url[:-1] + nextp
            page_num = nextp.split("=")[-1] if "=" in nextp else ""
            site.add_dir(
                "Next Page... ({0})".format(page_num), nextp, "Channels", site.img_next
            )

    utils.eod()


@site.register()
def Pornstars(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    items = soup.select("li.overflow")
    for item in items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            chpage = utils.safe_get_attr(link, "href")
            if not chpage:
                continue

            # Try to get image (some pornstars may not have one)
            img_tag = item.select_one("img")
            img = utils.safe_get_attr(img_tag, "src", ["data-src"]) if img_tag else ""

            name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            if chpage.startswith("/"):
                chpage = site.url[:-1] + chpage

            site.add_dir(name, chpage, "PList", img)
        except Exception as e:
            utils.kodilog("playvids Pornstars: Error processing pornstar - {}".format(e))
            continue

    # Pagination
    next_link = soup.select_one("li a.next[href]")
    if next_link:
        nextp = utils.safe_get_attr(next_link, "href")
        if nextp:
            if nextp.startswith("/"):
                nextp = site.url[:-1] + nextp
            page_num = nextp.split("=")[-1] if "=" in nextp else ""
            site.add_dir(
                "Next Page... ({0})".format(page_num), nextp, "Pornstars", site.img_next
            )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = "{0}{1}".format(url, keyword.replace(" ", "+"))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    soup = utils.parse_html(videopage)

    # Find video source tags
    source_tags = soup.select("source[src]")
    sources = []
    for source in source_tags:
        src = utils.safe_get_attr(source, "src")
        if src:
            sources.append(src)

    if sources:
        vidurl = utils.prefquality(sources, reverse=True)
        vp.play_from_direct_link(vidurl.replace("&amp;", "&"))
    else:
        vp.progress.close()
        utils.notify("Oh oh", "No video found")

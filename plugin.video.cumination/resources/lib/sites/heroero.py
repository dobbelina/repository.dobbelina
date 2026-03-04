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
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
from kodi_six import xbmcgui, xbmcplugin

site = AdultSite(
    "heroero",
    "[COLOR hotpink]Heroero[/COLOR]",
    "https://heroero.com/",
    "heroero.png",
    "heroero",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_search,
    )
    site.add_dir(
        "[COLOR hotpink]Actress[/COLOR]",
        site.url + "actress/",
        "Categories",
        site.img_search,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url
        + "see/{}/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&q={}&category_ids=&sort_by=&from_videos=1&from_albums=1",
        "Search",
        site.img_search,
    )

    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    if not soup:
        utils.eod()
        return

    # Find all video items (class contains 'item' and whitespace)
    items = soup.find_all("div", class_="item")

    for item in items:
        link = item.find("a", href=True, title=True)
        if not link:
            continue

        videourl = utils.safe_get_attr(link, "href")
        name = utils.safe_get_attr(link, "title")

        if not videourl or not name:
            continue

        name = utils.cleantext(name)

        # Get thumbnail
        img_tag = link.find("img")
        img = utils.safe_get_attr(img_tag, "data-original", fallback_attrs=["src"])

        # Check for HD quality
        hd_badge = item.find("div", class_="hd-badge")
        quality = "HD" if hd_badge else ""

        # Create context menu
        contextmenu = []
        contexturl = (
            utils.addon_sys
            + "?mode="
            + str("heroero.Related")
            + "&url="
            + urllib_parse.quote_plus(videourl)
        )
        contextmenu.append(
            ("[COLOR deeppink]Related Videos[/COLOR]", "RunPlugin(" + contexturl + ")")
        )

        site.add_download_link(
            name, videourl, "Playvid", img, name, contextm=contextmenu, quality=quality
        )

    # Handle pagination
    if "?" in url:
        # Search results pagination
        pagination = soup.find("div", class_="pagination")
        if pagination:
            next_link = pagination.find("a", string=re.compile("Next", re.IGNORECASE))
            if next_link:
                next_text = utils.safe_get_text(next_link)
                npage_match = re.search(r"\d+", next_text)
                npage = int(npage_match.group(0)) if npage_match else None

                if npage:
                    last_link = pagination.find(
                        "a", string=re.compile("Last", re.IGNORECASE)
                    )
                    lastp = ""
                    if last_link:
                        last_text = utils.safe_get_text(last_link)
                        last_match = re.search(r"\d+", last_text)
                        lastp = "/" + last_match.group(0) if last_match else ""

                    nurl = re.sub(
                        r"([&?])from([^=]*)=(\d+)", r"\1from\2={0:02d}", url
                    ).format(npage)
                    site.add_dir(
                        "[COLOR hotpink]Next Page...[/COLOR] ("
                        + str(npage)
                        + lastp
                        + ")",
                        nurl,
                        "List",
                        site.img_next,
                        npage,
                    )
    else:
        # Regular pagination
        pagination = soup.find("div", class_="pagination")
        if pagination:
            next_link = pagination.find("a", class_="next")
            if next_link:
                next_url = utils.safe_get_attr(next_link, "href")
                if next_url:
                    # Extract page numbers
                    page_match = re.search(r"/(\d+)/", next_url)
                    page_num = page_match.group(1) if page_match else ""

                    last_link = pagination.find("a", class_="last")
                    last_page = ""
                    if last_link:
                        last_url = utils.safe_get_attr(last_link, "href")
                        last_match = re.search(r"/(\d+)/", last_url)
                        last_page = last_match.group(1) if last_match else ""

                    # Add next page with goto context menu
                    contextmenu = []
                    if page_num and last_page:
                        contexturl = (
                            utils.addon_sys
                            + "?mode=heroero.GotoPage"
                            + "&list_mode=heroero.List"
                            + "&url="
                            + urllib_parse.quote_plus(url)
                            + "&np="
                            + page_num
                            + "&lp="
                            + last_page
                        )
                        contextmenu.append(
                            (
                                "[COLOR violet]Goto Page[/COLOR]",
                                "RunPlugin(" + contexturl + ")",
                            )
                        )

                    site.add_dir(
                        "[COLOR hotpink]Next Page...[/COLOR]",
                        next_url,
                        "List",
                        site.img_next,
                        contextm=contextmenu,
                    )

    utils.eod()


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("heroero.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "-")
        searchUrl = url.format(title, title)
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    if not soup:
        utils.eod()
        return

    # Find all category/actress items
    items = soup.find_all("a", class_="item", href=True, title=True)

    for item in items:
        caturl = utils.safe_get_attr(item, "href")
        name = utils.safe_get_attr(item, "title")

        if not caturl or not name:
            continue

        name = utils.cleantext(name)

        # Capitalize category names
        if "/categories/" in url:
            name = name.capitalize()

        # Get thumbnail (may be missing for some categories)
        img_tag = item.find("img")
        img = utils.safe_get_attr(img_tag, "src", default="")
        if img:
            img = img.replace(" ", "%20")

        # Get video count if available
        videos_div = item.find("div", class_="videos")
        if videos_div:
            video_count = utils.safe_get_text(videos_div, default="")
            if video_count:
                name = name + " [COLOR cyan][{}][/COLOR]".format(video_count)

        site.add_dir(name, caturl, "List", img)

    # Handle pagination
    pagination = soup.find("div", class_="pagination")
    if pagination:
        next_link = pagination.find("a", class_="next")
        if next_link:
            next_url = utils.safe_get_attr(next_link, "href")
            if next_url:
                # Extract page numbers
                page_match = re.search(r"/(\d+)/", next_url)
                page_num = page_match.group(1) if page_match else ""

                last_link = pagination.find("a", class_="last")
                last_page = ""
                if last_link:
                    last_url = utils.safe_get_attr(last_link, "href")
                    last_match = re.search(r"/(\d+)/", last_url)
                    last_page = last_match.group(1) if last_match else ""

                # Add next page with goto context menu
                contextmenu = []
                if page_num and last_page:
                    contexturl = (
                        utils.addon_sys
                        + "?mode=heroero.GotoPage"
                        + "&list_mode=heroero.Categories"
                        + "&url="
                        + urllib_parse.quote_plus(url)
                        + "&np="
                        + page_num
                        + "&lp="
                        + last_page
                    )
                    contextmenu.append(
                        (
                            "[COLOR violet]Goto Page[/COLOR]",
                            "RunPlugin(" + contexturl + ")",
                        )
                    )

                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR]",
                    next_url,
                    "Categories",
                    site.img_next,
                    contextm=contextmenu,
                )

    if "/categories/" in url:
        xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    def ssut51(arg):
        digits = re.sub(r"[\D]", "", str(arg))
        return sum(int(c) for c in digits)

    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, site.url)

    match = re.compile(
        r"videoFormats\.push\(\{title:'([^']+)',file_name:'([^']+)',w:'(\d+)',h:'(\d+)'",
        re.IGNORECASE | re.DOTALL,
    ).findall(vpage)
    if not match:
        match = re.compile(
            r'<iframe.+?src="([^"]+embed[^"]+)"', re.IGNORECASE | re.DOTALL
        ).findall(vpage)
        if match:
            url = match[0]
            if url.startswith("//"):
                url = "https:" + url
            vpage = utils.getHtml(url, site.url)
            match = re.compile(
                r"videoFormats\.push\(\{title:'([^']+)',file_name:'([^']+)',w:'(\d+)',h:'(\d+)'",
                re.IGNORECASE | re.DOTALL,
            ).findall(vpage)

    if match:
        formats = {str(m[3]) + "p": m[1] for m in match}
        format = utils.prefquality(formats, sort_by=lambda x: int(x[:-1]), reverse=True)
        if format:
            video_id = url.split("/")[4].split("?")[0]
            s = "0" if len(video_id) < 4 else video_id[:-3] + "000"
            videourl = "https://media.heroero.com/contents/videos/{}/{}/{}".format(
                s, video_id, format
            )
            vp.play_from_direct_link(videourl + "|Referer={}".format(site.url))
            return

    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)
    else:
        utils.notify(msg="Video URL not found!")
        vp.progress.close()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        if url.endswith("/{}/".format(np)):
            url = url.replace("/{}/".format(np), "/{}/".format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg="Out of range!")
            return
        contexturl = (
            utils.addon_sys
            + "?mode="
            + str(list_mode)
            + "&url="
            + urllib_parse.quote_plus(url)
        )
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")

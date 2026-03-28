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
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite(
    "tubxporn",
    "[COLOR hotpink]TubXporn[/COLOR]",
    "https://web.tubxporn.com/",
    "tubxporn.png",
    "tubxporn",
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
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/?q=",
        "Search",
        site.img_search,
    )
    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    headers = {"User-Agent": utils.USER_AGENT, "Referer": site.url}
    try:
        html = utils.getHtml(url, site.url, headers=headers)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in tubxporn: " + str(e))
        # Fallback with a potential bypass parameter
        fallback_url = url + ("?" if "?" not in url else "&") + "label_W9dmamG9w9zZg45g93FnLAVbSyd0bBDv=1"
        html = utils.getHtml(fallback_url, site.url, headers=headers)
    if "There are no videos in the list" in html:
        utils.notify(msg="Nothing found")
        utils.eod()
        return

    soup = utils.parse_html(html)
    if not soup:
        utils.eod()
        return

    for inner in soup.select(".inner"):
        link = inner.select_one("a[href][title]")
        if not link:
            continue

        videopage = utils.safe_get_attr(link, "href", default="")
        # Skip rexporn.com links
        if "www.rexporn.com" in videopage:
            continue

        name = utils.cleantext(utils.safe_get_attr(link, "title", default=""))
        img_tag = inner.select_one("img")
        img = utils.get_thumbnail(img_tag)
        if img and not img.startswith("http"):
            img = "https:" + img

        duration_elem = inner.select_one(".length")
        duration = utils.safe_get_text(duration_elem, default="")

        if videopage and name:
            site.add_download_link(
                name,
                videopage,
                "tubxporn.Playvid",
                img,
                name,
                duration=duration,
                contextm="tubxporn.Related",
            )

    # Pagination
    next_link = soup.select_one("a.mobnav[href]")
    if next_link and "Next" in utils.safe_get_text(next_link, default=""):
        next_url = utils.safe_get_attr(next_link, "href", default="")
        if next_url:
            # Extract page number from next URL
            np_match = re.search(r"/(\d+)(?:/\?|/)", next_url)
            np = np_match.group(1) if np_match else ""

            # Find last page number
            lp = ""
            for page_link in soup.select("a[href]"):
                page_text = utils.safe_get_text(page_link, default="")
                if page_text.isdigit():
                    lp = max(lp, page_text) if lp else page_text

            contextmenu = []
            if np and lp:
                baseurl = (
                    url.split("page")[0] if "page" in url else url.rstrip("/") + "/"
                )
                contexturl = (
                    utils.addon_sys
                    + "?mode=tubxporn.GotoPage"
                    + "&list_mode=tubxporn.List"
                    + "&url="
                    + urllib_parse.quote_plus(baseurl)
                    + "&np="
                    + np
                    + "&lp="
                    + lp
                )
                contextmenu.append(
                    ("[COLOR violet]Goto Page[/COLOR]", "RunPlugin(" + contexturl + ")")
                )

            label = "Next Page"
            if np and lp:
                label += f" ({np}/{lp})"
            elif np:
                label += f" ({np})"
            site.add_dir(
                label, next_url, "tubxporn.List", site.img_next, contextm=contextmenu
            )

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
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


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys + "?mode=tubxporn.List&url=" + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        search_url = url if "q=" in url else site.url + "search/?q="
        site.search_dir(search_url, "Search")
    else:
        base_url = url if "q=" in url else site.url + "search/?q="
        url = "{0}{1}".format(base_url, keyword.replace(" ", "%20"))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)
    if not soup:
        utils.eod()
        return

    for item in soup.select(".item"):
        link = item.select_one("a[href]")
        if not link:
            continue

        caturl = utils.safe_get_attr(link, "href", default="")
        img_tag = item.select_one("img")
        img = utils.get_thumbnail(img_tag)

        h2 = item.select_one("h2")
        if h2:
            # Extract name and count from h2 text (e.g., "Category Name (123)")
            full_text = utils.safe_get_text(h2, default="")
            count_match = re.search(r"\((\d+)\)", full_text)
            count = count_match.group(1) if count_match else ""
            name = re.sub(r"\s*\(\d+\)\s*$", "", full_text)
            name = utils.cleantext(name)
            if count:
                name = name + "[COLOR hotpink] ({} videos)[/COLOR]".format(count)
        else:
            name = utils.cleantext(utils.safe_get_text(link, default=""))

        if caturl and name:
            site.add_dir(name, caturl, "List", img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        videohtml = utils.getHtml(url, site.url)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in tubxporn: " + str(e))
        videohtml = utils._getHtml(
            url + "?label_W9dmamG9w9zZg45g93FnLAVbSyd0bBDv=1", site.url
        )

    match = re.compile(
        r'div data-c="([^"]+)">\D+(\d+p)<', re.IGNORECASE | re.DOTALL
    ).findall(videohtml)
    if match:
        sources = {x[1]: x[0] for x in match}
        videolink = utils.prefquality(
            sources, sort_by=lambda x: int(x[:-1]), reverse=True
        )
        videolink = videolink.split(";")
        videourl = "https://{0}.vstor.top/whpvid/{1}/{2}/{3}/{4}/{4}_{5}.mp4".format(
            videolink[7],
            videolink[5],
            videolink[6],
            videolink[4][:-3] + "000",
            videolink[4],
            videolink[1],
        )
        videourl = videourl.replace("_720p", "")
        vp.play_from_direct_link(videourl)

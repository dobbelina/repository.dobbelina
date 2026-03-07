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
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite
import xbmc
from six.moves import urllib_parse
from kodi_six import xbmcgui, xbmcplugin

site = AdultSite(
    "kissjav",
    "[COLOR hotpink]Kiss JAV[/COLOR]",
    "https://kissjav.com/",
    "kissjav.png",
    "kissjav",
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
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    video_cards = soup.select(".thumb.item, div.thumb")
    for card in video_cards:
        try:
            link = card.select_one("a[href]")
            if not link:
                continue
            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            img_tag = card.select_one("img[data-original], img[src]")
            if not img_tag:
                continue
            img = utils.safe_get_attr(
                img_tag, "data-webp", ["data-original", "data-src", "src"]
            )

            title_elem = card.select_one("a[title], .title, img[alt]")
            name = ""
            if title_elem:
                if title_elem.name == "a":
                    name = utils.safe_get_attr(title_elem, "title", default="")
                elif title_elem.name == "img":
                    name = utils.safe_get_attr(title_elem, "alt", default="")
                else:
                    name = utils.safe_get_text(title_elem, "")
            if not name:
                name = utils.safe_get_text(link, "")
            name = utils.cleantext(name)
            if not name:
                continue

            duration_elem = card.select_one(".time, .duration")
            duration = (
                utils.safe_get_text(duration_elem, "").strip() if duration_elem else ""
            )

            quality_elem = card.select_one(".qualtiy, .quality")
            quality = ""
            if quality_elem:
                qtext = utils.safe_get_text(quality_elem, "").upper()
                if "HD" in qtext:
                    quality = "HD"

            site.add_download_link(
                name,
                videopage,
                "Playvid",
                img,
                name,
                duration=duration,
                quality=quality,
            )
        except Exception as exc:
            utils.kodilog("kissjav List: Failed to parse video card - {}".format(exc))
            continue

    next_link = soup.select_one("a.next[href], a.pagination-next[href]")
    if next_link:
        nurl = utils.safe_get_attr(next_link, "href")
        nurl = urllib_parse.urljoin(site.url, nurl) if nurl else ""
        if nurl:
            current = soup.select_one(
                "a.active.item-pagination, a.item-pagination.is-active, .pagination-link.is-current"
            )
            last_candidates = soup.select(
                'a[data-container-id*="_pagination"], .pagination-link'
            )
            currpg = utils.safe_get_text(current, "").strip() if current else ""
            lastpg = (
                utils.safe_get_text(last_candidates[-1], "").strip()
                if last_candidates
                else ""
            )
            if lastpg and not lastpg.isdigit():
                lastpg = "".join(ch for ch in lastpg if ch.isdigit())
            info = ""
            if currpg and lastpg:
                info = " (Currently in {} of {})".format(currpg, lastpg)
            site.add_dir(
                "[COLOR hotpink]Next Page...[/COLOR]{}".format(info),
                nurl,
                "List",
                site.img_next,
            )

    utils.eod()


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


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    category_cards = soup.select("div.thumb.item, div.thumb.category, div.item")
    for card in category_cards:
        try:
            link = card.select_one("a[href]")
            if not link:
                continue
            caturl = utils.safe_get_attr(link, "href")
            if not caturl:
                continue

            img_tag = card.select_one("img[data-original], img[src]")
            img = (
                utils.safe_get_attr(img_tag, "data-original", ["data-src", "src"])
                if img_tag
                else ""
            )

            title_elem = card.select_one(".title, a[title], img[alt]")
            name = ""
            if title_elem:
                if title_elem.name == "a":
                    name = utils.safe_get_attr(title_elem, "title", default="")
                elif title_elem.name == "img":
                    name = utils.safe_get_attr(title_elem, "alt", default="")
                else:
                    name = utils.safe_get_text(title_elem, "")
            if not name:
                name = utils.safe_get_text(card, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            site.add_dir(name, caturl, "List", img)
        except Exception as exc:
            utils.kodilog("kissjav Categories: Failed to parse card - {}".format(exc))
            continue

    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playlists(url):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    playlist_cards = soup.select('div[id*="playlist-"]')
    for card in playlist_cards:
        try:
            link = card.select_one("a[href]")
            if not link:
                continue
            caturl = utils.safe_get_attr(link, "href")
            if not caturl:
                continue
            if caturl.startswith("/"):
                caturl = site.url[:-1] + caturl

            img_tag = card.select_one("img[data-src], img[src]")
            img = ""
            if img_tag:
                img = utils.safe_get_attr(img_tag, "data-src", ["src"])
                if img and img.startswith("/"):
                    img = site.url[:-1] + img

            name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)

            count_elem = card.select_one('[class*="video"], [class*="count"]')
            count = ""
            if count_elem:
                count_text = utils.safe_get_text(count_elem, "")
                count_match = re.search(r"(\d+)", count_text)
                if count_match:
                    count = count_match.group(1)

            if name:
                if count:
                    name = name + " [COLOR hotpink]({0} videos)[/COLOR]".format(count)
                site.add_dir(name, caturl, "List", img)
        except Exception as exc:
            utils.kodilog("kissjav Playlists: Failed to parse card - {}".format(exc))
            continue

    next_link = soup.select_one("a.pagination-next[href]")
    if next_link:
        np = utils.safe_get_attr(next_link, "href")
        if np:
            if np.startswith("/"):
                np = site.url[:-1] + np
            current = soup.select_one("a.pagination-link.is-current")
            last_candidates = soup.select("a.pagination-link")
            currpg = utils.safe_get_text(current, "").strip() if current else ""
            lastpg = (
                utils.safe_get_text(last_candidates[-1], "").strip()
                if last_candidates
                else ""
            )
            if currpg and lastpg:
                site.add_dir(
                    "[COLOR hotpink]Next Page[/COLOR] (Currently in Page {0} of {1})".format(
                        currpg, lastpg
                    ),
                    np,
                    "Playlists",
                    site.img_next,
                )
            else:
                site.add_dir(
                    "[COLOR hotpink]Next Page[/COLOR]", np, "Playlists", site.img_next
                )
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = url + keyword.replace(" ", "-") + "/"
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url)
    surl = re.search(r"video_url:\s*'([^']+)'", html)
    if surl:
        surl = surl.group(1)
        if surl.startswith("function/"):
            license = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, license)
        elif not surl.startswith("http"):
            surl = utils._bdecode(surl)
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(surl + "|referer=" + url)

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
    "supjav",
    "[COLOR hotpink]SupJav[/COLOR]",
    "https://supjav.com/",
    "supjav.png",
    "supjav",
)
surl = "https://lk1.supremejav.com/supjav.php"
enames = {
    "VV": "VideoVard",
    "TV": "TurboVIPlay",
    "JPA": "JAPOPAV",
    "ST": "StreamTape",
    "DS": "DoodStream",
    "JS": "JAVStream",
    "SSB": "StreamSB",
    "NS": "NinjaStream",
}


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Categories[/COLOR]", site.url, "Cat", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url + "popular?sort=week")


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in supjav: " + str(e))
        return None

    soup = utils.parse_html(listhtml)
    cookiestring = get_cookies()

    posts = soup.select('.post, [class*="post"]')
    for post in posts:
        try:
            link = post.select_one("a[href]")
            if not link:
                continue
            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            img_tag = post.select_one("img[data-original], img[src]")
            img = ""
            if img_tag:
                img = utils.safe_get_attr(img_tag, "data-original", ["src"])
                if img:
                    img = (
                        img
                        + "|Referer="
                        + url
                        + "&Cookie="
                        + cookiestring
                        + "&User-Agent="
                        + utils.USER_AGENT
                    )

            site.add_download_link(name, videopage, "Playvid", img, name)
        except Exception as exc:
            utils.kodilog("supjav List: Failed to parse post - {}".format(exc))
            continue

    # Find pagination
    active_page = soup.select_one("li.active span")
    if active_page:
        pagination_ul = active_page.find_parent("ul")
        if pagination_ul:
            active_li = active_page.find_parent("li")
            next_li = active_li.find_next_sibling("li") if active_li else None

            if next_li:
                next_link = next_li.select_one("a[href]")
                if next_link:
                    next_page = utils.safe_get_attr(next_link, "href")
                    np = utils.safe_get_text(next_link, "").strip()

                    # Find last page number
                    all_page_links = pagination_ul.select("li a")
                    lp = ""
                    if all_page_links:
                        last_text = utils.safe_get_text(all_page_links[-1], "").strip()
                        if last_text.isdigit():
                            lp = last_text

                    if next_page:
                        if np and lp:
                            site.add_dir(
                                "Next Page ({0}/{1})".format(np, lp),
                                next_page,
                                "List",
                                site.img_next,
                            )
                        else:
                            site.add_dir("Next Page", next_page, "List", site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(searchUrl, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    menu_items = soup.select(
        '.menu-item-object-category a, li[class*="menu-item-object-category"] a'
    )
    for link in menu_items:
        try:
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue
            name = utils.safe_get_text(link, "").strip()
            if name:
                site.add_dir(name, catpage, "List", "")
        except Exception as exc:
            utils.kodilog("supjav Cat: Failed to parse menu item - {}".format(exc))
            continue

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    videopage = utils.getHtml(url, site.url)
    soup = utils.parse_html(videopage)
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videourl = ""

    # Find the buttons div
    btns_div = soup.select_one('div.btns, div[class*="btns"]')
    if not btns_div:
        vp.progress.close()
        return

    sources = {}

    # Check if there are multiple parts (cd-server)
    cd_servers = btns_div.select('.cd-server, [class*="cd-server"]')
    if cd_servers:
        pno = 1
        for server_div in cd_servers:
            try:
                buttons = server_div.select(
                    'a.btn-server[data-link], a[class*="btn-server"][data-link]'
                )
                for btn in buttons:
                    embed = utils.safe_get_attr(btn, "data-link")
                    hoster = utils.safe_get_text(btn, "").strip()
                    if embed and hoster:
                        display_name = "{0} [COLOR hotpink]Part {1}[/COLOR]".format(
                            enames[hoster] if hoster in enames else hoster, pno
                        )
                        sources[display_name] = embed
                pno += 1
            except Exception as exc:
                utils.kodilog("supjav Playvid: Failed to parse cd-server - {}".format(exc))
                continue
    else:
        # Single part video
        try:
            buttons = btns_div.select(
                'a.btn-server[data-link], a[class*="btn-server"][data-link]'
            )
            for btn in buttons:
                embed = utils.safe_get_attr(btn, "data-link")
                hoster = utils.safe_get_text(btn, "").strip()
                if embed and hoster:
                    display_name = enames[hoster] if hoster in enames else hoster
                    sources[display_name] = embed
        except Exception as exc:
            utils.kodilog("supjav Playvid: Failed to parse buttons - {}".format(exc))

    olid = utils.selector("Select Hoster", sources)
    if olid:
        vurl = "{0}?c={1}".format(surl, olid[::-1])
        videourl = utils.getVideoLink(vurl, surl)

    if not videourl:
        vp.progress.close()
        return

    vp.play_from_link_to_resolve(videourl)


def get_cookies():
    domain = site.url.split("/")[2]
    utils.kodilog(domain)
    cookiestr = ""
    for cookie in utils.cj:
        utils.kodilog(cookie.domain)
        utils.kodilog(cookie.name)
        if domain in cookie.domain and cookie.name == "cf_clearance":
            cookiestr += "cf_clearance=" + cookie.value
        if domain in cookie.domain and cookie.name == "PHPSESSID":
            cookiestr += "; PHPSESSID=" + cookie.value
    return cookiestr

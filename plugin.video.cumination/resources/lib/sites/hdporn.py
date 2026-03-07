"""
Cumination
Copyright (C) 2018 Whitecream, holisticdioxide
Copyright (C) 2020 Team Cumination

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
    "porn00",
    "[COLOR hotpink]Porn00[/COLOR]",
    "https://www.porn00.org",
    "p00.png",
    "porn00",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        "{0}/tags/".format(site.url),
        "Cat",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        "{0}/search".format(site.url),
        "Search",
        site.img_search,
    )
    List("{0}/porn-page/1/".format(site.url))
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, "")
    soup = utils.parse_html(listhtml)
    video_items = soup.select(".item")

    for item in video_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            name_tag = item.select_one(".title, .le")
            name = utils.safe_get_text(name_tag)

            img_tag = item.select_one("img")
            img = utils.safe_get_attr(img_tag, "data-original", ["src"])

            duration_tag = item.select_one(".duration, .on")
            duration = utils.safe_get_text(duration_tag)

            is_hd = item.select_one(".is-hd")
            hd = "HD" if is_hd else ""

            if not videopage or not name:
                continue

            name = utils.cleantext(name.strip())
            site.add_download_link(
                name, videopage, "Playvid", img, name, duration=duration, quality=hd
            )
        except Exception as e:
            utils.kodilog("Error parsing video item in hdporn: " + str(e))
            continue

    next_page_tag = soup.select_one(".next a")
    if next_page_tag:
        next_url = utils.safe_get_attr(next_page_tag, "href")
        if next_url:
            if not next_url.startswith("http"):
                next_url = site.url + next_url
            page_num = next_url.split("/")[-2] if "/" in next_url else "Next"
            site.add_dir(
                "Next Page ({0})".format(page_num), next_url, "List", site.img_next
            )

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, site.url)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    cat_box = soup.select_one(".box")
    if not cat_box:
        utils.eod()
        return

    links = cat_box.select("li a[href]")
    for link in links:
        name = utils.safe_get_text(link)
        cat_url = utils.safe_get_attr(link, "href")
        if name and cat_url:
            site.add_dir(name, cat_url, "List", "")
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = "{0}/{1}/".format(url, title)
        List(searchUrl)

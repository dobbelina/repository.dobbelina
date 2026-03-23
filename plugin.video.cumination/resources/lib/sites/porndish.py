"""
Ultimate Whitecream
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

from resources.lib import utils
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "porndish",
    "[COLOR hotpink]Porndish[/COLOR]",
    "https://www.porndish.com/",
    "porndish.png",
    "porndish",
)


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Latest[/COLOR]", site.url + "page/1/", "List", site.img_next)
    List(site.url + "page/1/")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    if not listhtml:
        utils.eod()
        return
    soup = utils.parse_html(listhtml)
    if not soup:
        utils.eod()
        return

    seen = set()
    cards = soup.select("article a[title][href], .g1-collection a[title][href]")
    if not cards:
        cards = soup.select("a[title][href]")

    for link in cards:
        try:
            videopage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title")
            if not videopage or not name:
                continue
            if "/category/" in videopage or "/tag/" in videopage:
                continue
            if videopage in seen:
                continue
            seen.add(videopage)

            if videopage.startswith("/"):
                videopage = urllib_parse.urljoin(site.url, videopage)

            img_tag = link.select_one("img") or link.find_next("img")
            img = utils.get_thumbnail(img_tag)
            if img and img.startswith("/"):
                img = urllib_parse.urljoin(site.url, img)

            name = utils.cleantext(name)
            site.add_download_link(name, videopage, "Playvid", img, name)
        except Exception as e:
            utils.kodilog("Error parsing video: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one('a[rel="next"], a.next, .pagination a.next')
    if next_link:
        nurl = utils.safe_get_attr(next_link, "href")
        if nurl:
            if nurl.startswith("/"):
                nurl = urllib_parse.urljoin(site.url, nurl)
            site.add_dir("Next Page", nurl, "List", site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=None)
    vp.play_from_site_link(url, url)

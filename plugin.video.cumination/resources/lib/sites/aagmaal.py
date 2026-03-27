"""
Cumination Site Plugin
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

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "aagmaal",
    "[COLOR hotpink]Aag Maal[/COLOR]",
    "https://aagmaal.bz/",
    "aagmaal.png",
    "aagmaal",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]", site.url, "Categories", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    for item in soup.select("article"):
        link = item.select_one("a.vp-card__thumb") or item.select_one("a[href]")
        if not link:
            continue

        videopage = utils.safe_get_attr(link, "href")
        if not videopage:
            continue

        img_tag = link.select_one("img")
        name = utils.safe_get_attr(img_tag, "alt") or utils.safe_get_attr(link, "title")
        if not name:
            name = utils.safe_get_text(item.select_one("h2, h3, .entry-title"))
        if not name:
            name = "Video"
        name = utils.cleantext(name)

        img = utils.safe_get_attr(img_tag, "src", ["data-src", "data-original"])

        site.add_download_link(name, videopage, "Playvid", img, name)

    # .vp-pagination uses a.next.page-numbers
    vp_nav = soup.select_one(".vp-pagination")
    if vp_nav:
        next_link = vp_nav.select_one("a.next")
        if next_link:
            next_url = utils.safe_get_attr(next_link, "href")
            if next_url:
                curr = vp_nav.select_one(".current")
                dots = vp_nav.select_one(".dots")
                curr_txt = utils.safe_get_text(curr, "")
                last_txt = ""
                if dots:
                    after_dots = dots.find_next_sibling("a")
                    if after_dots:
                        last_txt = utils.safe_get_text(after_dots, "")
                if last_txt:
                    pgtxt = "Currently in Page {0} of {1}".format(curr_txt, last_txt)
                else:
                    pgtxt = "Currently in Page {0}".format(curr_txt)
                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR] ({0})".format(pgtxt),
                    next_url,
                    "List",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videourl = ""

    videopage = utils.getHtml(url, site.url)
    soup = utils.parse_html(videopage)

    # Find hosted links with title and target attributes
    links = {}
    for a in soup.select("a[title][href][target]"):
        link_url = utils.safe_get_attr(a, "href")
        link_title = utils.safe_get_attr(a, "title")
        if link_url and link_title and vp.resolveurl.HostedMediaFile(link_url):
            links[link_title] = link_url

    if not links:
        for a in soup.select('a.external[href], a[class*="external"][href]'):
            link_url = utils.safe_get_attr(a, "href")
            if link_url and vp.resolveurl.HostedMediaFile(link_url):
                links[link_url] = link_url

    if links:
        videourl = utils.selector("Select link", links)

    if not videourl:
        for pattern in [
            r'<iframe[^>]*\s+loading="lazy"\s+src="([^"]+)"',
            r'<iframe[^>]*\s+src="(http[^"]+)"',
        ]:
            match = re.search(pattern, videopage, re.DOTALL | re.IGNORECASE)
            if match:
                videourl = match.group(1)
                break

    if not videourl:
        utils.notify("Oh Oh", "No Videos found")
        vp.progress.close()
        return

    vp.play_from_link_to_resolve(videourl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    # Find the "Categories" h3 widget then its sibling ul
    cat_links = []
    for h3 in soup.select("h3"):
        if utils.safe_get_text(h3, "").strip() == "Categories":
            ul = h3.find_next_sibling("ul")
            if ul:
                for li in ul.select("li a[href]"):
                    catpage = utils.safe_get_attr(li, "href")
                    name = utils.cleantext(utils.safe_get_text(li))
                    if catpage and name:
                        cat_links.append((name, catpage))
            break

    for name, catpage in sorted(cat_links, key=lambda x: x[0].lower()):
        site.add_dir(name, catpage, "List")

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl + title
        List(searchUrl)

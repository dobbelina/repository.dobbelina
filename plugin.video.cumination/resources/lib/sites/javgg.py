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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "javgg", "[COLOR hotpink]JavGG[/COLOR]", "https://javgg.co/", "javgg.png", "javgg"
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]", site.url + "tags", "Cats", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Trending[/COLOR]", site.url + "trending/", "List", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Featured[/COLOR]", site.url + "featured/", "List", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]", site.url + "genre-list/", "Tags", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url + "new-post/page/1/")


@site.register()
def List(url):
    listhtml = utils.getHtml(url, "")
    soup = utils.parse_html(listhtml)

    contextmenu = []
    contexturl = utils.addon_sys + "?mode=javgg.Lookupinfo&url="
    contextmenu.append(
        ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
    )

    # Find all article elements
    articles = soup.select("article")
    for article in articles:
        try:
            # Get video link
            link = article.select_one("a[href]")
            if not link:
                continue
            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            # Get name from img alt
            img_tag = article.select_one("img")
            if not img_tag:
                continue
            name = utils.safe_get_attr(img_tag, "alt", default="")
            if not name:
                name = utils.safe_get_text(link, "").strip()

            # Get image src
            img = utils.safe_get_attr(img_tag, "src", ["data-src"])

            site.add_download_link(
                name, videopage, "Playvid", img, name, contextm=contextmenu
            )
        except Exception as e:
            utils.kodilog("javgg List: Error processing video - {}".format(e))
            continue

    # Pagination - find next link with id="next"
    next_link = soup.select_one(".pagination a[href] i#next")
    if next_link:
        # Get parent <a> tag
        next_a = next_link.find_parent("a")
        if next_a:
            next_url = utils.safe_get_attr(next_a, "href")
            if next_url:
                # Get page text from span
                page_span = soup.select_one(".pagination span")
                pgtxt = utils.safe_get_text(page_span, "").strip() if page_span else ""
                site.add_dir(
                    "Next Page...  ({0})".format(pgtxt), next_url, "List", site.img_next
                )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        List(url + keyword.replace(" ", "+"))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex='"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    eurls = re.compile(r"""<iframe[^<]+?src='([^']+)""").findall(videopage)
    sources = {}
    for eurl in eurls:
        if vp.resolveurl.HostedMediaFile(eurl):
            sources.update({eurl.split("/")[2]: eurl})
    videourl = utils.selector("Select Hoster", sources)
    vp.play_from_link_to_resolve(videourl)


@site.register()
def Cats(url):
    match = [
        ("Random", "random/"),
        ("HD Uncensored", "tag/hd-uncensored/"),
        ("Uncensored Leak", "tag/uncensored-leak/"),
        ("Decensored", "tag/decensored/"),
        ("Censored", "tag/censored/"),
        ("Chinese Subtitle", "tag/chinese-subtitle/"),
        ("English Subtitle", "tag/english-subtitle/"),
    ]

    for name, catpage in match:
        site.add_dir(name, site.url + catpage, "List", "")

    utils.eod()


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    # Find all genre links
    genre_links = soup.select('a[href*="/genre/"]')
    for link in genre_links:
        try:
            href = utils.safe_get_attr(link, "href")
            if not href or "/genre/" not in href:
                continue

            # Extract genre path from full URL or relative path
            if href.startswith("http"):
                # Full URL - extract path after domain
                tagpage = (
                    "/" + "/".join(href.split("/")[3:])
                    if len(href.split("/")) > 3
                    else href
                )
            else:
                tagpage = href

            name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            # Build full URL
            full_url = (
                site.url + tagpage
                if tagpage.startswith("/")
                else site.url + "/" + tagpage
            )
            site.add_dir(name, full_url, "List", "")
        except Exception as e:
            utils.kodilog("javgg Tags: Error processing tag - {}".format(e))
            continue

    utils.eod()


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)<', ""),
        ("Genres", r'/(genre/[^"]+)"\s*?rel="tag">([^<]+)<', ""),
        ("Maker", r'/(maker/[^"]+)"\s*?rel="tag">([^<]+)<', ""),
        ("Label", r'/(label/[^"]+)"\s*?rel="tag">([^<]+)<', ""),
        ("Director", r'/(director/[^"]+)"\s*?rel="tag">([^<]+)<', ""),
        ("Cast", r'/(star/[^"]+)"\s*?rel="tag">([^<]+)<', ""),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, "javgg.List", lookup_list)
    lookupinfo.getinfo()

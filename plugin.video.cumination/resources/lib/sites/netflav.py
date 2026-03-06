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

import json

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.http_timeouts import HTTP_TIMEOUT_DEFAULT
from six.moves import urllib_parse

site = AdultSite(
    "netflav",
    "[COLOR hotpink]Netflav[/COLOR]",
    "https://netflav.com/",
    "netflav.png",
    "netflav",
)


def make_netflav_headers():
    netflav_headers = utils.base_hdrs
    netflav_headers["Accept"] = (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    )
    netflav_headers["Accept-Encoding"] = "gzip, deflate, br"
    netflav_headers["Cookie"] = "i18next=en"
    return netflav_headers


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Censored[/COLOR]",
        site.url + "censored",
        "List",
        site.img_cat,
        section="censored",
    )
    site.add_dir(
        "[COLOR hotpink]Trending[/COLOR]",
        site.url + "trending",
        "List",
        site.img_cat,
        section="trending",
    )
    site.add_dir(
        "[COLOR hotpink]Uncensored[/COLOR]",
        site.url + "uncensored",
        "List",
        site.img_cat,
        section="uncensored",
    )
    site.add_dir(
        "[COLOR hotpink]Genres[/COLOR]", site.url + "genre", "Genres", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "api98/video/advanceSearchVideo?type=title&page=1&keyword=",
        "Search",
        site.img_search,
        section="search",
    )
    utils.eod()


@site.register()
def List(url, section="all"):
    try:
        listhtml, _ = utils.get_html_with_cloudflare_retry(
            url, referer=site.url, headers=make_netflav_headers()
        )
    except Exception as e:
        utils.kodilog("netflav List error: {}".format(str(e)))
        utils.eod()
        return

    stripped = listhtml.strip()
    if not stripped or stripped in {"0", "1"} or len(stripped) < 16:
        utils.notify("Netflav", "Access blocked/challenged")
        utils.eod()
        return

    try:
        if section == "search":
            jdata = json.loads(listhtml).get("result")
        else:
            # Extract JSON from Next.js data script tag
            soup = utils.parse_html(listhtml)
            script_tag = soup.select_one(
                'script#__NEXT_DATA__[type="application/json"]'
            )
            if not script_tag:
                utils.kodilog("netflav: Could not find __NEXT_DATA__ script tag")
                utils.notify("Error", "Unable to parse page data")
                utils.eod()
                return

            jdata_text = script_tag.string
            if not jdata_text:
                utils.kodilog("netflav: __NEXT_DATA__ script tag is empty")
                utils.notify("Error", "Unable to parse page data")
                utils.eod()
                return

            initial_state = json.loads(jdata_text).get("props", {}).get("initialState", {})
            jdata = initial_state.get(section)
            if not isinstance(jdata, dict) or not jdata.get("docs"):
                for key in ("censored", "trending", "all", "browse"):
                    if isinstance(initial_state.get(key), dict) and initial_state.get(key).get("docs"):
                        jdata = initial_state.get(key)
                        section = key
                        break
            if not isinstance(jdata, dict):
                utils.notify("Error", "Unable to parse page data")
                utils.eod()
                return

        page = jdata.get("page")
        pages = jdata.get("pages")
        videos = jdata.get("docs") or []

        for video in videos:
            name = video["title_en"] if utils.PY3 else video["title_en"].encode("utf-8")
            name = utils.cleantext(name)
            img = video.get("preview", "")
            date_added = video.get("sourceDate", "").split("T")[0]
            if not date_added:
                date_added = video.get("createdAt", "").split("T")[0]
            plot = "{0}\n{1}".format(name, date_added)
            videopage = "{0}video?id={1}".format(site.url, video.get("videoId"))

            contextmenu = []
            contexturl = (
                utils.addon_sys
                + "?mode=netflav.Lookupinfo"
                + "&url="
                + urllib_parse.quote_plus(videopage)
            )
            contextmenu.append(
                ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
            )

            site.add_download_link(
                name, videopage, "Playvid", img, plot, contextm=contextmenu
            )

        if page and pages and page < pages and "page=" in url:
            if "page=" in url:
                npurl = url.replace("page={}".format(page), "page={}".format(page + 1))
            else:
                npurl = url
            site.add_dir(
                "[COLOR hotpink]Next Page...[/COLOR] ({0}/{1})".format(page + 1, pages),
                npurl,
                "List",
                site.img_next,
                section=section,
            )

    except Exception as e:
        utils.kodilog("netflav List parsing error: {}".format(str(e)))
        utils.notify("Error", "Unable to parse videos")

    utils.eod()


@site.register()
def Genres(url):
    try:
        genrehtml = utils.getHtml(
            url, headers=make_netflav_headers(), timeout=HTTP_TIMEOUT_DEFAULT
        )
    except Exception as e:
        utils.kodilog("netflav Genres error: {}".format(str(e)))
        utils.eod()
        return

    soup = utils.parse_html(genrehtml)

    # Find all genre sections with headers
    sections = soup.select('[class*="container_header_title_large"]')

    for section_header in sections:
        header = utils.safe_get_text(section_header, "").strip()
        if not header:
            continue

        # Find the container following this header (look for genre links)
        # Navigate to parent and find genre links
        parent = section_header.find_parent()
        if not parent:
            continue

        # Find all genre links in this section
        genre_links = parent.select('a[href*="/all?genre"]')

        genre_list = []
        for link in genre_links:
            genreurl = utils.safe_get_attr(link, "href", default="")
            if not genreurl:
                continue

            # Get genre name from the link text or div inside
            genre_div = link.select_one("div")
            genre = utils.safe_get_text(genre_div if genre_div else link, "").strip()

            if genre and genreurl:
                genre_list.append((genreurl, genre))

        # Add genres sorted alphabetically
        for genreurl, genre in sorted(genre_list, key=lambda x: x[1]):
            name = "{0} - {1}".format(header, utils.cleantext(genre))
            if not genreurl.startswith("http"):
                genreurl = site.url + genreurl.lstrip("/")
            if "&page=" not in genreurl and "?page=" not in genreurl:
                genreurl += "&page=1"
            site.add_dir(name, genreurl, "List", "", page=1, section="all")

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = "{0}{1}".format(url, keyword.replace(" ", "+"))
        List(url, section="search")


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        html = utils.getHtml(url, site.url, timeout=HTTP_TIMEOUT_DEFAULT)
    except Exception as e:
        utils.kodilog("netflav Playvid error loading page: {}".format(str(e)))
        vp.progress.close()
        utils.notify("Error", "Unable to load video page")
        return

    try:
        # Extract JSON from Next.js data script tag using BeautifulSoup
        soup = utils.parse_html(html)
        script_tag = soup.select_one('script#__NEXT_DATA__[type="application/json"]')
        if not script_tag or not script_tag.string:
            utils.kodilog("netflav Playvid: Could not find __NEXT_DATA__ script tag")
            vp.progress.close()
            utils.notify("Error", "Unable to find video data")
            return

        jdata = (
            json.loads(script_tag.string)
            .get("props")
            .get("initialState")
            .get("video")
            .get("data")
        )
        links = {}

        for link in jdata.get("srcs", []):
            if vp.bypass_hosters_single(link):
                continue
            if vp.resolveurl.HostedMediaFile(link).valid_url():
                links[utils.get_vidhost(link)] = link

        videourl = utils.selector("Select link", links)
        if not videourl:
            vp.progress.close()
            return

        vp.play_from_link_to_resolve(videourl)

    except Exception as e:
        utils.kodilog("netflav Playvid parsing error: {}".format(str(e)))
        vp.progress.close()
        utils.notify("Error", "Unable to extract video link")


@site.register()
def Lookupinfo(url):
    class NetflavLookup(utils.LookupInfo):
        def url_constructor(self, url):
            return site.url + url + "&page=1"

    lookup_list = [
        ("Genre", r'/(all\?genre[^"]+)"><u>([^<]+)<', ""),
        ("Actress", r'/(all\?actress[^"]+)"><u>([^<]+)<', ""),
    ]

    lookupinfo = NetflavLookup(site.url, url, "netflav.List", lookup_list)
    lookupinfo.getinfo(headers=make_netflav_headers())

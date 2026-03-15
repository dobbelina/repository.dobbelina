"""
Cumination
Copyright (C) 2020 Cumination

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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "speedporn",
    "[COLOR hotpink]SpeedPorn[/COLOR]",
    "https://speedporn.net/",
    "speedporn.png",
    "speedporn",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        "{}categories/".format(site.url),
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR] - Loads all the pages",
        "{}categories/".format(site.url),
        "Categories_all",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]",
        "{}pornstars/".format(site.url),
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Porn videos[/COLOR]",
        "{}xxxfree/".format(site.url),
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Studios[/COLOR]",
        "{}all-porn-movie-studios/".format(site.url),
        "Tags",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        "{}?s=".format(site.url),
        "Search",
        site.img_search,
    )
    List(site.url + "category/1-porn-movies/")
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml, _ = utils.get_html_with_cloudflare_retry(url)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in speedporn: " + str(e))
        return None

    if not listhtml or utils.is_cloudflare_challenge_page(listhtml):
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    for link in soup.select("a.thumb, a.thumb[href]"):
        videopage = utils.safe_get_attr(link, "href", default="")
        if not videopage:
            continue
        img_tag = link.select_one("img")
        img = utils.safe_get_attr(img_tag, "src", ["data-src", "data-original"])
        name = utils.cleantext(
            utils.safe_get_text(link.select_one(".title"), default="")
        )
        duration = utils.safe_get_text(link.select_one(".duration"), default="")
        if duration:
            duration = duration.replace(" hrs.", "h").replace(" mins.", "m")

        contextmenu = []
        contexturl = (
            utils.addon_sys
            + "?mode="
            + str("speedporn.Lookupinfo")
            + "&url="
            + urllib_parse.quote_plus(videopage)
        )
        contextmenu.append(
            ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
        )

        site.add_download_link(
            name, videopage, "Playvid", img, contextm=contextmenu, duration=duration
        )

    next_link = soup.select_one("a.next.page-link[href]")
    if next_link:
        next_page = utils.safe_get_attr(next_link, "href", default="")
        if next_page:
            page_nr = (
                re.findall(r"\d+", next_page)[-1]
                if re.findall(r"\d+", next_page)
                else ""
            )
            site.add_dir(
                "Next Page (" + str(page_nr) + ")", next_page, "List", site.img_next
            )
    utils.eod()


@site.register()
def List_all(url):
    nextpg = True
    while nextpg:
        try:
            listhtml, _ = utils.get_html_with_cloudflare_retry(url)
            if not listhtml or utils.is_cloudflare_challenge_page(listhtml):
                break

            match = re.compile(
                r'class="thumb" href="([^"]+)".+?-src="([^"]+)".+?span class="duration">([^<]+).+?span class="title">([^<]+)',
                re.DOTALL | re.IGNORECASE,
            ).findall(listhtml)
            for videopage, img, duration, name in match:
                name = utils.cleantext(name)
                contextmenu = []
                contexturl = (
                    utils.addon_sys
                    + "?mode="
                    + str("speedporn.Lookupinfo")
                    + "&url="
                    + urllib_parse.quote_plus(videopage)
                )
                contextmenu.append(
                    (
                        "[COLOR deeppink]Lookup info[/COLOR]",
                        "RunPlugin(" + contexturl + ")",
                    )
                )

                site.add_download_link(
                    name,
                    videopage,
                    "Playvid",
                    img,
                    contextm=contextmenu,
                    duration=duration,
                )
            if len(match) == 49:
                next_page = re.compile(
                    r'class="next page-link" href="([^"]+)">&raquo;<',
                    re.DOTALL | re.IGNORECASE,
                ).findall(listhtml)
                if next_page:
                    url = next_page[0]
            else:
                nextpg = False
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in speedporn: " + str(e))
            nextpg = False
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.get_html_with_cloudflare_retry(url, "")[0]
    videos = cathtml.split('class="video-block video-block-cat"')
    videos.pop(0)

    for video in videos:
        match = re.compile(
            r'href="([^"]+)".+?src="(http[^"]+jpg)".+?class="title">([^<]+)<.+?class="video-datas">([^<]+)</div',
            re.DOTALL | re.IGNORECASE,
        ).findall(video)
        for catpage, img, name, count in match:
            name = (
                utils.cleantext(name) + " [COLOR deeppink]" + count.strip() + "[/COLOR]"
            )
            site.add_dir(name, catpage, "List", img)

    next_page = re.compile(
        r'class="next page-link" href="([^"]+)">&raquo;<', re.DOTALL | re.IGNORECASE
    ).findall(cathtml)
    if next_page:
        next_page = next_page[0]
        page_nr = re.findall(r"\d+", next_page)[-1]
        site.add_dir(
            "Next Page (" + str(page_nr) + ")", next_page, "Categories", site.img_next
        )
    utils.eod()


@site.register()
def Categories_all(url):
    nextpg = True
    while nextpg:
        try:
            cathtml = utils.get_html_with_cloudflare_retry(url, "")[0]
            videos = cathtml.split('class="video-block video-block-cat"')
            videos.pop(0)

            for video in videos:
                match = re.compile(
                    r'href="([^"]+)".+?src="(http[^"]+jpg)".+?class="title">([^<]+)<.+?class="video-datas">([^<]+)</div',
                    re.DOTALL | re.IGNORECASE,
                ).findall(video)
                for catpage, img, name, count in match:
                    name = (
                        utils.cleantext(name)
                        + " [COLOR deeppink]"
                        + count.strip()
                        + "[/COLOR]"
                    )
                    site.add_dir(name, catpage, "List", img)
            if len(videos) == 49:
                next_page = re.compile(
                    r'class="next page-link" href="([^"]+)">&raquo;<',
                    re.DOTALL | re.IGNORECASE,
                ).findall(cathtml)
                if next_page:
                    url = next_page[0]
            else:
                nextpg = False
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in speedporn: " + str(e))
            nextpg = False
    utils.eod()


@site.register()
def Tags(url):
    cathtml = utils.get_html_with_cloudflare_retry(url, "")[0]
    match = re.compile(
        'div class="tag-item"><a href="([^"]+)"[^>]+>([^<]+)<',
        re.DOTALL | re.IGNORECASE,
    ).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, catpage, "List", "")
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        videopage, _ = utils.get_html_with_cloudflare_retry(url)
    except Exception:
        vp.progress.close()
        return

    if not videopage or utils.is_cloudflare_challenge_page(videopage):
        vp.progress.close()
        return

    if "kt_player('kt_player'" in videopage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(videopage, url)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Genre", '(genres/[^"]+)" title="([^"]+)', ""),
        ("Studio", '(director/[^"]+)" title="([^"]+)', ""),
        ("Actor", '(pornstars/[^"]+)" title="([^"]+)', ""),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, "speedporn.List", lookup_list)
    lookupinfo.getinfo()

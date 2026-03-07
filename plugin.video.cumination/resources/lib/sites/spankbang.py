"""
Cumination
Copyright (C) 2015 Whitecream
Copyright (C) 2015 NothingGnome

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
    "spankbang",
    "[COLOR hotpink]SpankBang[/COLOR]",
    "https://spankbang.party/",
    "spankbang.png",
    "spankbang",
)
filterQ = utils.addon.getSetting("spankbang_quality") or "All"
filterL = utils.addon.getSetting("spankbang_length") or "All"


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Tags[/COLOR]", site.url + "tags", "Tags", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Models[/COLOR]",
        site.url + "pornstars_alphabet",
        "Models_alphabet",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "s/", "Search", site.img_search
    )
    site.add_dir(
        "[COLOR hotpink]Quality: [/COLOR] [COLOR orange]{}[/COLOR]".format(filterQ),
        "",
        "FilterQ",
        "",
        Folder=False,
    )
    site.add_dir(
        "[COLOR hotpink]Length: [/COLOR] [COLOR orange]{}[/COLOR]".format(filterL),
        "",
        "FilterL",
        "",
        Folder=False,
    )
    List(site.url + "new_videos/1/")
    utils.eod()


@site.register()
def List(url):
    from six.moves import urllib_parse

    filtersQ = {"All": "", "4k": "uhd", "1080p": "fhd", "720p": "hd"}
    filtersL = {"All": "", "10+min": 10, "20+min": 20, "40+min": 40}

    # Parse URL to preserve existing parameters
    parsed = urllib_parse.urlparse(url)
    params = urllib_parse.parse_qs(parsed.query)

    # Only apply filters to main listing and tag pages, NOT search pages
    # Search pages use different parameter structure
    is_search_page = "/s/" in parsed.path
    is_main_listing = "/new_videos/" in parsed.path or "/trending/" in parsed.path

    # Only add 'o=new' parameter for main listing (not tags or search)
    if is_main_listing and "o" not in params:
        params["o"] = ["new"]

    # Apply quality filter to all non-search pages
    if not is_search_page and "q" not in params and filtersQ[filterQ]:
        params["q"] = [filtersQ[filterQ]]

    # Apply length filter to all non-search pages
    if not is_search_page and "d" not in params and filtersL[filterL]:
        params["d"] = [str(filtersL[filterL])]

    # Rebuild URL with parameters
    query_string = urllib_parse.urlencode(params, doseq=True)
    url = urllib_parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", query_string, "")
    )

    listhtml = utils.getHtml(url, "")

    soup = utils.parse_html(listhtml)
    video_items = soup.select('[data-testid="video-item"]')
    for item in video_items:
        link = item.select_one('a[href*="/video/"]')
        if not link:
            continue
        videopage = utils.safe_get_attr(link, "href")
        if not videopage:
            continue

        img_tag = link.select_one("img")
        img = utils.safe_get_attr(img_tag, "data-src", ["src"])
        if not img:
            continue

        title_anchor = item.select_one("p a[title]") or link
        name = utils.cleantext(utils.safe_get_text(title_anchor))
        if not name:
            continue

        duration_tag = item.select_one('[data-testid="video-item-length"]')
        duration = utils.safe_get_text(duration_tag)

        quality_tag = item.select_one(
            '[data-testid="video-item-resolution"], .video-badge.h, .video-badge.uhd'
        )
        quality = utils.safe_get_text(quality_tag)

        videourl = (
            site.url[:-1] + videopage if not videopage.startswith("http") else videopage
        )
        site.add_download_link(
            name, videourl, "Playvid", img, name, duration=duration, quality=quality
        )

    pagination = soup.select_one(".pagination")
    if pagination:
        next_link = pagination.select_one("li.next a[href]")
        if next_link:
            next_href = utils.safe_get_attr(next_link, "href")
            if next_href:
                pages = [
                    utils.safe_get_text(a)
                    for a in pagination.select("li a")
                    if utils.safe_get_text(a).isdigit()
                ]
                lp = "/" + pages[-1] if pages else ""
                segment = next_href.split("/?")[0].rstrip("/").split("/")[-1]
                np = segment if segment.isdigit() else ""
                label = "Next Page.."
                if np or lp:
                    display_np = np if np else "?"
                    label += " ({}{})".format(display_np, lp)
                if not next_href.startswith("http"):
                    next_href = site.url[:-1] + next_href
                site.add_dir(label, next_href, "List", site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        from six.moves import urllib_parse

        title = urllib_parse.quote_plus(keyword)
        searchUrl = searchUrl + title + "/"
        List(searchUrl)


@site.register()
def Tags(url):
    cathtml = utils.getHtml(url, "")
    
    soup = utils.parse_html(cathtml)

    # Find all tag links (don't restrict to search_holder as tags are in main_content_container)
    tag_links = soup.select("a.keyword")
    tags = []
    for link in tag_links:
        try:
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue
            name = utils.safe_get_text(link).strip()
            if name and catpage:
                tags.append((catpage, name))
        except Exception as exc:
            utils.kodilog("spankbang Tags: Failed to parse tag - {}".format(exc))
            continue

    # Sort by name and add to directory
    for catpage, name in sorted(tags, key=lambda x: x[1]):
        full_url = (
            site.url[:-1] + catpage if not catpage.startswith("http") else catpage
        )
        site.add_dir(name, full_url, "List")

    pagination = soup.select_one(".pagination")
    if pagination:
        next_link = pagination.select_one("li.next a[href]")
        if next_link:
            next_href = utils.safe_get_attr(next_link, "href")
            if next_href:
                pages = [
                    utils.safe_get_text(a)
                    for a in pagination.select("li a")
                    if utils.safe_get_text(a).isdigit()
                ]
                lp = "/" + pages[-1] if pages else ""
                # segment logic might be different for tags, but let's try generic
                segment = next_href.split("/?")[0].rstrip("/").split("/")[-1]
                np = segment if segment.isdigit() else ""
                label = "Next Page.."
                if np or lp:
                    display_np = np if np else "?"
                    label += " ({}{})".format(display_np, lp)
                if not next_href.startswith("http"):
                    next_href = site.url[:-1] + next_href
                site.add_dir(label, next_href, "Tags", site.img_next)

    utils.eod()


@site.register()
def Models_alphabet(url):
    cathtml = utils.getHtml(url, "")
    
    soup = utils.parse_html(cathtml)
    items = soup.select("ul.alphabets li a")
    for link in items:
        catpage = utils.safe_get_attr(link, "href")
        name = utils.safe_get_text(link)
        if catpage and name:
            full_url = (
                site.url[:-1] + catpage if not catpage.startswith("http") else catpage
            )
            site.add_dir(name, full_url, "Models", "", "")
    utils.eod()


@site.register()
def Models(url):
    cathtml = utils.getHtml(url, "")
    
    soup = utils.parse_html(cathtml)
    items = soup.select("ul.list li")
    for item in items:
        link = item.select_one("a")
        if not link:
            continue

        catpage = utils.safe_get_attr(link, "href")
        name = utils.safe_get_text(link)

        videos = ""
        # Try to find the video count which is usually in a span with class "videos" or just a span
        span = item.select_one("span.videos") or item.select_one("span")
        if span:
            videos = utils.safe_get_text(span).strip()

        if catpage and name:
            name_display = name + "[COLOR hotpink]{}[/COLOR]".format(videos)
            full_url = (
                site.url[:-1] + catpage if not catpage.startswith("http") else catpage
            )
            site.add_dir(name_display, full_url, "List", "", "")
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    html = utils.getHtml(url, "")
    sources = {}
    srcs = re.compile(
        r"""["'](240p|320p|480p|720p|1080p|4k)["']:\s*\[["']([^"']+)""",
        re.DOTALL | re.IGNORECASE,
    ).findall(html)
    for quality, videourl in srcs:
        if videourl:
            sources[quality] = videourl

    videourl = utils.prefquality(
        sources, sort_by=lambda x: 1081 if x == "4k" else int(x[:-1]), reverse=True
    )
    if not videourl:
        utils.kodilog("spankbang: No video sources found")
        return

    # Clean up escaped characters in URL
    videourl = videourl.replace(r"\u0026", "&").replace("\\/", "/")
    vp.progress.update(75, "[CR]Playing video[CR]")
    vp.play_from_direct_link(videourl)


@site.register()
def FilterQ():
    filters = {"All": 1, "4k": 2, "1080p": 3, "720p": 4}
    f = utils.selector(
        "Select resolution", filters.keys(), sort_by=lambda x: filters[x]
    )
    if f:
        utils.addon.setSetting("spankbang_quality", f)
        utils.refresh()


@site.register()
def FilterL():
    filters = {"All", "10+min", "20+min", "40+min"}
    f = utils.selector("Select length", filters, reverse=True)
    if f:
        utils.addon.setSetting("spankbang_length", f)
        utils.refresh()

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
from six.moves import urllib_parse

site = AdultSite(
    "pornhoarder",
    "[COLOR hotpink]PornHoarder[/COLOR]",
    "https://pornhoarder.io/",
    "pornhoarder.png",
    "pornhoarder",
)

ph_headers = {
    "Origin": site.url[:-1],
    "User-Agent": utils.USER_AGENT,
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": "pornhoarder_settings=0---0---1---0",
}


def _extract_srcset_url(value):
    if not value:
        return ""
    first = value.split(",")[0].strip()
    return first.split(" ")[0].strip()


def _extract_search_term(url):
    match = re.search(r"[?&]search=([^&]+)", url)
    if not match:
        return ""
    return urllib_parse.unquote(match.group(1))


def _extract_video_image(link, siteurl):
    primary = link.select_one(
        ".video-image.primary[data-src], .video-image.primary[src]"
    )
    if primary:
        src = utils.safe_get_attr(primary, "data-src", ["src"])
        if src:
            return urllib_parse.urljoin(siteurl, src)

    for img_tag in link.select("img"):
        src = utils.safe_get_attr(
            img_tag,
            "data-src",
            ["data-original", "data-lazy", "data-srcset", "srcset", "src"],
        )
        src = _extract_srcset_url(src)
        if not src:
            continue
        alt = utils.safe_get_attr(img_tag, "alt", default="").lower()
        if (
            "logo" in src.lower()
            or "server_icons" in src
            or "logo" in alt
            or alt == "ico"
        ):
            continue
        return urllib_parse.urljoin(siteurl, src)
    return ""


def _parse_video_items(soup, siteurl):
    selector = (
        "article a[href], a.video-link[href], a[href*='/watch/'], "
        "a[href*='/pornvideo/'], a[href*='/videos/']"
    )
    for link in soup.select(selector):
        videourl = utils.safe_get_attr(link, "href", default="")
        if not videourl or not any(
            marker in videourl
            for marker in ("/watch/", "/pornvideo/", "/videos/", "/video/")
        ):
            continue

        videourl = urllib_parse.urljoin(siteurl, videourl)
        img = _extract_video_image(link, siteurl)

        name = utils.cleantext(utils.safe_get_text(link.select_one("h1"), default=""))
        if not name:
            name = utils.cleantext(utils.safe_get_attr(link, "title", default=""))
        if not name:
            continue

        duration = utils.safe_get_text(link.select_one(".length"), default="")
        if not duration:
            duration = utils.safe_get_text(link.select_one(".video-length"), default="")

        site.add_download_link(name, videourl, "Playvid", img, name, duration=duration)


def _add_next_page_from_soup(soup, url, mode, siteurl=None):
    next_link = soup.select_one(".pagination .next a[href], .next a[href]")
    next_button = soup.select_one(".next .pagination-button[data-page]")
    next_page = ""
    next_url = url

    if next_button:
        next_page = utils.safe_get_attr(next_button, "data-page", default="")

    if next_link:
        next_url = urllib_parse.urljoin(
            site.url, utils.safe_get_attr(next_link, "href", default="")
        )
        if not next_page:
            next_page = utils.safe_get_attr(next_link, "data-page", default="").strip()
        if not next_page:
            next_page = utils.safe_get_text(next_link, default="").strip()
        if not next_page:
            href = utils.safe_get_attr(next_link, "href", default="")
            match = re.search(r"(?:[?&]page=|/page/)(\d+)", href)
            if match:
                next_page = match.group(1)

    if next_page:
        if mode == "List" and siteurl:
            site.add_dir(
                "Next Page ({})".format(next_page),
                url,
                mode,
                site.img_next,
                page=int(next_page),
                section=siteurl,
            )
        else:
            site.add_dir(
                "Next Page ({})".format(next_page),
                next_url,
                mode,
                site.img_next,
            )


def Createdata(page=1, search="", sort="0", date="0"):
    return [
        ("search", search),
        ("sort", sort),
        ("date", date),
        ("servers[]", "21"),
        ("servers[]", "40"),
        ("servers[]", "12"),
        ("servers[]", "35"),
        ("servers[]", "25"),
        ("servers[]", "41"),
        ("servers[]", "46"),
        ("servers[]", "17"),
        ("servers[]", "44"),
        ("servers[]", "42"),
        ("servers[]", "43"),
        ("servers[]", "29"),
        ("author", "0"),
        ("page", page),
    ]


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Latest Videos[/COLOR]",
        site.url + "search/?search=&sort=0",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Popular Videos[/COLOR]",
        site.url + "search/?search=&sort=2",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Trending Videos[/COLOR]",
        site.url + "trending-videos/",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Random Videos[/COLOR]",
        site.url + "random-videos/",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Studios[/COLOR]",
        site.url + "studios/",
        "Studios",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]",
        site.url + "pornstars/",
        "Pornstars",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/",
        "Search",
        site.img_search,
    )
    # Keep legacy behavior: show latest videos directly on main page.
    List(site.url + "search/?search=&sort=0", page=1)


@site.register()
def List(url, page=1, section=None):
    try:
        current_page = int(page)
    except (TypeError, ValueError):
        current_page = 1

    if isinstance(url, str) and any(
        path in url for path in ("/trending-videos/", "/random-videos/")
    ):
        paged_url = url
        if current_page > 1 and "page=" not in paged_url:
            sep = "&" if "?" in paged_url else "?"
            paged_url = "{}{}page={}".format(paged_url, sep, current_page)
        html = utils.getHtml(paged_url, site.url)
        soup = utils.parse_html(html)
        _parse_video_items(soup, site.url)
        _add_next_page_from_soup(soup, url, "List")
        utils.eod()
        return

    search = "" if isinstance(url, str) and url.startswith("https://") else url
    siteurl = section if section else site.url
    sort = "0"
    date = "0"

    if isinstance(url, str) and url.startswith("https://"):
        if "ajax_search.php" in url or "/search/" in url:
            ajax_url = url
            if "/search/" in url:
                ajax_url = siteurl + "ajax_search.php"
            referer = siteurl
            search = _extract_search_term(url)
            sort_match = re.search(r"[?&]sort=(\d+)", url)
            if sort_match:
                sort = sort_match.group(1)
            date_match = re.search(r"[?&]date=(\d+)", url)
            if date_match:
                date = date_match.group(1)
        else:
            ajax_url = siteurl + "ajax_search.php"
            referer = url
            search = _extract_search_term(url)
    else:
        ajax_url = siteurl + "ajax_search.php"
        referer = siteurl

    headers = dict(ph_headers)
    headers["Referer"] = referer

    listhtml = utils.postHtml(
        ajax_url,
        form_data=Createdata(current_page, search, sort=sort, date=date),
        headers=headers,
    )
    if not listhtml:
        fallback_url = url
        if not isinstance(url, str) or not url.startswith("https://"):
            fallback_url = siteurl + "search/?search={}".format(
                urllib_parse.quote(search)
            )
        listhtml = utils.getHtml(fallback_url)

    soup = utils.parse_html(listhtml)
    _parse_video_items(soup, siteurl)
    _add_next_page_from_soup(soup, url, "List", siteurl=siteurl)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    # Check for direct video links in the page first
    match = re.search(r'["\']file["\']\s*:\s*["\']([^"\']+\.mp4[^"\']*)["\']', html, re.IGNORECASE)
    if match:
        video_url = match.group(1).replace("\\/", "/")
        vp.play_from_direct_link(video_url + "|Referer=" + url)
        return

    watch_soup = utils.parse_html(html)
    # Prefer current iframe source (player_t.php) over embedUrl metadata.
    embed_url = utils.safe_get_attr(
        watch_soup.select_one("iframe[src*='player']"), "src", default=""
    )
    if not embed_url:
        embed_url = "".join(re.findall(r'"embedUrl":\s*"([^"]+)"', html))

    if not embed_url:
        # Try to find any player.php or player_t.php link
        embed_match = re.search(r'https?://pornhoarder\.net/player(?:_t)?\.php\?video=[^"\'\s>]+', html)
        if embed_match:
            embed_url = embed_match.group(0)

    if not embed_url:
        # Fallback to metadata
        meta_embed = watch_soup.find("meta", {"itemprop": "embedURL"})
        if meta_embed:
            embed_url = utils.safe_get_attr(meta_embed, "content")

    if not embed_url:
        vp.play_from_link_to_resolve(url)
        return

    embed_url = embed_url.replace("/player.php?", "/player_t.php?")
    if embed_url.startswith("//"):
        embed_url = "https:" + embed_url
    elif embed_url.startswith("/"):
        embed_url = urllib_parse.urljoin(site.url, embed_url)

    # New player endpoints require a POST to resolve the final host iframe.
    if "pornhoarder.net/player" in embed_url:
        headers = dict(ph_headers)
        headers["Referer"] = url
        player_html = utils.postHtml(embed_url, headers=headers, form_data={"play": ""})
        if not player_html:
            player_html = utils.getHtml(embed_url, url)

        if player_html:
            # Check for direct file in player HTML
            file_match = re.search(r'["\']file["\']\s*:\s*["\']([^"\']+\.mp4[^"\']*)["\']', player_html, re.IGNORECASE)
            if file_match:
                video_url = file_match.group(1).replace("\\/", "/")
                vp.play_from_direct_link(video_url + "|Referer=" + embed_url)
                return

            iframe_match = re.findall(
                r"""<iframe.+?src\s*=\s*["']([^'"]+)""",
                player_html,
                re.DOTALL | re.IGNORECASE,
            )
            if iframe_match:
                embed_url = iframe_match[0]
                if embed_url.startswith("//"):
                    embed_url = "https:" + embed_url
                elif embed_url.startswith("/"):
                    embed_url = urllib_parse.urljoin(site.url, embed_url)

    if embed_url:
        if vp.resolveurl.HostedMediaFile(embed_url):
            vp.play_from_link_to_resolve(embed_url)
        else:
            vp.play_from_direct_link(embed_url + "|Referer=" + url)
    else:
        vp.play_from_link_to_resolve(url)


@site.register()
def Categories(url):
    html = utils.getHtml(url)
    soup = utils.parse_html(html)
    for item in soup.select(".video.category, article"):
        link = item.select_one("a[href]")
        if not link:
            continue

        caturl = utils.safe_get_attr(link, "href", default="")
        search_term = _extract_search_term(caturl)
        if not search_term:
            continue

        name = utils.cleantext(utils.safe_get_text(item.select_one("h2")))
        img_tag = item.select_one("img")
        img = utils.get_thumbnail(img_tag)
        if img and img.startswith("/"):
            img = urllib_parse.urljoin(site.url, img)

        site.add_dir(name, search_term, "List", img)

    _add_next_page_from_soup(soup, url, "Categories")
    utils.eod()


@site.register()
def Studios(url):
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    for item in soup.select("article"):
        link = item.select_one("a[href]")
        if not link:
            continue

        sturl = urllib_parse.urljoin(
            site.url, utils.safe_get_attr(link, "href", default="")
        )
        name = utils.cleantext(utils.safe_get_text(item.select_one("h2")))
        if not sturl or not name:
            continue
        site.add_dir(name, sturl, "List", "")

    _add_next_page_from_soup(soup, url, "Studios")
    utils.eod()


@site.register()
def Pornstars(url):
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    for item in soup.select("article"):
        link = item.select_one("a[href]")
        if not link:
            continue

        psurl = urllib_parse.urljoin(
            site.url, utils.safe_get_attr(link, "href", default="")
        )
        name = utils.cleantext(utils.safe_get_text(item.select_one("h2")))
        img = _extract_video_image(link, site.url)
        if not psurl or not name:
            continue
        site.add_dir(name, psurl, "List", img)

    _add_next_page_from_soup(soup, url, "Pornstars")
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        List(keyword, page=1)

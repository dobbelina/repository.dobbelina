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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "porntn", "[COLOR hotpink]PornTN[/COLOR]", "https://porntn.com/", "porntn.png"
)


@site.register(default_mode=True)
def Main(url):
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]", site.url + "tags/", "Tags", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/?q={0}",
        "Search",
        site.img_search,
    )
    # The async endpoint now frequently returns 404/empty data; use homepage listing.
    List(site.url, 1)
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml, _ = utils.get_html_with_cloudflare_retry(url, "")
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in porntn: " + str(e))
        return None

    if not listhtml or utils.is_cloudflare_challenge_page(listhtml):
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    if not soup:
        utils.eod()
        return

    for item in soup.select(".item"):
        link = item.select_one("a[href][title]")
        if not link:
            continue

        videopage = utils.safe_get_attr(link, "href", default="")
        if not videopage.startswith("http"):
            videopage = urllib_parse.urljoin(site.url, videopage)

        name = utils.cleantext(
            utils.safe_get_attr(
                link, "title", default=utils.safe_get_text(link, default="")
            )
        )
        img_tag = item.select_one("[data-original]")
        img = utils.safe_get_attr(img_tag, "data-original", ["src"])
        if img:
            if img.startswith("//"):
                img = "https:" + img
            elif not img.startswith("http"):
                img = urllib_parse.urljoin(site.url, img)

        duration = utils.safe_get_text(item.select_one(".duration"), default="")

        contextmenu = []
        contexturl = (
            utils.addon_sys
            + "?mode=porntn.Lookupinfo"
            + "&url="
            + urllib_parse.quote_plus(videopage)
        )
        contextmenu.append(
            ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
        )

        site.add_download_link(
            name,
            videopage,
            "Playvid",
            img,
            name,
            contextm=contextmenu,
            duration=duration,
        )

    next_link = soup.select_one(".next[href]")
    if next_link:
        np = utils.safe_get_attr(next_link, "href", default="")
        np_match = re.search(r"from(?:_videos)?=(\d+)", np)
        next_from = np_match.group(1) if np_match else ""
        nextp = url
        for p in ["from", "from_videos"]:
            nextp = nextp.replace(
                "{}={}".format(p, str(page)), "{}={}".format(p, next_from)
            )
        label = "Next Page ({})".format(next_from) if next_from else "Next Page"
        site.add_dir(label, nextp, "List", site.img_next, page=next_from)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        html, _ = utils.get_html_with_cloudflare_retry(url, site.url)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in porntn: " + str(e))
        vp.progress.close()
        return

    if not html or utils.is_cloudflare_challenge_page(html):
        vp.progress.close()
        return

    # Try to find license code
    license_match = re.search(r"license_code:\s*['\"]([^\"']+)['\"]", html, re.IGNORECASE)
    
    # Try finding the video source directly in the page first
    source_match = re.search(r'<source\s+[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if source_match and not license_match:
        vp.play_from_direct_link(source_match.group(1) + "|referer=" + url)
        return

    if not license_match:
        # Fallback to general html scanner if KVS pattern not found
        vp.play_from_html(html, url)
        return

    vp.play_from_kt_player(html, url)


@site.register()
def Categories(url):
    try:
        cathtml = utils.get_html_with_cloudflare_retry(url, "")[0]
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in porntn: " + str(e))
        return None
    soup = utils.parse_html(cathtml)
    if not soup:
        utils.eod()
        return

    for card in soup.select("a.item[href][title]"):
        catpage = utils.safe_get_attr(card, "href", default="")
        name = utils.cleantext(utils.safe_get_attr(card, "title", default=""))
        videos = utils.safe_get_text(card.select_one(".videos"), default="")
        if not catpage or not name:
            continue

        label = name + (" [COLOR hotpink]({})[/COLOR]".format(videos) if videos else "")
        catpage = (
            catpage
            + "?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1"
        )
        site.add_dir(label, catpage, "List", "", page=1)
    utils.eod()


@site.register()
def Tags(url):
    try:
        taghtml = utils.get_html_with_cloudflare_retry(url, "")[0]
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in porntn: " + str(e))
        return None
    soup = utils.parse_html(taghtml)
    if not soup:
        utils.eod()
        return

    for link in soup.select('a[href*="/tags/"]'):
        tagpage = utils.safe_get_attr(link, "href", default="")
        name = utils.cleantext(utils.safe_get_text(link, default=""))
        if not tagpage or not name:
            continue
        if tagpage.startswith("/"):
            tagpage = site.url.rstrip("/") + tagpage
        tagpage = (
            tagpage
            + "?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1"
        )
        site.add_dir(name, tagpage, "List", "", page=1)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(searchUrl, "Search")
    else:
        List(searchUrl.format(keyword.replace(" ", "-")), 1)


@site.register()
def Lookupinfo(url):
    try:
        html, _ = utils.get_html_with_cloudflare_retry(url, site.url)
    except Exception:
        return
    if not html or utils.is_cloudflare_challenge_page(html):
        return
    soup = utils.parse_html(html)

    categories = []
    for link in soup.select('a[href*="/categories/"]'):
        caturl = utils.safe_get_attr(link, "href", default="")
        catname = utils.cleantext(utils.safe_get_text(link, default=""))
        if caturl and catname and caturl.startswith("https://porntn.com/categories/"):
            caturl = (
                caturl
                + "?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1"
            )
            categories.append(("Cat", catname, caturl))

    if not categories:
        utils.notify("Lookup", "No categories found")
        return

    utils.kodiDB(categories, "porntn.List")

"""
Cumination
Copyright (C) 2015 Whitecream

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
from resources.lib.sites.soup_spec import SoupSiteSpec

site = AdultSite(
    "anybunny",
    "[COLOR hotpink]Anybunny[/COLOR]",
    "https://anybunny.org/",
    "anybunny.png",
    "anybunny",
)

VIDEO_LIST_SPEC = SoupSiteSpec(
    selectors={
        "items": ["a.nuyrfe", 'a[href*="/videos/"]'],
        "url": {"attr": "href"},
        "title": {
            "selector": "img",
            "attr": "alt",
            "text": True,
            "clean": True,
            "fallback_selectors": [None],
        },
        "thumbnail": {
            "selector": "img",
            "attr": "src",
            "fallback_attrs": ["data-src", "data-lazy", "data-original"],
        },
        "pagination": {
            "selectors": [
                {"query": 'a[rel="next"]', "scope": "soup"},
                {"query": "a.next", "scope": "soup"},
            ],
            "text_matches": ["next"],
            "attr": "href",
            "label": "Next Page",
            "mode": "List",
        },
    },
    description="",  # Site rarely exposes meaningful descriptions
)


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]New videos[/COLOR]", site.url + "new/", "List", site.img_cat)
    site.add_dir("[COLOR hotpink]Top videos[/COLOR]", site.url + "top/", "List", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Categories - images[/COLOR]",
        site.url,
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Categories - all[/COLOR]", site.url, "Categories2", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "new/", "Search", site.img_search
    )
    utils.eod()


@site.register()
def List(url):
    listhtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    
    if not listhtml:
        utils.kodilog("anybunny List: Failed to fetch page")
        utils.eod()
        return

    soup = utils.parse_html(listhtml)

    items = []
    for anchor in soup.select('a.nuyrfe[href], a[href*="/view/"], a[href*="/videos/"], a[href*="/too/"]'):
        href = utils.safe_get_attr(anchor, "href")
        if not href or ("/videos/" not in href and "/view/" not in href and "/too/" not in href):
            continue
        video_url = urllib_parse.urljoin(site.url, href)
        img_tag = anchor.find("img")
        thumb = utils.get_thumbnail(img_tag)
        title = utils.cleantext(utils.safe_get_attr(img_tag, "alt"))
        if not title:
            parent = anchor.find_parent("li")
            if parent:
                title = utils.cleantext(utils.safe_get_text(parent.select_one("p.clip")))
        if not title:
            title = utils.cleantext(
                utils.safe_get_attr(anchor, "title") or utils.safe_get_text(anchor)
            )
        if not title:
            continue
            
        if thumb:
            thumb = urllib_parse.urljoin(site.url, thumb)
        else:
            thumb = site.image

        items.append(
            {
                "title": title,
                "url": video_url,
                "thumb": thumb,
            }
        )

    for item in items:
        site.add_download_link(item["title"], item["url"], "Playvid", item["thumb"], item["title"])

    next_link = soup.select_one('a[rel="next"], a.next, a.topbtmsel2r')
    if next_link and next_link.has_attr("href"):
        text = next_link.get_text().strip().lower()
        if not text or "next" in text or text in ("»", ">", "→"):
            next_url = urllib_parse.urljoin(site.url, next_link["href"])
            # Only add pagination if it's NOT a /new/ or /top/ search-like page
            # These pages (e.g. /new/page/N/) are actually searches for "page" 
            # and return identical/stale results.
            if not any(x in url for x in ["/new/", "/top/"]) or "?" in next_link["href"]:
                site.add_dir("Next Page", next_url, "List")

    utils.eod()


def _extract_playerjs_best_url(html_content):
    """Extract the best quality video URL from Playerjs file parameter in HTML.

    Handles two formats:
    - Quality-labelled: file:"[240]url,[360]url,[480]url,[720]url" (picks highest)
    - Multi-source:     file:"m3u8_url :cast:cast_url or mp4_url :cast:cast_url"
    Falls back to bare URL pattern scan if no file: parameter is found.
    """
    file_match = re.search(r'file\s*:\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    if file_match:
        file_val = file_match.group(1)

        # Quality-labelled format: [240]url,[360]url,...
        quality_options = re.findall(r'\[(\d+)\](https?://[^,\[\s"\']+)', file_val)
        if quality_options:
            quality_options.sort(key=lambda x: int(x[0]), reverse=True)
            return quality_options[0][1]

        # Multi-source format: url1 :cast:casturl1 or url2 :cast:casturl2
        mp4_url = None
        m3u8_url = None
        for part in re.split(r'\s+or\s+', file_val):
            primary = part.split(':cast:')[0].strip()
            if '.mp4' in primary.lower() and not mp4_url:
                mp4_url = primary
            elif ('.m3u8' in primary.lower() or '/hls/' in primary.lower()) and not m3u8_url:
                m3u8_url = primary
        if mp4_url or m3u8_url:
            # Prefer mp4: plays without inputstream.adaptive
            return mp4_url or m3u8_url

    # Fallback: scan for bare media URLs
    for pattern in [
        r'(https?://[^\s"\'\\,\]]+\.mp4(?:[^\s"\'\\,\]]*)?)',
        r'(https?://[^\s"\'\\,\]]+\.m3u8(?:[^\s"\'\\,\]]*)?)',
    ]:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            video_url = match.group(1).split(':cast:')[0].strip()
            return video_url

    return None


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)

    vp.progress.update(50, "[CR]Fetching video page...[CR]")
    pagehtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)

    if not pagehtml:
        utils.kodilog("anybunny Playvid: Failed to fetch page")
        return

    # /too/ pages embed the Playerjs file parameter directly in the page HTML
    video_url = _extract_playerjs_best_url(pagehtml)
    if video_url:
        utils.kodilog(f"anybunny Playvid: Found video URL in page: {video_url[:100]}")
        vp.play_from_direct_link(video_url)
        return

    # /view/ pages use an iframe containing the Playerjs player
    iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', pagehtml, re.IGNORECASE)
    if not iframe_match:
        utils.kodilog("anybunny Playvid: No iframe or video found")
        utils.notify("Error", "Could not extract video URL")
        return

    iframe_url = iframe_match.group(1)
    if not iframe_url.startswith('http'):
        iframe_url = urllib_parse.urljoin(site.url, iframe_url)

    utils.kodilog(f"anybunny Playvid: Found iframe: {iframe_url[:100]}")
    vp.progress.update(70, "[CR]Loading player...[CR]")
    iframe_html, _ = utils.get_html_with_cloudflare_retry(iframe_url, referer=url)

    if not iframe_html:
        utils.kodilog("anybunny Playvid: Failed to fetch iframe")
        return

    video_url = _extract_playerjs_best_url(iframe_html)
    if video_url:
        utils.kodilog(f"anybunny Playvid: Found video URL in iframe: {video_url[:100]}")
        vp.play_from_direct_link(video_url)
        return

    utils.kodilog("anybunny Playvid: No video URL found")
    utils.notify("Error", "Could not extract video URL")


@site.register()
def Categories(url):
    cathtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    
    if not cathtml:
        utils.kodilog("anybunny Categories: Failed to fetch page")
        utils.eod()
        return
    soup = utils.parse_html(cathtml)

    categories = []
    for anchor in soup.select("a[href*='/top/']"):
        img_tag = anchor.select_one("img")
        if not img_tag:
            continue

        href = utils.safe_get_attr(anchor, "href")
        if "/top/" not in href:
            continue

        try:
            catid = href.split("/top/", 1)[1]
        except IndexError:
            continue

        name = utils.safe_get_attr(img_tag, "alt")
        if not name:
            name = utils.safe_get_text(anchor)
        name = utils.cleantext(name)
        if not name:
            continue

        img = utils.get_thumbnail(img_tag)
        catpage = urllib_parse.urljoin(site.url, "top/" + catid.lstrip("/"))
        categories.append((name.lower(), name, catpage, img))

    seen = set()
    for _, display_name, catpage, img in sorted(categories):
        if catpage in seen:
            continue
        seen.add(catpage)
        site.add_dir(display_name, catpage, "List", img)
    utils.eod()


@site.register()
def Categories2(url):
    cathtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    
    if not cathtml:
        utils.kodilog("anybunny Categories2: Failed to fetch page")
        utils.eod()
        return
    soup = utils.parse_html(cathtml)

    entries = []
    for anchor in soup.select("a[href*='/top/']"):
        href = utils.safe_get_attr(anchor, "href")
        if "/top/" not in href:
            continue

        try:
            catid = href.split("/top/", 1)[1]
        except IndexError:
            continue

        name = utils.cleantext(utils.safe_get_text(anchor))
        if not name:
            continue

        videos = ""
        for sibling in anchor.next_siblings:
            if isinstance(sibling, str):
                text = sibling.strip()
            else:
                text = utils.safe_get_text(sibling)

            if not text:
                continue

            match = re.search(r"\(([^)]+)\)", text)
            if match:
                videos = match.group(1)
                break

        label = name
        if videos:
            label = f"{name} [COLOR deeppink]({videos})[/COLOR]"

        catpage = urllib_parse.urljoin(site.url, "top/" + catid.lstrip("/"))
        entries.append((name.lower(), label, catpage))

    seen = set()
    for _, label, catpage in sorted(entries):
        if catpage in seen:
            continue
        seen.add(catpage)
        site.add_dir(label, catpage, "List", "")
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "_")
        searchUrl = searchUrl + title
        List(searchUrl)

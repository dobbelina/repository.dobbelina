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

site = AdultSite(
    "anybunny",
    "[COLOR hotpink]Anybunny[/COLOR]",
    "https://anybunny.org/",
    "anybunny.png",
    "anybunny",
)

# Site structure (as of 2026-03):
# - /new/ and /top/ are 404 for plain HTTP; only category pages (/top/{Name})
#   and individual video pages (/too/{id}-{slug}) work with getHtml().
# - Root page / contains 100 category links as a.nuyrfe with /top/{Name} hrefs.
# - Category pages /top/{Name} contain ~119 video links as a.nuyrfe with
#   absolute https://anybunny.org/too/{id}-{slug} hrefs.
# - Pagination on category pages uses <a class='topbtmsel2r' href='...?p=N'>Next</a>.
# - Video pages use Playerjs with file:"<m3u8_url>:cast:<m3u8_url> or <mp4_url>:cast:<mp4_url>"


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


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]", site.url, "Categories2", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "top/", "Search", site.img_search
    )
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    except Exception as exc:
        utils.kodilog("anybunny List: Fetch failed - {}".format(exc))
        listhtml = ""

    if not listhtml:
        utils.kodilog("anybunny List: Failed to fetch page")
        utils.eod()
        return

    soup = utils.parse_html(listhtml)

    # Video items: a.nuyrfe with absolute /too/ hrefs
    for anchor in soup.select("a.nuyrfe[href*='/too/']"):
        href = utils.safe_get_attr(anchor, "href")
        if not href:
            continue
        video_url = urllib_parse.urljoin(site.url, href)
        img_tag = anchor.find("img")
        thumb = utils.get_thumbnail(img_tag)
        title = utils.cleantext(utils.safe_get_attr(img_tag, "alt"))
        if not title:
            title = utils.cleantext(utils.safe_get_attr(anchor, "title") or "")
        if not title:
            continue

        if thumb:
            thumb = urllib_parse.urljoin(site.url, thumb)
        else:
            thumb = site.image

        site.add_download_link(title, video_url, "Playvid", thumb, title)

    # Pagination: a.topbtmsel2r with href and text "Next"
    next_link = soup.select_one("a.topbtmsel2r")
    if next_link and next_link.has_attr("href"):
        text = next_link.get_text().strip().lower()
        if not text or "next" in text or text in ("»", ">", "→"):
            next_url = urllib_parse.urljoin(site.url, next_link["href"])
            site.add_dir("Next Page", next_url, "List")

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)

    vp.progress.update(50, "[CR]Fetching video page...[CR]")
    pagehtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)

    if not pagehtml:
        utils.kodilog("anybunny Playvid: Failed to fetch page")
        return

    # Video pages embed Playerjs with file: parameter containing m3u8/mp4 URLs
    video_url = _extract_playerjs_best_url(pagehtml)
    if video_url:
        utils.kodilog(f"anybunny Playvid: Found video URL in page: {video_url[:100]}")
        vp.play_from_direct_link(video_url)
        return

    # Fallback: look for an iframe containing the player
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
def Categories2(url):
    try:
        cathtml, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    except Exception as exc:
        utils.kodilog("anybunny Categories2: Fetch failed - {}".format(exc))
        cathtml = ""

    if not cathtml:
        utils.kodilog("anybunny Categories2: Failed to fetch page")
        utils.eod()
        return
    soup = utils.parse_html(cathtml)

    entries = []
    # Root page has category links as a.nuyrfe pointing to /top/{Name}
    # (distinguished from video items which point to /too/{id}-{slug})
    for anchor in soup.select("a.nuyrfe"):
        href = utils.safe_get_attr(anchor, "href") or ""
        if "/top/" not in href or "/too/" in href:
            continue

        # Skip the bare /top/ index link
        stripped = href.rstrip("/")
        if stripped.endswith("/top"):
            continue

        try:
            catid = href.split("/top/", 1)[1].strip("/")
        except IndexError:
            continue

        if not catid or any(x in catid.lower() for x in ["dmca", "abuse", "2257", "login"]):
            continue

        img_tag = anchor.find("img")
        name = utils.cleantext(utils.safe_get_attr(img_tag, "alt") if img_tag else "")
        if not name:
            name = utils.cleantext(utils.safe_get_text(anchor))
        if not name:
            # Derive a human-readable name from the URL slug
            name = utils.cleantext(catid.replace("_", " ").title())
        if not name:
            continue

        img = utils.get_thumbnail(img_tag) if img_tag else ""
        if img:
            img = urllib_parse.urljoin(site.url, img)
        catpage = urllib_parse.urljoin(site.url, "top/" + catid)
        entries.append((name.lower(), name, catpage, img))

    seen = set()
    for _, display_name, catpage, img in sorted(entries):
        if catpage in seen:
            continue
        seen.add(catpage)
        site.add_dir(display_name, catpage, "List", img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # Search works by navigating to /top/{keyword}
        title = keyword.replace(" ", "_")
        searchUrl = urllib_parse.urljoin(site.url, "top/" + title)
        List(searchUrl)

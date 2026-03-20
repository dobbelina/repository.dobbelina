"""
Cumination
Copyright (C) 2025 Team Cumination

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

from __future__ import annotations

import base64
import re
from collections import OrderedDict
from typing import Dict, Iterable, List as TList, Optional, Tuple

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite(
    "peachurnet",
    "[COLOR hotpink]PeachUrNet[/COLOR]",
    "https://peachurnet.com/",
    "peachurnet.png",
    "peachurnet",
)

HOME_CACHE: Dict[str, Optional[Iterable]] = {
    "sections": None,
    "search": None,
}

VIDEO_HOST_PATTERN = re.compile(
    r'https?://[^"\']+?(?:m3u8|mp4|m4v|webm)', re.IGNORECASE
)
STYLE_URL_PATTERN = re.compile(r"url\(['\"]?(?P<url>[^)\'\"]+)['\"]?\)")
DURATION_CLASSES = re.compile(r"duration|length", re.IGNORECASE)
META_CLASSES = re.compile(r"(meta|info|date|views|category)", re.IGNORECASE)


def _home_url() -> str:
    return urllib_parse.urljoin(site.url, "en")


def _ensure_headers() -> Dict[str, str]:
    headers = utils.base_hdrs.copy()
    headers["Referer"] = site.url
    headers["Origin"] = site.url.rstrip("/")
    return headers


def _absolute_url(url: str, base: Optional[str] = None) -> str:
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http"):
        return url
    base_url = base or site.url
    return urllib_parse.urljoin(base_url, url.lstrip("/"))


def _clean_image(img: str) -> str:
    if not img:
        return ""
    img = img.strip()
    if " " in img and img.startswith("http"):
        img = img.split(" ")[0]
    if img.startswith("//"):
        img = "https:" + img
    if img.startswith("/"):
        img = urllib_parse.urljoin(site.url, img.lstrip("/"))
    return img


def _extract_from_style(style_value: str) -> str:
    if not style_value:
        return ""
    match = STYLE_URL_PATTERN.search(style_value)
    return _clean_image(match.group("url")) if match else ""


def _cache_homepage_metadata(force: bool = False) -> None:
    global HOME_CACHE
    if (
        HOME_CACHE["sections"] is not None
        and HOME_CACHE["search"] is not None
        and not force
    ):
        return

    try:
        html = utils.getHtml(_home_url(), headers=_ensure_headers())
    except (
        Exception
    ) as exc:  # pragma: no cover - network/runtime issues surfaced to Kodi UI
        utils.kodilog("peachurnet Main load error: {}".format(exc))
        HOME_CACHE["sections"] = []
        HOME_CACHE["search"] = urllib_parse.urljoin(site.url, "en/search?q=")
        return

    soup = utils.parse_html(html)
    sections: TList[Tuple[str, str]] = []
    seen = set()

    for anchor in soup.select("nav a[href], header a[href]"):
        label = utils.safe_get_text(anchor)
        href = utils.safe_get_attr(anchor, "href")
        if not label or not href:
            continue
        label = label.strip()
        href = href.strip()
        if len(label) < 2 or label.lower() in {"home", "blog", "sign in", "login"}:
            continue
        if "/video/" in href or href.startswith("#"):
            continue
        full_url = _absolute_url(href)
        if not full_url.startswith(site.url):
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        sections.append((label, full_url))

    HOME_CACHE["sections"] = sections
    HOME_CACHE["search"] = _discover_search_endpoint(soup)


def _discover_search_endpoint(soup) -> str:
    fallback = urllib_parse.urljoin(site.url, "en/search?q=")
    for form in soup.find_all("form"):
        method_attr = utils.safe_get_attr(form, "method")
        method = method_attr.lower() if method_attr else "get"
        if method != "get":
            continue
        input_tag = form.find(
            "input", attrs={"name": re.compile("q|keyword|search", re.IGNORECASE)}
        )
        if not input_tag:
            continue
        action = utils.safe_get_attr(form, "action", default="") or "/en/search"
        base = _absolute_url(action)
        query_name = input_tag.get("name", "q")
        separator = "&" if "?" in base else "?"
        return f"{base}{separator}{query_name}="
    return fallback


def _extract_title(element) -> str:
    if not element:
        return ""

    # First try specific title selectors
    for selector in [
        ".title",
        ".video-title",
        ".name",
        ".video-name",
        "h3",
        "h2",
        "h4",
    ]:
        node = element.select_one(selector)
        if node:
            title = utils.safe_get_text(node)
            if title and len(title) > 3:  # Ensure it's not just "..." or similar
                return title

    # Try img alt attribute as fallback (common pattern)
    img = element.select_one("img")
    if img:
        alt = utils.safe_get_attr(img, "alt")
        if alt and len(alt) > 3 and not re.match(r"^\d+:\d+$", alt):  # Not a duration
            return alt

    # Try title attribute on the link itself
    link_title = utils.safe_get_attr(element, "title")
    if link_title and len(link_title) > 3:
        return link_title

    # Try aria-label
    aria_label = utils.safe_get_attr(element, "aria-label")
    if aria_label and len(aria_label) > 3:
        return aria_label

    # Last resort: get all text but filter out duration-only patterns
    all_text = utils.safe_get_text(element)
    if all_text:
        # Split by newlines/spaces and find the longest meaningful text
        parts = [p.strip() for p in re.split(r"[\n\r]+", all_text) if p.strip()]
        for part in parts:
            # Skip if it's just a duration (MM:SS or HH:MM:SS)
            if re.match(r"^\d+:\d+(?::\d+)?$", part):
                continue
            # Skip if it's just numbers and separators
            if re.match(r"^[\d\s\-\|:]+$", part):
                continue
            # Skip very short parts
            if len(part) < 4:
                continue
            return part

    return ""


def _extract_thumbnail(element) -> str:
    img_tag = element.select_one("img")
    if img_tag:
        thumb = utils.safe_get_attr(
            img_tag,
            "data-src",
            ["data-original", "data-lazy-src", "src", "data-srcset", "srcset"],
        )
        if thumb and " " in thumb and thumb.startswith("http"):
            thumb = thumb.split(" ")[0]
        if thumb:
            return _clean_image(thumb)
    style_thumb = _extract_from_style(utils.safe_get_attr(element, "style"))
    if style_thumb:
        return style_thumb
    parent = element.find_parent()
    if parent:
        return _extract_thumbnail(parent)
    return ""


def _extract_duration(element) -> str:
    for target in (element, element.find_parent() if element else None):
        if not target:
            continue
        attr_duration = target.get("data-duration") or target.get("data-length")
        if attr_duration:
            return attr_duration.strip()
        duration_tag = target.find(attrs={"class": DURATION_CLASSES})
        if duration_tag:
            duration = utils.safe_get_text(duration_tag)
            if duration:
                return duration
    return ""


def _extract_metadata(element) -> str:
    parent = element.find_parent()
    meta_bits: TList[str] = []
    search_target = parent if parent else element
    if not search_target:
        return ""
    for meta_tag in search_target.find_all(["span", "div", "time"], limit=6):
        css = " ".join(meta_tag.get("class", []))
        if css and META_CLASSES.search(css):
            text = utils.safe_get_text(meta_tag)
            if text:
                meta_bits.append(text)
                continue
        if meta_tag.name == "time":
            meta_bits.append(utils.safe_get_text(meta_tag))
    joined = " | ".join(bit for bit in meta_bits if bit)
    return joined


def _parse_video_cards(soup) -> TList[Dict[str, str]]:
    cards: TList[Dict[str, str]] = []
    seen = set()
    for link in soup.select('a[href*="/video/"]'):
        href = utils.safe_get_attr(link, "href")
        if not href:
            continue
        href = href.split("#")[0]
        if "/video/" not in href:
            continue
        key = href
        if key in seen:
            continue
        seen.add(key)
        title = utils.cleantext(_extract_title(link))
        if not title:
            continue
        thumb = _extract_thumbnail(link)
        duration = _extract_duration(link)
        meta = _extract_metadata(link)
        plot_parts = [title]
        if duration:
            plot_parts.append(f"Duration: {duration}")
        if meta:
            plot_parts.append(meta)
        plot = "\n".join(plot_parts)
        cards.append(
            {
                "title": title,
                "url": _absolute_url(href),
                "thumb": thumb,
                "plot": plot,
            }
        )
    return cards


def _find_next_page(soup, current_url: str) -> str:
    selectors = [
        'a[rel="next"]',
        'a[aria-label*="next" i]',
        ".pagination a.next",
        "li.next a",
    ]
    for selector in selectors:
        link = soup.select_one(selector)
        if link:
            href = utils.safe_get_attr(link, "href")
            if href:
                return _absolute_url(href, current_url)
    for link in soup.find_all("a", string=re.compile("next", re.IGNORECASE)):
        href = utils.safe_get_attr(link, "href")
        if href:
            return _absolute_url(href, current_url)
    return ""


def _decode_base64_var(value: str) -> str:
    """Decode a double base64-encoded value."""
    if not value:
        return ""
    try:
        # First decode
        first_decode = base64.b64decode(value).decode("utf-8")
        # Second decode
        second_decode = base64.b64decode(first_decode).decode("utf-8")
        return second_decode
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in peachurnet: " + str(e))
        return ""


def _extract_peachurnet_video_url(html: str) -> str:
    """
    Extract video URL from PeachUrNet's obfuscated JavaScript variables.

    The site uses double base64 encoding:
    - var sy = base64(base64(request_url))
    - var syt = base64(base64(path))
    - Full URL = decoded_sy + "/" + decoded_syt
    """
    # Look for the JavaScript variables
    sy_match = re.search(r'var\s+sy\s*=\s*"([^"]+)"', html)
    syt_match = re.search(r'var\s+syt\s*=\s*"([^"]+)"', html)

    if not sy_match or not syt_match:
        return ""

    # Decode the variables
    request_url = _decode_base64_var(sy_match.group(1))
    path_suffix = _decode_base64_var(syt_match.group(1))

    if not request_url or not path_suffix:
        utils.kodilog("peachurnet: Failed to decode video URL variables")
        return ""

    # Construct full video URL
    video_url = "{}/{}".format(request_url, path_suffix)
    utils.kodilog("peachurnet: Decoded video URL from JavaScript: {}".format(video_url))
    return video_url


def _gather_video_sources(html: str, base_url: str) -> OrderedDict:
    soup = utils.parse_html(html)
    sources: OrderedDict[str, str] = OrderedDict()

    def _add_source(src: str, label: str = None):
        if not src:
            return
        # Clean up the source URL
        src = src.strip().strip('"').strip("'")
        link = _absolute_url(src, base_url)
        if not link or link in sources.values():
            return
        # Skip invalid links
        if not link.startswith("http"):
            return
        # Skip placeholder URLs
        if link.endswith("/data/video.mp4") or "/data/video.mp4" in link:
            utils.kodilog("peachurnet: Skipping placeholder URL: {}".format(link))
            return
        host = label or utils.get_vidhost(link)
        sources[host] = link

    # PRIORITY 1: Try to extract from obfuscated JavaScript variables
    js_video_url = _extract_peachurnet_video_url(html)
    if js_video_url:
        _add_source(js_video_url, label="MP4")

    # Try video tags with source children
    for tag in soup.select("video source[src], video source[data-src]"):
        _add_source(
            utils.safe_get_attr(
                tag, "src", ["data-src", "data-hls", "data-mp4", "data-quality-src"]
            )
        )

    # Try video tags with src directly
    for tag in soup.select("video[src], video[data-src]"):
        _add_source(utils.safe_get_attr(tag, "src", ["data-src"]))

    # Try data attributes on various elements
    for tag in soup.select(
        "[data-src], [data-hls], [data-mp4], [data-video], [data-video-src]"
    ):
        _add_source(
            utils.safe_get_attr(
                tag,
                "data-src",
                ["data-hls", "data-mp4", "data-video", "data-video-src"],
            )
        )

    # Try iframes (common for embedded players)
    for iframe in soup.select("iframe[src]"):
        iframe_src = utils.safe_get_attr(iframe, "src")
        # Skip iframe if it looks like an ad or tracking
        if iframe_src and not any(
            x in iframe_src.lower()
            for x in ["ads", "analytics", "tracking", "doubleclick"]
        ):
            _add_source(iframe_src, label="Embedded Player")

    # Search for video URLs in JavaScript/HTML using regex
    # Look for quoted URLs ending in video extensions (but skip placeholders)
    video_patterns = [
        r'"(https?://[^"]+\.(?:mp4|m3u8|m4v|webm)[^"]*)"',
        r"'(https?://[^']+\.(?:mp4|m3u8|m4v|webm)[^']*)'",
        r'src:\s*["\']([^"\']+\.(?:mp4|m3u8))',
        r'file:\s*["\']([^"\']+\.(?:mp4|m3u8))',
        r'source:\s*["\']([^"\']+\.(?:mp4|m3u8))',
    ]

    for pattern in video_patterns:
        for match in re.findall(pattern, html, re.IGNORECASE):
            _add_source(match)

    # Last resort: find any video URLs in the HTML
    for match in VIDEO_HOST_PATTERN.findall(html):
        _add_source(match)

    # Log what we found for debugging
    if sources:
        utils.kodilog("peachurnet: Found {} video source(s)".format(len(sources)))
    else:
        utils.kodilog("peachurnet: No video sources found in page")

    return sources


@site.register(default_mode=True)
def Main():
    _cache_homepage_metadata()
    site.add_dir(
        "[COLOR hotpink]Latest Updates[/COLOR]", _home_url(), "List", site.img_cat
    )
    sections = HOME_CACHE.get("sections") or []
    for label, url in sections:
        site.add_dir(f"[COLOR hotpink]{label}[/COLOR]", url, "List", site.img_cat)
    search_url = HOME_CACHE.get("search") or urllib_parse.urljoin(
        site.url, "en/search?q="
    )
    site.add_dir("[COLOR hotpink]Search[/COLOR]", search_url, "Search", site.img_search)
    utils.eod()


@site.register()
def List(url):
    target_url = _absolute_url(url)
    try:
        html = utils.getHtml(target_url, headers=_ensure_headers())
    except Exception as exc:  # pragma: no cover - surfaced to Kodi UI
        utils.kodilog("peachurnet List load error: {}".format(exc))
        utils.notify("PeachUrNet", "Unable to load listing page")
        utils.eod()
        return

    soup = utils.parse_html(html)
    videos = _parse_video_cards(soup)

    if not videos:
        utils.notify("PeachUrNet", "No videos found on this page")

    for video in videos:
        site.add_download_link(
            video["title"], video["url"], "Playvid", video["thumb"], video["plot"]
        )

    next_page = _find_next_page(soup, target_url)
    if next_page:
        site.add_dir(
            "[COLOR hotpink]Next Page...[/COLOR]", next_page, "List", site.img_next
        )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    _cache_homepage_metadata()
    search_base = HOME_CACHE.get("search") or urllib_parse.urljoin(
        site.url, "en/search?q="
    )
    if not keyword:
        site.search_dir(search_base, "Search")
        return
    search_url = f"{search_base}{urllib_parse.quote_plus(keyword)}"
    List(search_url)


@site.register()
def Playvid(url, name, download=None):
    videopage = _absolute_url(url)
    utils.kodilog("peachurnet: Playing video from {}".format(videopage))
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        html = utils.getHtml(videopage, headers=_ensure_headers())
        utils.kodilog("peachurnet: Fetched video page ({} bytes)".format(len(html)))
    except Exception as exc:  # pragma: no cover - surfaced to Kodi UI
        utils.kodilog("peachurnet Playvid load error: {}".format(exc))
        vp.progress.close()
        utils.notify("PeachUrNet", "Unable to load video page")
        return

    vp.progress.update(50, "[CR]Searching for video sources[CR]")
    sources = _gather_video_sources(html, videopage)

    if not sources:
        vp.progress.close()
        # Check if page requires authentication
        if (
            "/login" in html
            or 'href="https://peachurnet.com/en/login"' in html
            or "sign in" in html.lower()
        ):
            utils.kodilog("PeachUrNet: Video page appears to require login")
            utils.notify(
                "PeachUrNet",
                "This video may require login or is unavailable",
                time=5000,
            )
        else:
            utils.kodilog("PeachUrNet: No video sources found for {}".format(videopage))
            # Save HTML for debugging if needed
            import os

            try:
                debug_path = os.path.join(
                    os.path.expanduser("~"), "peachurnet_debug.html"
                )
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html)
                utils.kodilog("PeachUrNet: Saved debug HTML to {}".format(debug_path))
                utils.notify(
                    "PeachUrNet", "No playable sources found - check logs", time=5000
                )
            except Exception as e:  # pragma: no cover
                utils.kodilog("@@@@Cumination: failure in peachurnet: " + str(e))
                utils.notify("PeachUrNet", "No playable sources found")
        return

    utils.kodilog(
        "peachurnet: Found {} video source(s): {}".format(
            len(sources), list(sources.keys())
        )
    )

    videourl = utils.selector("Select source", sources)
    if not videourl:
        vp.progress.close()
        return

    utils.kodilog("peachurnet: Selected source: {}".format(videourl))
    # Use play_from_direct_link for direct MP4 URLs instead of play_from_link_to_resolve
    # since hostmediaplus.com is not a recognized host in resolveurl
    vp.play_from_direct_link(videourl + "|Referer=" + videopage)

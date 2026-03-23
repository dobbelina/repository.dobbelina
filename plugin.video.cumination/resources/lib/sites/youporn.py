"""
Cumination
Copyright (C) 2024 Team Cumination

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
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "youporn",
    "[COLOR hotpink]YouPorn[/COLOR]",
    "https://www.youporn.com/",
    "youporn.png",
    "youporn",
)
cookiehdr = {"Cookie": "age_verified=1"}


def _normalize_thumb(url):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return url


def _get_listing_thumbnail(item, link):
    img_tag = item.select_one("img.thumb-image, img")
    if img_tag:
        poster = utils.safe_get_attr(
            img_tag,
            "data-poster",
            ["poster", "data-preview", "data-thumb_url", "data-thumb-url"],
        )
        if poster:
            return _normalize_thumb(poster)

    img = utils.get_thumbnail(img_tag)
    if img:
        return _normalize_thumb(img)

    img = utils.safe_get_attr(
        item,
        "data-thumbnail",
        ["data-poster", "poster", "data-src", "data-original", "thumb", "data-thumb"],
    )
    if img:
        return _normalize_thumb(img)

    img = utils.safe_get_attr(
        link,
        "data-thumbnail",
        ["data-poster", "poster", "data-src", "data-original", "thumb", "data-thumb"],
    )
    return _normalize_thumb(img)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    # Show newest videos by default
    List(site.url + "browse/time/")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url, cookiehdr)

    if not listhtml or "Error Page Not Found" in listhtml:
        utils.eod()
        return

    # Parse HTML with BeautifulSoup
    soup = utils.parse_html(listhtml)

    # Extract video items - keep selectors broad for homepage/search/category variants.
    video_items = soup.select(
        ".video-box, .js_video-box, .thumbnail-card, li.videoBox, div.videoBox"
    )
    seen = set()

    for item in video_items:
        try:
            # Get the link element
            link = item.select_one(
                "a.video-box-image, a.tm_video_item, a.video-box-link, a[href*='/watch/']"
            )
            if not link:
                continue

            # Extract video URL
            video_url = utils.safe_get_attr(link, "href")
            if not video_url or "/watch/" not in video_url:
                continue

            # Make absolute URL if needed
            if video_url.startswith("/"):
                video_url = site.url[:-1] + video_url
            normalized = urllib_parse.urlsplit(video_url)
            normalized_url = urllib_parse.urlunsplit(
                (normalized.scheme, normalized.netloc, normalized.path, "", "")
            )
            if normalized_url in seen:
                continue
            seen.add(normalized_url)

            # Extract title from the title link
            title_link = item.select_one(".video-title-text span")
            title = utils.safe_get_text(title_link) if title_link else ""
            if not title:
                # Fallback to image alt attribute
                img_tag = item.select_one("img.thumb-image")
                title = utils.safe_get_attr(img_tag, "alt") if img_tag else "Video"

            # Extract thumbnail image
            img = _get_listing_thumbnail(item, link)

            # Extract duration
            duration_tag = item.select_one(
                ".video-duration span, .tm_video_duration span, .video-duration, .duration"
            )
            duration = utils.safe_get_text(duration_tag).replace("\xa0", " ").strip()
            if not duration:
                duration = utils.safe_get_attr(item, "data-duration")
            duration_seconds = _duration_to_seconds(duration)
            if duration_seconds is not None and 0 < duration_seconds < 60:
                continue

            # Add video to list
            site.add_download_link(
                title, video_url, "Playvid", img, "", duration=duration
            )

        except Exception as e:
            # Log error but continue processing other videos
            utils.kodilog("YouPorn: Error parsing video item: " + str(e))
            continue

    # Extract pagination (Next Page link)
    # YouPorn uses pagination with page numbers
    next_page = soup.select_one(
        ".pagination_pages_list a.tm_pagination_link:last-of-type"
    )
    if next_page:
        next_url = utils.safe_get_attr(next_page, "href")
        if next_url and "page=" in next_url:
            # Extract page number for display
            page_match = re.search(r"page=(\d+)", next_url)
            page_num = page_match.group(1) if page_match else ""

            # Build next page URL
            if next_url.startswith("/"):
                next_url = site.url[:-1] + next_url

            site.add_dir(
                "Next Page ({})".format(page_num), next_url, "List", site.img_next
            )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = urllib_parse.quote_plus(keyword)
        searchUrl = site.url + "search/?query=" + title
        List(searchUrl)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url, cookiehdr)

    if not cathtml:
        utils.eod()
        return

    soup = utils.parse_html(cathtml)

    # YouPorn uses class="categoryBox" for category items
    categories = soup.select(".categoryBox")

    entries = []
    for category in categories:
        try:
            catpage = utils.safe_get_attr(category, "href")
            if not catpage:
                continue

            if catpage.startswith("/"):
                catpage = site.url[:-1] + catpage

            # Extract category name
            name_tag = category.select_one(".tm_category_title")
            if name_tag:
                # Get only the text, not the subtitle
                name_parts = list(name_tag.stripped_strings)
                name = name_parts[0] if name_parts else ""
            else:
                name = utils.safe_get_attr(category, "alt")

            if not name:
                continue

            # Extract thumbnail
            img_tag = category.select_one("img")
            img = utils.get_thumbnail(img_tag)
            if img and img.startswith("//"):
                img = "https:" + img

            entries.append((name, catpage, img, name.lower()))

        except Exception as e:
            utils.kodilog("YouPorn: Error parsing category: " + str(e))
            continue

    # Sort alphabetically
    entries.sort(key=lambda item: item[3])

    for display_name, catpage, img, _ in entries:
        site.add_dir(display_name, catpage, "List", img, "")

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url, cookiehdr)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    src = _extract_best_source(html)
    if src:
        # Use the actual page as referer to satisfy Aylo CDN checks
        vp.play_from_direct_link("{0}|Referer={1}".format(src, url))
    else:
        vp.play_from_link_to_resolve(url)


def _extract_best_source(html):
    # Aylo sites expose mediaDefinition JSON with videoUrl entries
    match = re.search(r'mediaDefinition["\']?\s*:\s*(\[.*?\])', html, re.DOTALL)
    candidates = []
    if match:
        try:
            items = json.loads(match.group(1).replace("\\/", "/"))
            for item in items:
                url = item.get("videoUrl") or item.get("videoUrlMain")
                if not url:
                    continue

                # If URL is a manifest endpoint, fetch it to get actual video URLs
                if "/media/mp4/" in url or "/media/hls/" in url:
                    try:
                        manifest_data = utils.getHtml(url, site.url)
                        if manifest_data:
                            manifest_json = json.loads(manifest_data)
                            # Extract video URLs from manifest
                            for video in manifest_json:
                                video_url = video.get("videoUrl", "")
                                video_quality = video.get("quality", "")
                                if video_url:
                                    candidates.append((str(video_quality), video_url))
                    except Exception as e:
                        utils.kodilog("YouPorn: Error fetching manifest: " + str(e))
                        # Continue with the manifest URL itself as fallback
                        quality = (
                            item.get("quality") or item.get("defaultQuality") or ""
                        )
                        candidates.append((str(quality), url))
                else:
                    quality = item.get("quality") or item.get("defaultQuality") or ""
                    candidates.append((str(quality), url))
        except Exception as e:
            utils.kodilog("YouPorn: Error parsing mediaDefinition: " + str(e))

    if not candidates:
        # Fallback: look for quality/url pairs used by Aylo inline JSON
        for quality, src in re.findall(
            r'"(?:quality|label)"\s*:\s*"?(\d{3,4})p?"?.*?"(?:videoUrl|src|url)"\s*:\s*"([^"]+)',
            html,
            re.IGNORECASE | re.DOTALL,
        ):
            candidates.append((quality, src.replace("\\/", "/")))

    if not candidates:
        # Fallback: look for <source> tags or any direct mp4/m3u8 references
        for src in re.findall(
            r"<source[^>]+src=[\"\\\']([^\"\\\']+)", html, re.IGNORECASE
        ):
            if any(ext in src for ext in (".mp4", ".m3u8")):
                candidates.append(("", src.replace("\\/", "/")))
        for src in re.findall(
            r'https?://[^"\\\']+\.(?:mp4|m3u8)[^"\\\']*', html, re.IGNORECASE
        ):
            candidates.append(("", src.replace("\\/", "/")))

    if not candidates:
        return ""

    def score(item):
        label = item[0]
        digits = "".join(ch for ch in label if ch.isdigit())
        return int(digits) if digits else 0

    best = sorted(candidates, key=score, reverse=True)[0][1]
    if best.startswith("//"):
        best = "https:" + best
    return best


def _duration_to_seconds(duration):
    if not duration:
        return None

    parts = [p.strip() for p in duration.split(":") if p.strip()]
    if not parts:
        return None

    try:
        values = [int(p) for p in parts]
    except (ValueError, TypeError):
        return None

    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return values[0] * 60 + values[1]
    if len(values) == 3:
        return values[0] * 3600 + values[1] * 60 + values[2]
    return None

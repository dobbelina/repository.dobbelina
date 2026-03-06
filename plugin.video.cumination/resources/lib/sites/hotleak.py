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
import base64
import json
import os
import time
import requests
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite(
    "hotleak",
    "[COLOR hotpink]Hotleak[/COLOR]",
    "https://hotleak.vip/",
    "hotleak.png",
    "hotleak",
)

@site.register(default_mode=True)
def Main(url):
    site.add_dir("[COLOR hotpink]Videos[/COLOR]", site.url + "videos", "List", "")
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search?search=", "Search", site.img_search
    )
    utils.eod()


@site.register()
def List(url, page=1):
    listhtml = ""
    try:
        listhtml, _ = utils.get_html_with_cloudflare_retry(
            url, referer=site.url, retry_on_empty=True
        )
    except Exception:
        listhtml = ""
    if not listhtml:
        listhtml = utils.getHtml(url, site.url)
    if not listhtml:
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    items = soup.select("article.movie-item, article[class*='movie-item']")
    if not items:
        # Fallback layout: derive entries directly from video/profile links.
        items = soup.select("a[href*='/video/'], a[href*='/photo/']")

    for item in items:
        link = item if getattr(item, "name", "") == "a" else item.select_one("a[href]")
        videopage = utils.safe_get_attr(link, "href")
        if not videopage or "tantaly.com" in videopage: # Skip ads
            continue
        videopage = urllib_parse.urljoin(site.url, videopage)
        is_video = "/video/" in videopage
        is_photo = "/photo/" in videopage
        if is_photo:
            # Ignore photo posts in video listings.
            continue

        img_tag = (
            item.select_one("img.post-thumbnail, img")
            if getattr(item, "name", "") != "a"
            else item.select_one("img")
        )
        img = utils.safe_get_attr(img_tag, "data-src", ["data-original", "srcset", "src"])
        if img and img.startswith("data:image"):
            img = utils.safe_get_attr(img_tag, "data-src", ["data-original", "src"])
        if img and "," in img and " " in img:
            img = img.split(",")[0].strip().split(" ")[0].strip()
        if img:
            img = urllib_parse.urljoin(site.url, img)
            img = img + "|User-Agent=" + utils.USER_AGENT

        name = utils.safe_get_text(
            item.select_one(".movie-name h3, .movie-name, .post-title, .title")
            if getattr(item, "name", "") != "a"
            else None
        )
        if not name:
            name = utils.safe_get_attr(img_tag, "alt", default="Video")
        if not name:
            name = utils.safe_get_attr(link, "title")
        name = re.sub(r"\s+\d{5,}\s*$", "", name).strip()
        if not name:
            name = "Video"

        date = utils.safe_get_text(item.select_one(".date"))
        views = utils.safe_get_text(item.select_one(".view"))
        meta = []
        if date:
            meta.append(date)
        if views:
            meta.append(views)
        description = " | ".join(meta)

        if is_video:
            site.add_download_link(
                name, videopage, "Playvid", img, desc=description
            )
        else:
            # Search results often return profile pages; open them as folders.
            site.add_dir(name, videopage, "List", img, desc=description)

    # Next Page
    next_el = soup.select_one(
        "a.page-link[rel='next'], ul.pagination a[rel='next'], a[aria-label='Next'], a.next"
    )
    if next_el:
        np_url = utils.safe_get_attr(next_el, "href")
        if np_url:
            np_url = urllib_parse.urljoin(site.url, np_url)
            page_match = re.search(r"page=(\d+)", np_url)
            np = page_match.group(1) if page_match else str(int(page) + 1)
            site.add_dir("Next Page ({})".format(np), np_url, "List", site.img_next, page=np)

    utils.eod()


def _decrypt_video_url(encrypted_url):
    """
    Decrypt hotleak video URL.

    The site uses client-side encryption that:
    1. Removes first 8 characters
    2. Removes last 16 characters
    3. Reverses the string
    4. Base64 decodes the result

    Args:
        encrypted_url: Encrypted URL from data-video attribute

    Returns:
        Decrypted M3U8 URL
    """
    try:
        # Remove first 8 chars
        decrypted = encrypted_url[8:]
        # Remove last 16 chars
        decrypted = decrypted[:-16]
        # Reverse the string
        decrypted = decrypted[::-1]
        # Base64 decode
        decrypted = base64.b64decode(decrypted).decode('utf-8')
        return decrypted
    except Exception as e:
        utils.kodilog("hotleak: URL decryption failed: {}".format(e))
        return None


def _write_local_manifest(manifest_url):
    """
    Fetch one-time manifest URL once, then write a local playlist file.
    This avoids token reuse failures caused by repeated remote manifest requests.
    """
    try:
        response = requests.get(
            manifest_url,
            timeout=15,
            headers={"User-Agent": utils.USER_AGENT, "Referer": site.url},
        )
        if response.status_code != 200:
            utils.kodilog(
                "hotleak: Manifest fetch failed (status {}): {}".format(
                    response.status_code, manifest_url[:120]
                )
            )
            return ""
        manifest = response.text
        if "#EXTM3U" not in manifest:
            utils.kodilog("hotleak: Invalid manifest content")
            return ""

        # Rewrite all relative references in both media lines and URI="..."
        # attributes so Kodi can resolve them from a local temp file.
        uri_attr_pattern = re.compile(r'URI="([^"]+)"')
        rewritten = []
        for line in manifest.splitlines():
            stripped = line.strip()
            if not stripped:
                rewritten.append("")
                continue

            if stripped.startswith("#"):
                def _replace_uri(match):
                    value = match.group(1)
                    return 'URI="{0}"'.format(urllib_parse.urljoin(manifest_url, value))

                rewritten.append(uri_attr_pattern.sub(_replace_uri, stripped))
                continue

            rewritten.append(urllib_parse.urljoin(manifest_url, stripped))

        temp_dir = utils.TRANSLATEPATH("special://temp")
        local_path = os.path.join(
            temp_dir, "hotleak_{0}.m3u8".format(int(time.time() * 1000))
        )
        with open(local_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(rewritten))

        # Kodi can be inconsistent with directly opening local .m3u8 from add-ons.
        # Wrap the local manifest in a parent playlist file for better compatibility.
        parent_path = os.path.join(
            temp_dir, "hotleak_parent_{0}.mp4".format(int(time.time() * 1000))
        )
        parent_manifest = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-STREAM-INF:PROGRAM-ID=1\n"
            "{0}".format(local_path)
        )
        with open(parent_path, "w", encoding="utf-8") as handle:
            handle.write(parent_manifest)
        return parent_path
    except Exception as e:
        utils.kodilog("hotleak: Failed to materialize manifest: {}".format(e))
        return ""


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    # Skip inputstream.adaptive - the m3u8 server rejects HEAD requests (403)
    # and rejects Referer headers. Let Kodi's FFMpeg handle the HLS directly.
    vp.IA_check = "skip"

    # Get HTML page
    html = utils.getHtml(url)
    soup = utils.parse_html(html)

    # Look for video data in data-video attributes
    video_items = soup.select('[data-video]')

    for item in video_items:
        data_video = utils.safe_get_attr(item, 'data-video')
        if not data_video:
            continue

        try:
            video_json = json.loads(data_video)

            # Extract encrypted URL from JSON
            if 'source' in video_json and len(video_json['source']) > 0:
                encrypted_url = video_json['source'][0].get('src', '')

                if encrypted_url:
                    # Decrypt the URL
                    vp.progress.update(50, "[CR]Decrypting video URL[CR]")
                    video_url = _decrypt_video_url(encrypted_url)

                    if video_url:
                        utils.kodilog("hotleak: Decrypted URL: {}".format(video_url))
                        local_manifest = _write_local_manifest(video_url)
                        if local_manifest:
                            utils.kodilog(
                                "hotleak: Playing local manifest: {}".format(local_manifest)
                            )
                            vp.play_from_direct_link(local_manifest)
                        else:
                            # Fallback if local manifest materialization failed.
                            vp.play_from_direct_link(video_url)
                        return

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            utils.kodilog("hotleak: Failed to parse video data: {}".format(e))
            continue

    # If we get here, we couldn't find/decrypt the video URL
    utils.kodilog("hotleak: Could not extract video URL from page")
    vp.progress.close()
    utils.notify("Error", "Could not find video URL")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        search_url = site.url + "search?search=" + urllib_parse.quote(keyword)
        List(search_url)

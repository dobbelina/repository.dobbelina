"""
Cumination site scraper
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

import re
from six.moves import urllib_parse, html_parser
from resources.lib import utils
from resources.lib.adultsite import AdultSite

# Python 2/3 compatible HTML entity decoder
try:
    import html

    unescape = html.unescape
except ImportError:
    # Python 2
    h = html_parser.HTMLParser()
    unescape = h.unescape

site = AdultSite(
    "livecamrips",
    "[COLOR hotpink]LiveCamRips[/COLOR]",
    "https://www.livecamsrip.com/",
    "livecamrips.png",
    "livecamrips",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search",
        "Search",
        site.img_search,
    )
    List(site.url, 1)
    utils.eod()


@site.register()
def List(url, page=1):
    """List videos from the site"""
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    # livecamsrip.com uses <a href="/watch/[BASE64]"> with <video> preview inside
    # Match both relative (/watch/) and absolute (https://livecamsrip.com/watch/) URLs
    video_links = soup.select('a[href*="/watch/"]')

    utils.kodilog(
        "@@@@Cumination: LiveCamRips found {} video links".format(len(video_links))
    )

    seen = set()
    for link in video_links:
        videopage = utils.safe_get_attr(link, "href")
        if not videopage:
            continue
        videopage = urllib_parse.urljoin(site.url, videopage)

        # Skip duplicates
        if videopage in seen:
            continue
        seen.add(videopage)

        # Extract thumbnail from <video> tag poster attribute
        video_tag = link.select_one("video.video-splash-mov")
        img = utils.safe_get_attr(video_tag, "poster") if video_tag else None
        if img and img.startswith("//"):
            img = "https:" + img

        # Debug: Log first few thumbnails
        if len(seen) <= 3:
            utils.kodilog("@@@@Cumination: LiveCamRips thumbnail: " + str(img))

        # Find the parent container for metadata
        parent = link.find_parent()

        # Extract username and platform (usually in text near the video)
        name = "LiveCam"
        platform = ""
        timestamp = ""
        views = ""

        if parent:
            # Look for username links (they usually link to /[username]/profile)
            username_link = parent.select_one('a[href*="/profile"]')
            if username_link:
                username = utils.safe_get_text(username_link)
                if username:
                    name = username

            # Look for platform name (Stripchat, Chaturbate, etc.)
            platform_elem = parent.select_one("small.default")
            if platform_elem:
                platform = utils.safe_get_text(platform_elem).strip()
                if platform:
                    name += " - " + platform

            # Extract timestamp (e.g., "1 day ago")
            timestamp_elem = parent.select_one("small.muted")
            if timestamp_elem:
                timestamp = utils.safe_get_text(timestamp_elem).strip()

            # Extract views
            views_text = parent.get_text()

            views_match = re.search(r"(\d+)\s+views?", views_text, re.IGNORECASE)
            if views_match:
                views = views_match.group(1) + " views"

        name = utils.cleantext(name) if name else "Video"

        # Build description with timestamp and views
        desc_parts = []
        if timestamp:
            desc_parts.append(timestamp)
        if views:
            desc_parts.append(views)
        desc = " • ".join(desc_parts) if desc_parts else name

        site.add_download_link(
            name,
            videopage,
            "Playvid",
            img,
            desc,
        )

    # Handle pagination
    page_links = soup.select('a[href*="?page="]')
    if page_links:
        # Find the next page
        next_link = soup.select_one('a[rel="next"]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, "href")
            if next_href:
                nurl = urllib_parse.urljoin(url, next_href)
                # Try to extract page number
                page_match = re.search(r"[?&]page=(\d+)", next_href)
                npage = int(page_match.group(1)) if page_match else (page + 1)
                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR] ({})".format(npage),
                    nurl,
                    "List",
                    site.img_next,
                    npage,
                )
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    """Extract and play video using Livewire AJAX"""
    import json
    import base64

    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    # Extract the base64 video ID from URL (e.g., /watch/MTU2MDk3NTU=)
    video_id_match = re.search(r"/watch/([A-Za-z0-9+/=]+)", url)
    if not video_id_match:
        utils.notify("Error", "Invalid video URL")
        vp.progress.close()
        return

    video_id_b64 = video_id_match.group(1)

    # Decode the base64 ID to get the numeric UUID
    try:
        video_uuid = base64.b64decode(video_id_b64).decode("utf-8")
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in livecamrips: " + str(e))
        utils.notify("Error", "Could not decode video ID")
        vp.progress.close()
        return

    utils.kodilog("@@@@Cumination: LiveCamRips video UUID: " + str(video_uuid))

    # First, fetch the page to get CSRF token and Livewire snapshot
    vpage = utils.getHtml(url, site.url)

    # Extract CSRF token
    csrf_match = re.search(r'name="_token"[^>]+value="([^"]+)"', vpage)
    if not csrf_match:
        csrf_match = re.search(r'csrf-token"\s+content="([^"]+)"', vpage)

    if not csrf_match:
        utils.notify("Error", "Could not find CSRF token")
        vp.progress.close()
        return

    csrf_token = csrf_match.group(1)

    # Extract Livewire snapshot data
    # Look for wire:id or x-data attributes containing component data
    snapshot_match = re.search(r'wire:snapshot="([^"]+)"', vpage)
    if snapshot_match:
        # Decode HTML entities in snapshot
        snapshot_encoded = unescape(snapshot_match.group(1))
        try:
            snapshot_data = json.loads(snapshot_encoded)
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in livecamrips: " + str(e))
            snapshot_data = None
    else:
        snapshot_data = None

    vp.progress.update(50, "[CR]Requesting video URL[CR]")

    # Prepare Livewire AJAX request
    # Build snapshot if we couldn't extract it
    if not snapshot_data:
        snapshot_data = {
            "data": {"uuid": int(video_uuid), "video": None},
            "memo": {
                "id": "sglcZtKdHd97demFBSU7",  # This might need to be dynamic
                "name": "play-video",
                "path": "watch/" + video_id_b64,
                "method": "GET",
                "children": [],
                "scripts": [],
                "assets": [],
                "errors": [],
                "locale": "en",
            },
            "checksum": "8416600b98c7bf91c789ee5a10a5e45b5ce42c90ef82908a7c421e94bd77ae56",
        }

    livewire_payload = {
        "_token": csrf_token,
        "components": [
            {
                "snapshot": json.dumps(snapshot_data),
                "updates": {},
                "calls": [{"path": "", "method": "updateView", "params": []}],
            }
        ],
    }

    # Make POST request to /livewire/update
    livewire_url = site.url + "livewire/update"
    livewire_headers = {
        "Content-Type": "application/json",
        "X-Livewire": "true",
        "Referer": url,
    }

    try:
        livewire_response = utils.getHtml(
            livewire_url,
            referer=url,
            headers=livewire_headers,
            data=json.dumps(livewire_payload),
        )

        utils.kodilog(
            "@@@@Cumination: Livewire response: " + str(livewire_response[:500])
        )

        # Extract myvidplay.com URL from response
        myvidplay_match = re.search(
            r"(https?://(?:www\.)?myvidplay\.com/e/[a-zA-Z0-9]+)",
            livewire_response,
            re.IGNORECASE,
        )

        if not myvidplay_match:
            # Try parsing as JSON
            try:
                livewire_json = json.loads(livewire_response)
                # Search through the JSON for myvidplay URL
                livewire_str = json.dumps(livewire_json)
                myvidplay_match = re.search(
                    r"(https?://(?:www\.)?myvidplay\.com/e/[a-zA-Z0-9]+)",
                    livewire_str,
                    re.IGNORECASE,
                )
            except Exception as e:
                utils.kodilog(
                    "@@@@Cumination: Silent failure in livecamrips: " + str(e)
                )
        if myvidplay_match:
            myvidplay_url = myvidplay_match.group(1)
            utils.kodilog("@@@@Cumination: Found myvidplay.com URL: " + myvidplay_url)

            vp.progress.update(75, "[CR]Resolving video URL[CR]")

            # Try resolveurl with myvidplay URL
            try:
                import resolveurl

                hmf = resolveurl.HostedMediaFile(url=myvidplay_url)
                if hmf:
                    videourl = hmf.resolve()
                    if videourl:
                        vp.play_from_direct_link(videourl)
                        return
            except Exception as e:
                utils.kodilog("@@@@Cumination: MyVidPlay resolveurl failed: " + str(e))

        utils.notify("Error", "Could not find video URL")
        vp.progress.close()

    except Exception as e:
        utils.kodilog("@@@@Cumination: Livewire request failed: " + str(e))
        utils.notify("Error", "Could not load video")
        vp.progress.close()


@site.register()
def Search(url, keyword=None):
    """Search for videos"""
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # Build search URL
        searchUrl = site.url + "?search=" + keyword.replace(" ", "+")
        List(searchUrl)

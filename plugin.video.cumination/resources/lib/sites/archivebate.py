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

import html as htmlmod
import json
import re

import requests

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.http_timeouts import HTTP_TIMEOUT_MEDIUM

site = AdultSite(
    "archivebate",
    "[COLOR hotpink]Archivebate[/COLOR]",
    "https://archivebate.com/",
    "archivebate.png",
    "archivebate",
)

_PLATFORMS = [
    ("[COLOR hotpink]Chaturbate[/COLOR]", "https://archivebate.com/platform/Y2hhdHVyYmF0ZQ=="),
    ("[COLOR hotpink]Stripchat[/COLOR]", "https://archivebate.com/platform/c3RyaXBjaGF0"),
]


def _livewire_list(url):
    """Two-step Livewire fetch. Returns (html_fragment, next_page_url) or (None, None)."""
    session = requests.Session()
    session.headers.update({"User-Agent": utils.USER_AGENT})

    resp = session.get(url, timeout=HTTP_TIMEOUT_MEDIUM)
    # Derive base from the final URL after any redirect (.cc ↔ .com)
    final_url = resp.url
    base = final_url.split("//", 1)[0] + "//" + final_url.split("//", 1)[1].split("/")[0]

    csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', resp.text)
    if not csrf_match:
        return None, None
    csrf = csrf_match.group(1)

    wire_match = re.search(
        r'wire:initial-data="([^"]+)"[^>]*wire:init="loadVideos"', resp.text
    )
    if not wire_match:
        return None, None
    wire_state = json.loads(htmlmod.unescape(wire_match.group(1)))

    component_name = wire_state["fingerprint"]["name"]
    payload = {
        "fingerprint": wire_state["fingerprint"],
        "serverMemo": wire_state["serverMemo"],
        "updates": [{
            "type": "callMethod",
            "payload": {"id": "lw1", "method": "loadVideos", "params": []},
        }],
    }

    lw_resp = session.post(
        base + "/livewire/message/" + component_name,
        json=payload,
        headers={
            "X-CSRF-TOKEN": csrf,
            "X-Livewire": "true",
            "Accept": "application/json",
            "Referer": final_url,
        },
        timeout=HTTP_TIMEOUT_MEDIUM,
    )
    data = lw_resp.json()
    fragment = data.get("effects", {}).get("html")

    # Extract next page URL and normalise domain to archivebate.com
    next_url = None
    if fragment:
        next_match = re.search(r'<a[^>]+rel="next"[^>]+href="([^"]+)"', fragment)
        if next_match:
            next_url = re.sub(r'https://archivebate\.\w+', 'https://archivebate.com', next_match.group(1))

    return fragment, next_url


@site.register(default_mode=True)
def Main():
    for label, platform_url in _PLATFORMS:
        site.add_dir(label, platform_url, "List", site.img_cat)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    fragment, next_url = _livewire_list(url)
    if not fragment:
        utils.eod()
        return

    soup = utils.parse_html(fragment)
    for item in soup.select("section.video_item"):
        link = item.select_one('a[href*="/watch/"]')
        if not link:
            continue

        thumb = item.select_one("video.video-splash-mov")
        performer = item.select_one('a[href*="/profile/"]')

        watch_url = link["href"]
        image = thumb.get("poster", "") if thumb else ""
        name = performer.text.strip() if performer else "Video"

        site.add_download_link(name, watch_url, "Playvid", image)

    if next_url:
        site.add_dir("Next Page", next_url, "List", site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    soup = utils.parse_html(utils.getHtml(url, site.url))
    iframe = soup.select_one("iframe.video-frame")
    if iframe and iframe.get("src"):
        vp.play_from_link_to_resolve(iframe["src"])
        return
    utils.notify("Archivebate", "No video found")

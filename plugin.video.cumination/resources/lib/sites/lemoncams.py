"""
Cumination
Copyright (C) 2026 Team Cumination

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

import json
import time
import re
import xbmc
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite(
    "lemoncams",
    "[COLOR hotpink]LemonCams[/COLOR]",
    "https://www.lemoncams.com/",
    "lemoncams.png",
    "lemoncams",
    True,
)

API_URL = "https://api-v2-prod.lemoncams.com/main"
DEFAULT_PROVIDER = "stripchat"
DEFAULT_PAGE = 1
TOP_CAMS_KEY = "__top__"
SUPPORTED_PROVIDERS = {
    "stripchat": "Stripchat",
    "chaturbate": "Chaturbate",
    "camsoda": "Camsoda",
    "cam4": "Cam4",
}


def _api_get(params):
    query = urllib_parse.urlencode(params)
    url = "{}?{}".format(API_URL, query)
    payload = utils._getHtml(url, referer=site.url)
    try:
        return json.loads(payload)
    except Exception as e:
        utils.kodilog("LemonCams API error: {} - Payload: {}".format(str(e), payload[:200]))
        return {}


def _build_model_page_url(provider, username, stream_url=None):
    base = urllib_parse.urljoin(site.url, "{}/{}".format(provider, username))
    if stream_url:
        return "{}|{}".format(base, stream_url)
    return base


def _parse_model_identifier(value, default_provider=DEFAULT_PROVIDER):
    # Handle piped stream URL: base_url|stream_url
    stream_url = None
    if "|" in value:
        value, stream_url = value.split("|", 1)

    value = (value or "").strip()
    if not value:
        return None, None, None

    parsed = urllib_parse.urlparse(value)
    if parsed.scheme and parsed.netloc:
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2:
            return path_parts[0].lower(), path_parts[1], stream_url
        return None, None, stream_url

    if ":" in value:
        provider, username = value.split(":", 1)
        return provider.strip().lower(), username.strip(), stream_url

    return default_provider, value, stream_url


def _fetch_provider_payload(provider, page):
    params = {
        "page": str(page),
        "function": "cams",
        "project": "lemoncams",
        "tsp": str(int(time.time() * 1000)),
    }
    if provider and provider != TOP_CAMS_KEY:
        params["provider"] = provider
    return _api_get(params)


def _extract_playable_url(cam):
    # Try embedUrl first
    embed_url = cam.get("embedUrl") or ""
    if any(token in embed_url.lower() for token in [".m3u8", ".mp4", "manifest"]):
        return embed_url

    # Then try previewUrls
    for preview_url in cam.get("previewUrls", []):
        if any(token in preview_url.lower() for token in [".m3u8", ".mp4", "manifest"]):
            return preview_url

    return ""


def _format_plot(cam):
    meta = [
        "[COLOR deeppink]Provider:[/COLOR] {}".format(cam.get("provider", "")),
        "[COLOR deeppink]Viewers:[/COLOR] {}".format(cam.get("numberOfUsers", 0)),
    ]
    if cam.get("country"):
        meta.append("[COLOR deeppink]Country:[/COLOR] {}".format(cam["country"].upper()))
    if cam.get("title"):
        meta.append("[CR]{}".format(cam["title"]))
    return "[CR]".join(meta)


def _image_url(cam):
    image = cam.get("imageUrl") or ""
    if not image:
        return ""
    return "{}|User-Agent={}&Referer={}".format(
        image,
        urllib_parse.quote(utils.USER_AGENT),
        urllib_parse.quote(site.url),
    )


def _find_model_stream(provider, username, max_pages=5):
    """Search listing pages for a specific model's stream URL."""
    for page in range(1, max_pages + 1):
        payload = _fetch_provider_payload(provider, page)
        for cam in payload.get("cams", []):
            if cam.get("username", "").lower() == username.lower():
                url = _extract_playable_url(cam)
                if url:
                    return url
    return ""


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Top Cams[/COLOR]",
        TOP_CAMS_KEY,
        "List",
        "",
        DEFAULT_PAGE,
    )
    for p_id, p_name in sorted(SUPPORTED_PROVIDERS.items()):
        site.add_dir(
            "[COLOR hotpink]{} Cams[/COLOR]".format(p_name),
            p_id,
            "List",
            "",
            DEFAULT_PAGE,
        )
    
    site.add_dir(
        "[COLOR hotpink]Search Model[/COLOR]",
        "any",
        "Search",
        site.img_search,
    )
    site.add_dir(
        "[COLOR hotpink]Open LemonCams URL[/COLOR]",
        "url",
        "Search",
        site.img_search,
    )
    utils.eod()


@site.register()
def List(url, page=DEFAULT_PAGE):
    provider = (url or TOP_CAMS_KEY).strip().lower()
    
    payload = _fetch_provider_payload(provider, page)
    cams = []
    for cam in payload.get("cams", []):
        # If we requested a specific provider, filter for it
        if provider != TOP_CAMS_KEY and cam.get("provider", "").lower() != provider:
            continue
        cams.append(cam)
        
    if not cams:
        label = "top cams" if provider == TOP_CAMS_KEY else provider
        utils.notify("LemonCams", "No cams found for {}".format(label))
        utils.eod()
        return

    for cam in cams:
        cam_username = cam.get("username", "unknown")
        cam_provider = cam.get("provider", "")
        stream_url = _extract_playable_url(cam)
        
        label = cam_username
        if cam.get("title"):
            label = "{} - {}".format(cam_username, cam["title"][:80])
        
        if provider == TOP_CAMS_KEY and cam_provider:
            label = "[{}] {}".format(cam_provider.title(), label)
            
        site.add_download_link(
            label,
            _build_model_page_url(cam_provider or provider, cam_username, stream_url),
            "Playvid",
            _image_url(cam),
            _format_plot(cam),
            noDownload=True,
        )

    max_page = int(payload.get("maxPage") or 0)
    if max_page and page < max_page:
        site.add_dir(
            "Next Page ({}/{})".format(page + 1, max_page),
            provider,
            "List",
            site.img_next,
            page + 1,
        )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        prompt = (
            "Paste a LemonCams URL" if url == "url" else "Enter exact LemonCams model username"
        )
        site.search_dir(url, prompt)
        return

    # Try to parse as URL first if it looks like one
    if keyword.startswith("http"):
        provider, username, _ = _parse_model_identifier(keyword)
    else:
        # Check if they used provider:username
        if ":" in keyword:
            provider, username, _ = _parse_model_identifier(keyword)
        else:
            provider, username = DEFAULT_PROVIDER, keyword

    if not provider or not username:
        utils.notify("LemonCams", "Invalid model or URL")
        utils.eod()
        return

    playable_url = _find_model_stream(provider, username)
    if not playable_url:
        utils.notify("LemonCams", "Model offline or no stream found")
        utils.eod()
        return

    site.add_download_link(
        username,
        _build_model_page_url(provider, username, playable_url),
        "Playvid",
        "",
        "",
        noDownload=True,
    )
    utils.eod()


@site.register()
def Playvid(url, name):
    provider, username, stream_url = _parse_model_identifier(url)
    if not provider or not username:
        utils.notify("LemonCams", "Could not parse model URL")
        return

    # Use cached stream URL if available, otherwise search for a new one
    playable_url = stream_url
    if not playable_url:
        utils.kodilog("LemonCams: No cached URL, searching for stream for {}".format(username))
        playable_url = _find_model_stream(provider, username)

    if not playable_url:
        utils.notify("LemonCams", "Model offline or no stream found")
        return

    # Build headers for playback
    headers = {
        "User-Agent": utils.USER_AGENT,
        "Referer": "https://www.lemoncams.com/",
        "Origin": "https://www.lemoncams.com"
    }
    
    # Append headers to URL
    header_str = "|User-Agent={}&Referer={}&Origin={}".format(
        urllib_parse.quote(headers["User-Agent"]),
        urllib_parse.quote(headers["Referer"]),
        urllib_parse.quote(headers["Origin"])
    )
    
    final_url = playable_url + header_str
    
    utils.kodilog("LemonCams: Playing {}".format(final_url), xbmc.LOGDEBUG)
    
    vp = utils.VideoPlayer(name)
    vp.IA_check = "IA" # Use inputstream.adaptive for HLS
    vp.play_from_direct_link(final_url)

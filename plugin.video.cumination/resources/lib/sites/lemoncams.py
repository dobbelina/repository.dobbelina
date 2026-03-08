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
}


def _api_get(params):
    query = urllib_parse.urlencode(params)
    url = "{}?{}".format(API_URL, query)
    payload = utils._getHtml(url, referer=site.url)
    return json.loads(payload)


def _build_model_page_url(provider, username):
    return urllib_parse.urljoin(site.url, "{}/{}".format(provider, username))


def _parse_model_identifier(value, default_provider=DEFAULT_PROVIDER):
    value = (value or "").strip()
    if not value:
        return None, None

    parsed = urllib_parse.urlparse(value)
    if parsed.scheme and parsed.netloc:
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2:
            return path_parts[0].lower(), path_parts[1]
        return None, None

    if ":" in value:
        provider, username = value.split(":", 1)
        return provider.strip().lower(), username.strip()

    return default_provider, value


def _fetch_cam_payload(provider, username):
    params = {
        "page": "1",
        "provider": provider,
        "function": "cam",
        "project": "lemoncams",
        "tsp": str(int(time.time() * 1000)),
    }
    if username:
        params["username"] = username
        params["path"] = ".{}.{}".format(provider, username)
    return _api_get(params)


def _fetch_provider_payload(provider, page):
    params = {
        "page": str(page),
        "function": "cam",
        "project": "lemoncams",
        "tsp": str(int(time.time() * 1000)),
    }
    if provider and provider != TOP_CAMS_KEY:
        params["provider"] = provider
    return _api_get(params)


def _extract_playable_url(cam):
    embed_url = cam.get("embedUrl") or ""
    if any(token in embed_url.lower() for token in [".m3u8", ".mp4", "manifest"]):
        return embed_url

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


def _iter_search_results(provider, username):
    payload = _fetch_cam_payload(provider, username)
    cams = payload.get("cams", [])
    exact = []
    related = []
    for cam in cams:
        if cam.get("provider") != provider:
            continue
        cam_username = cam.get("username", "")
        playable_url = _extract_playable_url(cam)
        if not playable_url:
            continue
        if cam_username.lower() == username.lower():
            exact.append(cam)
        else:
            related.append(cam)
    return exact + related


def _provider_cams(provider, page):
    payload = _fetch_provider_payload(provider, page)
    cams = []
    for cam in payload.get("cams", []):
        if provider != TOP_CAMS_KEY and cam.get("provider") != provider:
            continue
        playable_url = _extract_playable_url(cam)
        if not playable_url:
            continue
        cams.append(cam)
    return cams


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Top Cams[/COLOR]",
        TOP_CAMS_KEY,
        "List",
        "",
        DEFAULT_PAGE,
    )
    site.add_dir(
        "[COLOR hotpink]Stripchat Cams[/COLOR]",
        DEFAULT_PROVIDER,
        "List",
        "",
        DEFAULT_PAGE,
    )
    site.add_dir(
        "[COLOR hotpink]Search Stripchat Model[/COLOR]",
        DEFAULT_PROVIDER,
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
    provider = (url or DEFAULT_PROVIDER).strip().lower()
    if provider != TOP_CAMS_KEY and provider not in SUPPORTED_PROVIDERS:
        utils.notify("LemonCams", "Provider not supported yet: {}".format(provider))
        utils.eod()
        return

    cams = _provider_cams(provider, page)
    if not cams:
        label = "top cams" if provider == TOP_CAMS_KEY else provider
        utils.notify("LemonCams", "No cams found for {}".format(label))
        utils.eod()
        return

    for cam in cams:
        cam_username = cam.get("username", "unknown")
        cam_provider = cam.get("provider", "")
        label = cam_username
        if cam.get("title"):
            label = "{} - {}".format(cam_username, cam["title"][:80])
        if provider == TOP_CAMS_KEY and cam_provider:
            label = "[{}] {}".format(cam_provider, label)
        site.add_download_link(
            label,
            _build_model_page_url(cam_provider or provider, cam_username),
            "Playvid",
            _image_url(cam),
            _format_plot(cam),
            noDownload=True,
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

    default_provider = DEFAULT_PROVIDER if url != "url" else DEFAULT_PROVIDER
    provider, username = _parse_model_identifier(keyword, default_provider=default_provider)
    if not provider or not username:
        utils.notify("LemonCams", "Enter a LemonCams URL or exact username")
        utils.eod()
        return

    if provider not in SUPPORTED_PROVIDERS:
        utils.notify(
            "LemonCams",
            "Provider not supported yet: {}".format(provider),
        )
        utils.eod()
        return

    results = _iter_search_results(provider, username)
    if not results:
        utils.notify("LemonCams", "No playable result found for {}".format(username))
        utils.eod()
        return

    for cam in results:
        cam_username = cam.get("username", "unknown")
        label = cam_username
        if cam.get("title"):
            label = "{} - {}".format(cam_username, cam["title"][:80])
        site.add_download_link(
            label,
            _build_model_page_url(provider, cam_username),
            "Playvid",
            _image_url(cam),
            _format_plot(cam),
            noDownload=True,
        )

    utils.eod()


@site.register()
def Playvid(url, name):
    provider, username = _parse_model_identifier(url, default_provider=DEFAULT_PROVIDER)
    if not provider or not username:
        utils.notify("LemonCams", "Could not parse model URL")
        return

    results = _iter_search_results(provider, username)
    if not results:
        utils.notify("LemonCams", "Model offline or no playable stream found")
        return

    chosen = None
    for cam in results:
        if cam.get("username", "").lower() == username.lower():
            chosen = cam
            break
    if not chosen:
        chosen = results[0]

    playable_url = _extract_playable_url(chosen)
    if not playable_url:
        utils.notify("LemonCams", "No direct playable URL found")
        return

    vp = utils.VideoPlayer(name)
    vp.IA_check = "skip"
    vp.play_from_direct_link(playable_url)

"""
Cumination site scraper - ThotHub
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

import json
import re

import xbmc
import xbmcaddon
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode


addon = xbmcaddon.Addon()
site = AdultSite(
    "thothub",
    "[COLOR hotpink]ThotHub[/COLOR]",
    "https://thothub.mx/",
    "thothub.png",
    "thothub",
)
REFERER_HEADER = site.url
ORIGIN_HEADER = site.url.rstrip("/")
UA_HEADER = urllib_parse.quote(utils.USER_AGENT, safe="")
IMG_HEADER_SUFFIX = "|Referer={0}&User-Agent={1}".format(REFERER_HEADER, UA_HEADER)
VIDEO_HEADER_SUFFIX = "|Referer={0}&Origin={1}&User-Agent={2}".format(
    REFERER_HEADER, ORIGIN_HEADER, UA_HEADER
)
SITE_DOMAIN = urllib_parse.urlsplit(site.url).hostname or "thothub.mx"
VIDEO_FILTER_MODE = "public_only"
_VIDEO_PAGE_CACHE = {}

AUTH_COOKIE_NAMES = ("kt_member", "kt_login_key")
PRIVATE_MESSAGE_MAP = {
    "private video": "ThotHub marks this video as private (login may be required).",
    "only active members can watch private videos": "Only active members can watch private videos.",
    "you are not allowed to watch this video": "ThotHub denied access to this video.",
    "login-required": "This video requires login.",
    "login required": "This video requires login.",
    "login to view": "Login is required to view this video.",
    "please login": "Please login at ThotHub to view this video.",
    "you must be logged in": "You must be logged in to view this video.",
    "members only": "This video is available to logged-in members only.",
    "registered members only": "This video is available to registered members only.",
    "subscribers only": "This video is available to subscribers only.",
    "followers only": "This video is limited to circle/follower members.",
    "join our circle": "Join the poster circle on ThotHub to view this video.",
    "join this circle": "Join the poster circle on ThotHub to view this video.",
}


def _has_credentials():
    username = addon.getSetting("thothub_username") or ""
    password = addon.getSetting("thothub_password") or ""
    return bool(username.strip() and password.strip())


def _thothub_cookie_names():
    names = []
    for cookie in utils.cj:
        domain = (cookie.domain or "").lstrip(".")
        if domain.endswith(SITE_DOMAIN):
            names.append(cookie.name)
    return names


def _log_thothub_cookies(context):
    names = _thothub_cookie_names()
    label = ", ".join(sorted(set(names))) if names else "none"
    utils.kodilog("ThotHub [{}] cookies: {}".format(context, label), xbmc.LOGDEBUG)


def _clean_media_url(media_url):
    """Normalize ThotHub media URL strings."""
    if not media_url:
        return None
    cleaned = media_url.replace("\\/", "/").replace("&amp;", "&").strip()
    if "/&" in cleaned:
        cleaned = cleaned.replace("/&", "?", 1)
    cleaned = cleaned.rstrip("/")
    if not cleaned.startswith("http"):
        cleaned = urllib_parse.urljoin(site.url, cleaned)
    return cleaned


def _parse_flashvars(html):
    """Return a dict of flashvars key/value pairs from the given HTML."""
    # Try pattern 1: var flashvars = { key: 'value', ... }
    # This matches JavaScript object literal syntax with unquoted keys
    block = re.search(
        r"var\s+flashvars\s*=\s*\{([^}]+)\}", html, re.IGNORECASE | re.DOTALL
    )
    if block:
        vars_block = block.group(1)
        # Match unquoted keys with single-quoted values: key: 'value'
        pairs = re.findall(r"([a-z0-9_]+):\s*'([^']*)'", vars_block, re.IGNORECASE)
        if pairs:
            utils.kodilog(
                "ThotHub parsed flashvars (var with single quotes): {} pairs".format(
                    len(pairs)
                ),
                xbmc.LOGDEBUG,
            )
            return {key.lower(): value for key, value in pairs}
        # Also try double-quoted values: key: "value"
        pairs = re.findall(r'([a-z0-9_]+):\s*"([^"]*)"', vars_block, re.IGNORECASE)
        if pairs:
            utils.kodilog(
                "ThotHub parsed flashvars (var with double quotes): {} pairs".format(
                    len(pairs)
                ),
                xbmc.LOGDEBUG,
            )
            return {key.lower(): value for key, value in pairs}

    # Try pattern 2: flashvars = {...} (without var keyword)
    block2 = re.search(r"flashvars\s*=\s*\{([^}]+)\}", html, re.IGNORECASE | re.DOTALL)
    if block2:
        vars_block = block2.group(1)
        pairs = re.findall(r"([a-z0-9_]+):\s*'([^']*)'", vars_block, re.IGNORECASE)
        if pairs:
            utils.kodilog(
                "ThotHub parsed flashvars (no var, single quotes): {} pairs".format(
                    len(pairs)
                ),
                xbmc.LOGDEBUG,
            )
            return {key.lower(): value for key, value in pairs}
        pairs = re.findall(r'([a-z0-9_]+):\s*"([^"]*)"', vars_block, re.IGNORECASE)
        if pairs:
            utils.kodilog(
                "ThotHub parsed flashvars (no var, double quotes): {} pairs".format(
                    len(pairs)
                ),
                xbmc.LOGDEBUG,
            )
            return {key.lower(): value for key, value in pairs}

    # Try pattern 3: JSON configuration assigned to a player variable
    json_block = re.search(
        r"(?:playerConfig|kt_player_config)\s*=\s*(\{.*?\});",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if json_block:
        raw = json_block.group(1)
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                utils.kodilog(
                    "ThotHub parsed JSON config: {} keys".format(len(data)),
                    xbmc.LOGDEBUG,
                )
                return {k.lower(): v for k, v in data.items()}
        except Exception as e:
            utils.kodilog("ThotHub JSON parse failed: {}".format(str(e)), xbmc.LOGDEBUG)

    # Try pattern 4: var flashvars_XXXX = {...}
    var_block = re.search(
        r"var\s+flashvars[^=]*=\s*(\{[^;]+\});", html, re.IGNORECASE | re.DOTALL
    )
    if var_block:
        try:
            data = json.loads(var_block.group(1))
            if isinstance(data, dict):
                utils.kodilog(
                    "ThotHub parsed var flashvars: {} keys".format(len(data)),
                    xbmc.LOGDEBUG,
                )
                return {k.lower(): v for k, v in data.items()}
        except Exception as e:
            utils.kodilog(
                "ThotHub var flashvars parse failed: {}".format(str(e)), xbmc.LOGDEBUG
            )

    utils.kodilog("ThotHub: No flashvars found in HTML", xbmc.LOGDEBUG)
    return {}


def _is_logged_in():
    """Return True only when real ThotHub auth cookies are present."""
    for name in _thothub_cookie_names():
        if name in AUTH_COOKIE_NAMES:
            utils.kodilog("ThotHub: Found auth cookie {}".format(name), xbmc.LOGDEBUG)
            return True
    return False


def _login(force=False):
    """Attempt to login to ThotHub using stored credentials."""
    username = addon.getSetting("thothub_username")
    password = addon.getSetting("thothub_password")

    if not username or not password:
        utils.kodilog("ThotHub: No credentials configured", xbmc.LOGDEBUG)
        utils.notify(
            "ThotHub Login", "Please configure username/password in addon settings"
        )
        return False

    if not force and _is_logged_in():
        utils.kodilog("ThotHub: Already logged in, skipping re-auth", xbmc.LOGDEBUG)
        return True

    utils.kodilog(
        "ThotHub: Attempting login for user: {}".format(username), xbmc.LOGDEBUG
    )

    # Get the login page to extract any CSRF tokens
    login_page_url = site.url + "login/"
    try:
        login_html = utils._getHtml(login_page_url, site.url)
    except Exception as e:
        utils.kodilog("ThotHub: Failed to fetch login page: {}".format(str(e)))
        utils.notify("ThotHub Login", "Failed to load login page")
        return None

    # Try to find CSRF token or similar
    csrf_token = None
    csrf_match = re.search(
        r'name=["\']csrfmiddlewaretoken["\'][^>]+value=["\']([^"\']+)["\']|value=["\']([^"\']+)["\'][^>]+name=["\']csrfmiddlewaretoken["\']',
        login_html,
        re.IGNORECASE,
    )
    if csrf_match:
        csrf_token = csrf_match.group(1) or csrf_match.group(2)
        utils.kodilog("ThotHub: Found CSRF token", xbmc.LOGDEBUG)

    # Prepare login POST data
    login_data = {
        "username": username,
        "pass": password,
        "remember_me": "1",
        "action": "login",
        "email_link": site.url + "email/",
        "format": "json",
        "mode": "async",
    }

    if csrf_token:
        login_data["csrfmiddlewaretoken"] = csrf_token

    # POST to login endpoint
    login_url = site.url + "login/"
    headers = utils.base_hdrs.copy()
    headers.update(
        {
            "Referer": login_page_url,
            "Origin": ORIGIN_HEADER,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
    )

    try:
        response = utils._postHtml(login_url, headers=headers, form_data=login_data)
        _log_thothub_cookies("after-login-post")
        lowered = (response or "").lower()
        if "invalid_login" in lowered or "incorrect" in lowered:
            utils.kodilog("ThotHub: Login failed - credentials rejected", xbmc.LOGDEBUG)
            utils.notify("ThotHub Login", "Login failed - check username/password")
            return False

        if _is_logged_in():
            utils.kodilog("ThotHub: Login successful (cookies present)", xbmc.LOGDEBUG)
            utils.notify("ThotHub", "Login successful")
            return True

        if "login" in lowered and "error" in lowered:
            utils.kodilog("ThotHub: Login response contained error text", xbmc.LOGDEBUG)
            utils.notify("ThotHub Login", "Login failed - site returned an error")
            return False

        utils.kodilog(
            "ThotHub: Login response inconclusive, no auth cookies detected",
            xbmc.LOGDEBUG,
        )
        utils.kodilog(
            "ThotHub: Last response snippet: {}".format((response or "")[:200]),
            xbmc.LOGDEBUG,
        )
        return False

    except Exception as e:
        utils.kodilog("ThotHub: Login request failed: {}".format(str(e)))
        utils.notify("ThotHub Login", "Login request failed")
        return None


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Latest Updates[/COLOR]",
        site.url + "latest-updates/",
        "List",
        site.img_next,
    )
    site.add_dir(
        "[COLOR hotpink]Public[/COLOR]", site.url + "public/", "List", site.img_next
    )
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Models[/COLOR]",
        site.url + "models/",
        "Models",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    # latest-updates/ is more reliable than public/
    List(site.url + "latest-updates/")


def _extract_list_items(html):
    """Extract video items from ThotHub HTML using BeautifulSoup."""
    items = []
    soup = utils.parse_html(html)

    # Try to find the main video container to avoid sidebar/related videos
    # Common IDs: list_videos_latest_videos_list_items, list_videos_most_recent_videos_items, etc.
    container = soup.select_one('[id*="videos"][id*="_items"]')
    if not container:
        container = soup.select_one(".list-videos, .videos-list")

    source = container if container else soup

    # Find all items
    for item in source.select(".item"):
        # Check if it's a private video
        classes = item.get("class", [])
        if "private" in classes:
            utils.kodilog(
                "ThotHub: Skipping private video (class=private)", xbmc.LOGDEBUG
            )
            continue

        # Also check for .line-private span as a safety measure
        if item.select_one(".line-private, .ico-private"):
            utils.kodilog(
                "ThotHub: Skipping private video (found .line-private)", xbmc.LOGDEBUG
            )
            continue

        link = item.select_one('a[href*="/videos/"]')
        if not link:
            continue

        url = utils.safe_get_attr(link, "href")
        if not url or "/videos/" not in url:
            continue

        # Extract video ID from URL: /videos/1430251/slug/
        try:
            parts = url.split("/videos/")
            if len(parts) < 2:
                continue
            video_id = parts[1].split("/")[0]
            if not video_id.isdigit():
                continue
        except (IndexError, AttributeError):
            continue

        # Get title from title attribute or link text
        title = utils.safe_get_attr(link, "title")
        if not title:
            title = utils.safe_get_text(link)
        if not title:
            # Fallback: extract from URL slug
            slug = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
            title = slug.replace("-", " ").title()

        name = utils.cleantext(title)

        # ThotHub screenshot pattern: /contents/videos_screenshots/ID000/ID/preview.jpg
        video_id_int = int(video_id)
        base_id = (video_id_int // 1000) * 1000
        screenshot = urllib_parse.urljoin(
            site.url,
            "contents/videos_screenshots/{}/{}/preview.jpg".format(base_id, video_id),
        )

        items.append((url, name, screenshot))

    # Deduplicate by URL
    seen = set()
    uniq = []
    for u, n, t in items:
        if u not in seen:
            uniq.append((u, n, t))
            seen.add(u)

    utils.kodilog("ThotHub extracted {} unique items".format(len(uniq)), xbmc.LOGDEBUG)
    return uniq


@site.register()
def Categories(url):
    """List video categories from ThotHub."""
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    container = soup.select_one(".list-categories")
    source = container if container else soup

    for item in source.select("a.item"):
        cat_url = utils.safe_get_attr(item, "href")
        title_el = item.select_one(".title")
        title = utils.safe_get_text(title_el)
        count_el = item.select_one(".videos")
        count = utils.safe_get_text(count_el)

        if title and cat_url:
            display_name = title
            if count:
                display_name += " [COLOR yellow]({})[/COLOR]".format(count)
            site.add_dir(display_name, cat_url, "List", site.img_cat)

    nurl = _find_next_page(html, url)
    if nurl:
        if nurl.startswith("/"):
            nurl = urllib_parse.urljoin(site.url, nurl)
        site.add_dir(
            "[COLOR hotpink]Next Page...[/COLOR]", nurl, "Categories", site.img_next
        )
    utils.eod()


@site.register()
def Models(url):
    """List models from ThotHub."""
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    container = soup.select_one(".list-models")
    source = container if container else soup

    for item in source.select("a.item"):
        model_url = utils.safe_get_attr(item, "href")
        title_el = item.select_one(".title")
        title = utils.safe_get_text(title_el)
        count_el = item.select_one(".videos")
        count = utils.safe_get_text(count_el)
        img_el = item.select_one("img")
        img = utils.safe_get_attr(img_el, "src")

        if title and model_url:
            display_name = title
            if count:
                display_name += " [COLOR yellow]({})[/COLOR]".format(count)
            site.add_dir(display_name, model_url, "List", img or site.img_cat)

    nurl = _find_next_page(html, url)
    if nurl:
        if nurl.startswith("/"):
            nurl = urllib_parse.urljoin(site.url, nurl)
        site.add_dir(
            "[COLOR hotpink]Next Page...[/COLOR]", nurl, "Models", site.img_next
        )
    utils.eod()


def _find_next_page(html, current_url):
    """Find the next page URL in pagination using BeautifulSoup."""
    soup = utils.parse_html(html)

    # Try various pagination patterns
    # Pattern 1: <a rel="next" href="...">
    next_link = soup.select_one('a[rel="next"]')
    if next_link:
        url = utils.safe_get_attr(next_link, "href")
        if url and url != "#" and url != "#search":
            utils.kodilog("ThotHub found next page (rel=next): {}".format(url), xbmc.LOGDEBUG)
            return url

    # Pattern 2: <li class="next"><a href="...">
    # Handle #search relative links by looking at data-parameters
    li_next = soup.select_one('li.next a, li[class*="next"] a')
    if li_next:
        url = utils.safe_get_attr(li_next, "href")
        if url == "#search" or url == "#":
            params = utils.safe_get_attr(li_next, "data-parameters")
            if params:
                # from_videos+from_albums:2 or similar
                match = re.search(r'from(?:_videos\+from_albums)?:(\d+)', params)
                if match:
                    next_page = match.group(1)
                    if "/search/" in current_url:
                        # Construct: /search/keyword/2/
                        base_search = re.sub(r'/\d+/?$', '', current_url.rstrip("/"))
                        return base_search + "/{}/".format(next_page)
        
        if url and url != "#" and url != "#search":
            utils.kodilog(
                "ThotHub found next page via li.next: {}".format(url), xbmc.LOGDEBUG
            )
            return url

    # Try to find numbered pagination and increment
    # URLs like /latest-updates/2/ -> /latest-updates/3/
    page_match = re.search(r"/(\d+)/?$", current_url)
    if page_match:
        current_page = int(page_match.group(1))
        next_page = current_page + 1
        next_url = re.sub(r"/\d+/?$", "/{}/".format(next_page), current_url)
        # Verify this page number exists in the HTML
        if "/{}/".format(next_page) in html or 'data-parameters="' in html:
            utils.kodilog(
                "ThotHub incrementing page to: {}".format(next_url), xbmc.LOGDEBUG
            )
            return next_url
    else:
        # Initial page, try to find "2" in pagination
        if "/2/" in html or 'from:2' in html or 'from_videos+from_albums:2' in html:
            if current_url.endswith("/"):
                return current_url + "2/"
            else:
                return current_url + "/2/"

    return None


@site.register()
def List(url):
    """List videos from a ThotHub page."""
    utils.kodilog("ThotHub List URL: {}".format(url), xbmc.LOGDEBUG)

    try:
        listhtml = utils.getHtml(url, site.url)
    except Exception as e:
        utils.kodilog("ThotHub error fetching {}: {}".format(url, str(e)))
        utils.notify("Error", "Could not fetch ThotHub page")
        utils.eod()
        return

    # Extract video items
    items = _extract_list_items(listhtml)

    if not items:
        utils.kodilog("ThotHub: No items found on page", xbmc.LOGDEBUG)
        utils.notify("ThotHub", "No videos found on this page")

    # Add video links (no filtering - /public/ page only has public videos)
    for videopage, name, img in items:
        # Make URLs absolute
        if videopage.startswith("/"):
            videopage = urllib_parse.urljoin(site.url, videopage)

        thumb = img + IMG_HEADER_SUFFIX if "|" not in img else img
        site.add_download_link(name, videopage, "Playvid", thumb, name)

    # Add pagination
    nurl = _find_next_page(listhtml, url)
    if nurl:
        if nurl.startswith("/"):
            nurl = urllib_parse.urljoin(site.url, nurl)

        site.add_dir("[COLOR hotpink]Next Page...[/COLOR]", nurl, "List", site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    """Extract and play video from ThotHub."""
    utils.kodilog("ThotHub Playvid: {}".format(url), xbmc.LOGDEBUG)

    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    # Add comprehensive browser-like headers to bypass bot detection
    headers = _build_browser_headers()

    html = _get_cached_video_page(url)
    if not html:
        try:
            html = utils.getHtml(url, site.url, headers=headers)
            _VIDEO_PAGE_CACHE[url] = html
        except Exception as e:
            utils.kodilog("ThotHub Playvid error fetching page: {}".format(str(e)))
            utils.notify("Error", "Could not load video page")
            return

    license_code = None
    lmatch = re.search(r"license_code:\s*'([^']+)", html, re.IGNORECASE)
    if lmatch:
        license_code = lmatch.group(1)

    flashvars = _parse_flashvars(html)
    if flashvars and not license_code:
        license_code = flashvars.get("license_code")

    # Check for private/restricted videos
    blocked_messages, requires_login = _detect_access_messages(html)

    # If no flashvars and access seems restricted, log in (or refresh login) automatically
    login_attempted = False
    have_credentials = _has_credentials()
    if have_credentials and not flashvars and not _is_logged_in():
        utils.kodilog(
            "ThotHub: No auth cookies before playback, attempting login", xbmc.LOGDEBUG
        )
        login_result = _login()
        login_attempted = True
        if login_result:
            _log_thothub_cookies("after-initial-login")
            try:
                html = utils.getHtml(url, site.url, headers=headers)
                flashvars = _parse_flashvars(html)
                if flashvars and not license_code:
                    license_code = flashvars.get("license_code")
                blocked_messages, requires_login = _detect_access_messages(html)
            except Exception as e:
                utils.kodilog(
                    "ThotHub: Retry after initial login failed: {}".format(str(e))
                )

    if not flashvars and requires_login and have_credentials:
        if _is_logged_in() and not login_attempted:
            utils.kodilog(
                "ThotHub: Session looks stale, forcing re-login", xbmc.LOGDEBUG
            )
            login_result = _login(force=True)
        elif not login_attempted:
            utils.kodilog(
                "ThotHub: Video requires login, attempting login", xbmc.LOGDEBUG
            )
            login_result = _login()
        else:
            login_result = None

        if login_result is not None:
            if login_result is False:
                utils.kodilog(
                    "ThotHub: Login attempt completed but no auth cookies detected",
                    xbmc.LOGDEBUG,
                )
            utils.kodilog(
                "ThotHub: Retrying video page after login attempt", xbmc.LOGDEBUG
            )
            try:
                html = utils.getHtml(url, site.url, headers=headers)
                flashvars = _parse_flashvars(html)
                if flashvars and not license_code:
                    license_code = flashvars.get("license_code")
                if flashvars:
                    blocked_messages = []
                    requires_login = False
            except Exception as e:
                utils.kodilog("ThotHub: Retry after login failed: {}".format(str(e)))
        else:
            utils.kodilog(
                "ThotHub: Login could not be attempted (missing credentials or request failure)",
                xbmc.LOGDEBUG,
            )

    # Extract video URL from JavaScript flashvars
    # Pattern: 'video_url': 'function/0/https://thothub.org/get_file/.../ID.mp4/'
    video_url = flashvars.get("video_url") if flashvars else None

    # Try to find video_url in flashvars
    flashvars_match = re.search(
        r"['\"]video_url['\"]:\s*['\"]([^'\"]+)['\"]", html, re.IGNORECASE
    )
    if flashvars_match:
        video_url = flashvars_match.group(1)
        # Remove 'function/0/' prefix if present
        if video_url.startswith("function/") and license_code:
            try:
                video_url = kvs_decode(video_url, license_code)
            except Exception as err:
                utils.kodilog(
                    "ThotHub kvs_decode failed: {}".format(err), xbmc.LOGDEBUG
                )
                video_url = re.sub(r"^function/\d+/", "", video_url)
        else:
            video_url = re.sub(r"^function/\d+/", "", video_url)
        video_url = _clean_media_url(video_url)
        utils.kodilog(
            "ThotHub extracted video URL: {}".format(video_url), xbmc.LOGDEBUG
        )

    # Fallback: try to find direct .mp4 URL
    if not video_url and not flashvars and have_credentials and not login_attempted:
        utils.kodilog(
            "ThotHub: Missing flashvars without private marker, attempting login just in case",
            xbmc.LOGDEBUG,
        )
        login_result = _login(force=not _is_logged_in())
        login_attempted = True
        if login_result:
            try:
                html = utils.getHtml(url, site.url, headers=headers)
            except Exception as e:
                utils.kodilog(
                    "ThotHub: Second retry after login failed: {}".format(str(e))
                )
            else:
                flashvars = _parse_flashvars(html)
                if flashvars and not license_code:
                    license_code = flashvars.get("license_code")
                flashvars_match = re.search(
                    r"['\"]video_url['\"]:\s*['\"]([^'\"]+)['\"]", html, re.IGNORECASE
                )
                if flashvars_match:
                    video_url = flashvars_match.group(1)
                    if video_url.startswith("function/") and license_code:
                        try:
                            video_url = kvs_decode(video_url, license_code)
                        except Exception as err:
                            utils.kodilog(
                                "ThotHub kvs_decode second try failed: {}".format(err),
                                xbmc.LOGDEBUG,
                            )
                            video_url = re.sub(r"^function/\d+/", "", video_url)
                    else:
                        video_url = re.sub(r"^function/\d+/", "", video_url)
                    video_url = _clean_media_url(video_url)
                blocked_messages, requires_login = _detect_access_messages(html)

    if not video_url:
        mp4_match = re.search(r'(https?://[^"\'<>\s]+\.mp4/?)', html, re.IGNORECASE)
        if mp4_match:
            video_url = _clean_media_url(mp4_match.group(1))
            utils.kodilog("ThotHub found MP4 URL: {}".format(video_url), xbmc.LOGDEBUG)
        elif flashvars:
            for key in (
                "video_alt_url",
                "video_alt_url2",
                "video_alt_url3",
                "src",
                "file",
            ):
                candidate = flashvars.get(key)
                if candidate and candidate.startswith("http"):
                    normalized = _clean_media_url(candidate)
                    if normalized and ".mp4" in normalized:
                        video_url = normalized
                        utils.kodilog(
                            "ThotHub found alternate video URL ({})".format(key),
                            xbmc.LOGDEBUG,
                        )
                        break

    # Additional fallback: look for quality-based URLs (similar to spankbang pattern)
    if not video_url:
        quality_pattern = re.compile(
            r'["\'](?:240p|320p|480p|720p|1080p|4k)["\']:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
            re.IGNORECASE,
        )
        quality_matches = quality_pattern.findall(html)
        if quality_matches:
            # Prefer highest quality available
            video_url = _clean_media_url(quality_matches[-1])
            utils.kodilog(
                "ThotHub found quality-based MP4 URL: {}".format(video_url),
                xbmc.LOGDEBUG,
            )

    # Additional fallback: look for video sources array pattern
    if not video_url:
        sources_pattern = re.compile(
            r'sources?\s*:\s*\[\s*["\']([^"\']+\.mp4[^"\']*)["\']', re.IGNORECASE
        )
        sources_match = sources_pattern.search(html)
        if sources_match:
            video_url = _clean_media_url(sources_match.group(1))
            utils.kodilog(
                "ThotHub found sources array MP4 URL: {}".format(video_url),
                xbmc.LOGDEBUG,
            )

    # Additional fallback: look for file: "url" pattern
    if not video_url:
        file_pattern = re.compile(
            r'file\s*:\s*["\']([^"\']+\.mp4[^"\']*)["\']', re.IGNORECASE
        )
        file_match = file_pattern.search(html)
        if file_match:
            video_url = _clean_media_url(file_match.group(1))
            utils.kodilog(
                "ThotHub found file: pattern MP4 URL: {}".format(video_url),
                xbmc.LOGDEBUG,
            )

    # Additional fallback: look for m3u8 HLS streams
    if not video_url:
        m3u8_pattern = re.compile(r'["\']([^"\']+\.m3u8[^"\']*)["\']', re.IGNORECASE)
        m3u8_match = m3u8_pattern.search(html)
        if m3u8_match:
            video_url = _clean_media_url(m3u8_match.group(1))
            utils.kodilog(
                "ThotHub found M3U8 stream URL: {}".format(video_url), xbmc.LOGDEBUG
            )

    # Fallback: try iframe embed
    if not video_url:
        video_id_match = re.search(r"/videos/(\d+)/", url)
        if video_id_match:
            video_id = video_id_match.group(1)
            embed_url = urllib_parse.urljoin(site.url, "embed/{}".format(video_id))
            utils.kodilog(
                "ThotHub trying embed URL: {}".format(embed_url), xbmc.LOGDEBUG
            )
            embed_html = None
            try:
                embed_html = utils.getHtml(embed_url, url, headers=headers)
            except Exception as e:
                utils.kodilog("@@@@Cumination: failure in thothub: " + str(e))
                embed_html = None
            if embed_html:
                embed_vars = _parse_flashvars(embed_html)
                if not license_code:
                    license_code = embed_vars.get("license_code", license_code)
                if not video_url:
                    video_url = embed_vars.get("video_url")
                embed_lower = embed_html.lower()
                if "you are not allowed to watch this video" in embed_lower:
                    blocked_messages.append(
                        "ThotHub denied access to this embedded video."
                    )

    if video_url:
        if video_url.startswith("function/") and license_code:
            try:
                decoded = kvs_decode(video_url, license_code)
                video_url = _clean_media_url(decoded)
            except Exception as err:
                utils.kodilog(
                    "ThotHub kvs_decode fallback failed: {}".format(err), xbmc.LOGDEBUG
                )
                video_url = _clean_media_url(re.sub(r"^function/\d+/", "", video_url))
        else:
            video_url = _clean_media_url(video_url)

        # If we found an M3U8 stream, we need to use inputstream.adaptive
        # Re-initialize VideoPlayer with IA_check="IA" for HLS streams
        if video_url and ".m3u8" in video_url.lower():
            utils.kodilog(
                "ThotHub: M3U8 stream detected, using inputstream.adaptive",
                xbmc.LOGDEBUG,
            )
            vp.progress.close()
            vp = utils.VideoPlayer(name, download, IA_check="IA")
            vp.progress.update(75, "[CR]Playing video[CR]")

        play_url = video_url if "|" in video_url else video_url + VIDEO_HEADER_SUFFIX
        vp.progress.update(75, "[CR]Playing video[CR]")
        vp.play_from_direct_link(play_url)
    else:
        utils.kodilog("ThotHub: Could not find video URL", xbmc.LOGDEBUG)
        # Debug logging to help diagnose the issue
        utils.kodilog(
            "ThotHub: Flashvars found: {}".format("Yes" if flashvars else "No"),
            xbmc.LOGDEBUG,
        )
        utils.kodilog(
            "ThotHub: License code found: {}".format("Yes" if license_code else "No"),
            xbmc.LOGDEBUG,
        )
        utils.kodilog(
            "ThotHub: Blocked messages: {}".format(len(blocked_messages)), xbmc.LOGDEBUG
        )

        # Log snippet of HTML for debugging (first 500 chars of any script tag)
        script_tags = re.findall(
            r"<script[^>]*>(.*?)</script>", html, re.IGNORECASE | re.DOTALL
        )
        if script_tags:
            utils.kodilog(
                "ThotHub: Found {} script tags".format(len(script_tags)), xbmc.LOGDEBUG
            )
            for i, script in enumerate(script_tags[:3]):  # Log first 3 scripts
                snippet = script.strip()[:200].replace("\n", " ")
                utils.kodilog(
                    "ThotHub: Script {} snippet: {}...".format(i + 1, snippet),
                    xbmc.LOGDEBUG,
                )

        # Check for common video-related keywords
        keywords = ["video", "player", "mp4", "m3u8", "source", "stream"]
        for keyword in keywords:
            count = html.lower().count(keyword)
            if count > 0:
                utils.kodilog(
                    "ThotHub: HTML contains '{}' {} times".format(keyword, count),
                    xbmc.LOGDEBUG,
                )

        if blocked_messages:
            utils.notify("ThotHub", blocked_messages[0])
        else:
            utils.notify("Error", "Could not extract video URL")
        vp.progress.close()


@site.register()
def Search(url, keyword=None):
    """Search for videos on ThotHub."""
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # ThotHub uses /search/keyword/ format
        keyword_clean = keyword.replace(" ", "-")
        search_url = urllib_parse.urljoin(site.url, "search/{}/".format(urllib_parse.quote(keyword_clean)))
        List(search_url)


def _get_cached_video_page(url):
    return _VIDEO_PAGE_CACHE.get(url)


def _build_browser_headers():
    return {
        "User-Agent": utils.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def _fetch_video_page(url, headers=None):
    try:
        html = utils.getHtml(url, site.url, headers=headers or _build_browser_headers())
    except Exception as e:
        utils.kodilog(
            "ThotHub: Failed to fetch {} while checking privacy: {}".format(url, e),
            xbmc.LOGDEBUG,
        )
        return ""
    _VIDEO_PAGE_CACHE[url] = html
    return html


def _is_private_video(url):
    if VIDEO_FILTER_MODE != "public_only":
        return False

    html = _get_cached_video_page(url)
    if not html:
        html = _fetch_video_page(url)
    if not html:
        return False

    _, requires_login = _detect_access_messages(html)
    return requires_login


def _detect_access_messages(html):
    """Return (messages, requires_login) inferred from HTML blocks."""
    messages = []
    lowered = (html or "").lower()
    requires_login = False

    for marker, user_message in PRIVATE_MESSAGE_MAP.items():
        if marker in lowered:
            messages.append(user_message)
            requires_login = True

    attribute_patterns = [
        r'data-(?:private|logged-in|need-login)[="\'](?:true|1)[\'"]',
        r'class=["\'][^"\']*private-video[^"\']*["\']',
        r'id=["\']private-video-notice["\']',
    ]

    for pattern in attribute_patterns:
        if re.search(pattern, lowered):
            messages.append("ThotHub flagged this entry as private.")
            requires_login = True
            break

    return messages, requires_login

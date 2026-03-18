"""
Cumination
Copyright (C) 2017 Whitecream, hdgdl, Team Cumination
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

import os
import sqlite3
import json
import re
import time
import base64
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin

from resources.lib import utils
from resources.lib.http_timeouts import (
    HTTP_TIMEOUT_MANIFEST,
    HTTP_TIMEOUT_MEDIUM,
    HTTP_TIMEOUT_SHORT,
)
from six.moves import urllib_parse
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "stripchat",
    "[COLOR hotpink]stripchat.com[/COLOR]",
    "https://stripchat.com/",
    "stripchat.png",
    "stripchat",
    True,
)

# Stripchat's CDN increasingly rejects the addon-wide legacy Firefox UA on
# HLS segment requests. Use a modern browser UA for all live stream fetches.
STRIPCHAT_STREAM_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)
STRIPCHAT_DISABLED = True
STRIPCHAT_PROXY_SESSION_HEADERS = {}
STRIPCHAT_PROXY_SESSION_COOKIES = {}


def _normalize_model_image_url(url):
    if not isinstance(url, str) or not url:
        return ""
    normalized = url.strip()
    if normalized.startswith("//"):
        return "https:" + normalized
    if normalized.startswith("/"):
        return "https://stripchat.com" + normalized
    if normalized.startswith("http"):
        return normalized
    return ""


def _notify_stripchat_disabled():
    utils.notify("Stripchat", "Temporarily disabled")
    utils.kodilog("Stripchat: site is temporarily disabled")


def _stripchat_stream_headers(model_name=""):
    return {
        "User-Agent": STRIPCHAT_STREAM_UA,
        "Origin": "https://stripchat.com",
        "Referer": "https://stripchat.com/",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Not:A-Brand";v="99", "HeadlessChrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


def _load_cookie_dict_for_url(url):
    """Return saved addon cookies matching the given URL/domain."""
    try:
        parsed = urlparse(url if isinstance(url, str) else "")
        domain = (parsed.netloc or "").lower()
        if not domain:
            return {}
        clean_domain = domain[4:] if domain.startswith("www.") else domain
        cookies = {}
        for cookie in getattr(utils, "cj", []):
            cookie_name = getattr(cookie, "name", "")
            cookie_value = getattr(cookie, "value", "")
            cookie_domain = (getattr(cookie, "domain", "") or "").lstrip(".").lower()
            if (
                cookie_name
                and isinstance(cookie_value, str)
                and cookie_domain
                and (
                    clean_domain.endswith(cookie_domain)
                    or cookie_domain.endswith(clean_domain)
                )
            ):
                cookies[cookie_name] = cookie_value
        return cookies
    except Exception as exc:
        utils.kodilog("Stripchat cookies: load failed {}".format(str(exc)))
        return {}


def _prime_stream_session(model_url, model_name):
    """Warm Cloudflare/session cookies before manifest and segment fetches."""
    if not isinstance(model_url, str) or not model_url.startswith("http"):
        return
    try:
        utils.kodilog(
            "Stripchat: Priming stream session via {}".format(model_url[:140])
        )
        utils.get_html_with_cloudflare_retry(
            model_url,
            referer=site.url,
            headers=_stripchat_stream_headers(model_name),
            retry_on_empty=True,
        )
    except Exception as exc:
        utils.kodilog("Stripchat: Session prime failed: {}".format(str(exc)))


def _ensure_low_latency_playlist(url):
    if not isinstance(url, str) or ".m3u8" not in url:
        return url
    params = {"playlistType": "lowLatency"}
    lower = url.lower()
    if "media-hls." in lower or "doppiocdn" in lower:
        params["preferredVideoCodec"] = "h264"
    return _merge_query(url, params)


def _should_use_manifest_proxy(stream_url):
    """Identify Stripchat manifests that require localhost rewrite/proxying."""
    if not isinstance(stream_url, str) or ".m3u8" not in stream_url:
        return False
    return (
        "media-hls." in stream_url
        or "doppiocdn" in stream_url
        or "playlistType=lowLatency" in stream_url
    )


def _iter_manifest_probe_urls(url):
    """Probe LL-HLS first, then the original URL for older/plain manifests."""
    if not isinstance(url, str) or ".m3u8" not in url:
        return [url]
    ll_url = _ensure_low_latency_playlist(url)
    if ll_url == url:
        return [url]
    return [ll_url, url]


def _live_preview_url(url, snapshot_ts=None, cache_bust=None):
    normalized = _normalize_model_image_url(url)
    if not normalized:
        return ""
    if "strpst.com/previews/" in normalized and "-thumb-small" in normalized:
        # Stripchat API currently exposes only thumb-small in many responses.
        # The corresponding thumb-big endpoint exists and gives a clearer live frame.
        normalized = normalized.replace("-thumb-small", "-thumb-big")
    # Attach snapshot/cache-bust params so Kodi does not hold stale thumbnails.
    if "strpst.com/previews/" in normalized and snapshot_ts:
        sep = "&" if "?" in normalized else "?"
        normalized = "{}{}t={}".format(normalized, sep, snapshot_ts)
    if "strpst.com/previews/" in normalized and cache_bust:
        sep = "&" if "?" in normalized else "?"
        normalized = "{}{}cb={}".format(normalized, sep, cache_bust)
    return normalized


def _model_screenshot(model, cache_bust=None):
    if not isinstance(model, dict):
        return ""
    model_id = model.get("id")
    snapshot_ts = model.get("snapshotTimestamp") or model.get(
        "popularSnapshotTimestamp"
    )
    if snapshot_ts and model_id:
        return "https://img.doppiocdn.com/thumbs/{0}/{1}_webp".format(
            snapshot_ts, model_id
        )
    image_fields = (
        "previewUrlThumbSmall",
        "previewUrlThumbBig",
        "previewUrlThumbLarge",
        "preview",
        "previewUrl",
        "snapshotUrl",
        "avatarUrl",
        "thumbnailUrl",
        "thumbUrl",
        "imageUrl",
        "posterUrl",
    )
    for field in image_fields:
        value = model.get(field)
        if isinstance(value, dict):
            for nested_key in ("url", "src", "https", "absolute"):
                img = _live_preview_url(
                    value.get(nested_key), snapshot_ts, cache_bust=cache_bust
                )
                if img:
                    return img
            continue
        img = _live_preview_url(value, snapshot_ts, cache_bust=cache_bust)
        if img:
            return img

    return ""


def _is_ad_or_stub_manifest(text):
    if not text or "#EXTM3U" not in text:
        return True
    # Stripchat ad manifests often have very few segments or specific keywords
    if "cpa/v2/stream.m3u8" in text or "ad-provider" in text:
        return True
    if text.count("#EXTINF") < 2:
        return True
    return False


def _merge_query(url, params):
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    for key, value in params.items():
        if key not in query:
            query[key] = [value]
    new_query = urlencode(query, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


def _normalize_stream_cdn_url(url):
    if not isinstance(url, str) or not url:
        return url

    normalized = url.replace(".doppiocdn.com", ".doppiocdn.net")
    parsed = urlparse(normalized)
    if ".m3u8" not in parsed.path:
        return normalized

    query = parse_qs(parsed.query, keep_blank_values=True)
    # We used to pop playlistType, but we now know it's needed for correct hashes
    # in MOUFLON manifests.
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query, doseq=True),
            parsed.fragment,
        )
    )


def _encode_proxy_target(url):
    if not isinstance(url, str):
        return ""
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii")


def _decode_proxy_target(value):
    if not isinstance(value, str) or not value:
        return ""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii")).decode(
        "utf-8"
    )


def _rewrite_mouflon_manifest_for_kodi(manifest_text, base_url=""):
    """Rewrite a MOUFLON HLS manifest so Kodi can play it.

    MOUFLON is Stripchat's proprietary LL-HLS extension. Each real segment URL
    is carried in an #EXT-X-MOUFLON:URI:<url> tag immediately before the
    placeholder ../media.mp4 segment line. This function:
      - replaces every placeholder segment with the corresponding real URL
      - makes the EXT-X-MAP URI absolute
      - strips low-latency and MOUFLON-specific tags ISA doesn't understand
    """
    if not manifest_text:
        return manifest_text

    _STRIP_PREFIXES = (
        "#EXT-X-SERVER-CONTROL:",
        "#EXT-X-PART-INF:",
        "#EXT-X-PART:",
        "#EXT-X-PRELOAD-HINT:",
        "#EXT-X-RENDITION-REPORT:",
        "#EXT-X-MOUFLON:",
        "#EXT-X-MOUFLON-ADVERT",
    )

    lines_out = []
    pending_mouflon_url = None
    pending_full_segment_url = None
    pending_part_segments = []
    skip_next_placeholder = False
    
    # Track metrics for logging
    replaced_segments = 0
    replaced_parts = 0
    map_rewrites = 0
    normalized_relative = 0
    
    lines = manifest_text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#EXT-X-MOUFLON:URI:"):
            utils.kodilog("Stripchat raw mouflon line: {!r}".format(line))
            mouflon_url = stripped[len("#EXT-X-MOUFLON:URI:") :].strip()
            if mouflon_url.startswith("http://") or mouflon_url.startswith("https://"):
                pass
            elif mouflon_url.startswith("/"):
                mouflon_url = urljoin(base_url, mouflon_url)
            elif "://" not in mouflon_url:
                mouflon_url = urljoin(base_url, mouflon_url)
            utils.kodilog("Stripchat raw mouflon uri: {!r}".format(mouflon_url))
            pending_mouflon_url = mouflon_url
            if "_part" in mouflon_url or "part" in mouflon_url:
                pending_full_segment_url = None
            else:
                pending_full_segment_url = mouflon_url
            continue

        if stripped.startswith("#EXT-X-PART:"):
            duration_match = re.search(r"DURATION=([0-9.]+)", stripped)
            if duration_match and pending_mouflon_url and ("_part" in pending_mouflon_url or "part" in pending_mouflon_url):
                part_url = pending_mouflon_url
                pending_part_segments.append((duration_match.group(1), part_url))
            pending_mouflon_url = None
            continue

        if any(stripped.startswith(p) for p in _STRIP_PREFIXES):
            continue

        if stripped.startswith("#EXT-X-MAP:URI="):
            uri_match = re.search(r'URI="([^"]+)"', stripped)
            if uri_match:
                map_uri = uri_match.group(1)
                if not map_uri.startswith("http"):
                    line = line.replace(map_uri, urljoin(base_url, map_uri))
                    map_rewrites += 1
            lines_out.append(line)
            continue

        if stripped.startswith("#EXTINF:"):
            # Check if a full MOUFLON URI follows this EXTINF
            found_full_mouflon = None
            for j in range(i + 1, min(i + 5, len(lines))):
                if (
                    lines[j].strip().startswith("#EXT-X-MOUFLON:URI:")
                    and ".mp4" in lines[j]
                    and "_part" not in lines[j]
                ):
                    found_full_mouflon = lines[j].strip()[
                        len("#EXT-X-MOUFLON:URI:")
                    :]
                    if not found_full_mouflon.startswith("http"):
                        found_full_mouflon = urljoin(base_url, found_full_mouflon)
                    break
                if not lines[j].strip().startswith("#"):
                    break

            if pending_part_segments:
                for duration, part_url in pending_part_segments:
                    lines_out.append("#EXTINF:{0},".format(duration))
                    lines_out.append(part_url)
                    replaced_parts += 1
                pending_part_segments = []
                skip_next_placeholder = True
                pending_full_segment_url = None
                pending_mouflon_url = None
                continue
            selected_full_segment = found_full_mouflon or pending_full_segment_url
            if selected_full_segment:
                if not stripped.endswith(","):
                    stripped += ","
                lines_out.append(stripped)
                lines_out.append(selected_full_segment)
                skip_next_placeholder = True
                replaced_segments += 1
                pending_full_segment_url = None
                pending_mouflon_url = None
                continue

        if stripped and not stripped.startswith("#"):
            if skip_next_placeholder:
                skip_next_placeholder = False
                pending_mouflon_url = None
                pending_full_segment_url = None
                continue
            
            # If we didn't skip it, and it's a relative URL, make it absolute
            if not stripped.startswith("http"):
                lines_out.append(urljoin(base_url, stripped))
                normalized_relative += 1
                continue

        lines_out.append(line)

    if not lines_out:
        utils.kodilog("Stripchat rewrite: produced empty manifest")
        return ""
    rewritten = "\n".join(lines_out) + "\n"
    utils.kodilog(
        "Stripchat rewrite: in_lines={0} out_lines={1} replaced_segments={2} replaced_parts={3} map_rewrites={4} normalized_relative={5}".format(
            len(manifest_text.splitlines()),
            len(lines_out),
            replaced_segments,
            replaced_parts,
            map_rewrites,
            normalized_relative,
        )
    )
    return rewritten


def _rewrite_mouflon_for_isa(manifest_text, base_url):
    return _rewrite_mouflon_manifest_for_kodi(manifest_text, base_url)


def _keep_only_stable_segments(
    manifest_text,
    fetch_headers=None,
    keep_count=3,
    edge_buffer=1,
):
    """Build a minimal manifest from older, reachable full segments.

    Stripchat's newest live-edge segments can disappear before Kodi fetches them.
    For playback stability, skip the freshest segment and keep only a few older
    full segments that respond successfully.
    """
    if not manifest_text or "#EXTM3U" not in manifest_text:
        utils.kodilog("Stripchat stable: skipped, manifest missing or invalid")
        return manifest_text

    header_prefixes = (
        "#EXTM3U",
        "#EXT-X-VERSION:",
        "#EXT-X-TARGETDURATION:",
        "#EXT-X-INDEPENDENT-SEGMENTS",
        "#EXT-X-MAP:",
    )

    header_lines = []
    segments = []
    lines = manifest_text.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if stripped.startswith("#EXTINF:") and idx + 1 < len(lines):
            segment_url = lines[idx + 1].strip()
            if segment_url and not segment_url.startswith("#"):
                segments.append((line, lines[idx + 1]))
                idx += 2
                continue
        if stripped.startswith(header_prefixes):
            header_lines.append(line)
        idx += 1

    if len(segments) <= edge_buffer:
        utils.kodilog(
            "Stripchat stable: skipped filtering, segments={0} edge_buffer={1}".format(
                len(segments), edge_buffer
            )
        )
        return manifest_text

    def _segment_ok(segment_url):
        try:
            probe_url = segment_url
            resp = requests.get(
                probe_url,
                headers=fetch_headers or None,
                timeout=HTTP_TIMEOUT_SHORT,
                stream=True,
            )
            ok = resp.status_code == 200
            utils.kodilog(
                "Stripchat stable: probe {0} -> HTTP {1}".format(
                    probe_url[:140], resp.status_code
                )
            )
            resp.close()
            return ok
        except Exception as e:
            utils.kodilog(
                "Stripchat stable: probe error for {0}: {1}".format(
                    probe_url[:140], str(e)
                )
            )
            return False

    utils.kodilog(
        "Stripchat stable: header_lines={0} segments={1} keep_count={2} edge_buffer={3}".format(
            len(header_lines), len(segments), keep_count, edge_buffer
        )
    )

    stable_segments = []
    last_usable_index = len(segments) - edge_buffer
    for idx in range(last_usable_index - 1, -1, -1):
        extinf_line, segment_url = segments[idx]
        utils.kodilog(
            "Stripchat stable: testing candidate index={0} url={1}".format(
                idx, segment_url.strip()[:140]
            )
        )
        if _segment_ok(segment_url.strip()):
            stable_segments.append((extinf_line, segment_url))
            utils.kodilog(
                "Stripchat stable: accepted candidate index={0} url={1}".format(
                    idx, segment_url.strip()[:140]
                )
            )
            if len(stable_segments) >= keep_count:
                break
        else:
            utils.kodilog(
                "Stripchat stable: rejected candidate index={0} url={1}".format(
                    idx, segment_url.strip()[:140]
                )
            )

    if not stable_segments:
        utils.kodilog(
            "Stripchat stable: no stable segments found, keeping original manifest"
        )
        return manifest_text

    stable_segments.reverse()
    out_lines = list(header_lines)
    for extinf_line, segment_url in stable_segments:
        out_lines.append(extinf_line)
        out_lines.append(segment_url)
    utils.kodilog(
        "Stripchat stable: selected {0} segment(s): {1}".format(
            len(stable_segments),
            " | ".join(segment_url.strip()[:100] for _, segment_url in stable_segments),
        )
    )
    return "\n".join(out_lines) + "\n"


def _proxy_segment_urls_in_manifest(manifest_text, port):
    """Rewrite absolute CDN segment URLs to route through the local proxy.

    ISA fetches segments directly from the CDN without Origin/Referer headers,
    causing 404 errors. By rewriting URLs to http://127.0.0.1:{port}/seg?url=...,
    all segment fetches go through our proxy which adds the required headers.
    """
    lines = manifest_text.splitlines()
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#EXT-X-MAP:URI="):
            uri_match = re.search(r'URI="([^"]+)"', stripped)
            if uri_match:
                cdn_url = uri_match.group(1)
                if cdn_url.startswith("http"):
                    proxy_url = "http://127.0.0.1:{0}/seg?u={1}".format(
                        port, _encode_proxy_target(cdn_url)
                    )
                    line = line.replace(cdn_url, proxy_url)
        elif stripped and not stripped.startswith("#") and stripped.startswith("http"):
            line = "http://127.0.0.1:{0}/seg?u={1}".format(
                port, _encode_proxy_target(stripped)
            )
        out.append(line)
    return "\n".join(out) + "\n"


def _start_manifest_proxy(selected_url, name):
    """Start a local HTTP server that serves a MOUFLON-rewritten manifest.

    ISA cannot handle MOUFLON HLS extensions, so we intercept the manifest,
    rewrite the placeholder ../media.mp4 segments with real CDN URLs, and
    serve the clean manifest over localhost HTTP for ISA to poll.

    Returns the localhost URL to pass to ISA, or None on failure.
    """
    import http.server
    import threading
    import socket
    import socketserver

    selected_url = _normalize_stream_cdn_url(selected_url)
    utils.kodilog(
        "Stripchat proxy: starting for {}".format(selected_url[:140])
    )
    parsed = urlparse(selected_url)
    base_url = "{0}://{1}{2}/".format(
        parsed.scheme,
        parsed.netloc,
        "/".join(parsed.path.split("/")[:-1]),
    )
    
    # Only signing params belong on child manifests / segment URLs.
    fetch_headers = _stripchat_stream_headers(name)
    if isinstance(STRIPCHAT_PROXY_SESSION_HEADERS, dict):
        fetch_headers.update(
            {
                key: value
                for key, value in STRIPCHAT_PROXY_SESSION_HEADERS.items()
                if isinstance(key, str) and isinstance(value, str) and value
            }
        )

    # Shared session so CDN cookies from the manifest fetch carry over to
    # all segment requests (some CDNs set auth cookies on the manifest URL).
    session = requests.Session()
    session.headers.update(fetch_headers)
    saved_cookies = _load_cookie_dict_for_url(selected_url)
    if saved_cookies:
        session.cookies.update(saved_cookies)
        utils.kodilog(
            "Stripchat proxy: loaded {} saved cookie(s)".format(len(saved_cookies))
        )
    if isinstance(STRIPCHAT_PROXY_SESSION_COOKIES, dict):
        session.cookies.update(
            {
                key: value
                for key, value in STRIPCHAT_PROXY_SESSION_COOKIES.items()
                if isinstance(key, str) and isinstance(value, str)
            }
        )

    state = {
        "content": b"",
        "last_selected_url": selected_url,
        "last_activity": time.time(),
    }
    state_lock = threading.Lock()
    fetch_round = {"count": 0}
    shutdown_started = {"value": False}

    # Bind socket first so port is known for segment URL rewriting.
    # Some test/sandbox environments disallow localhost listeners entirely.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    except OSError as exc:
        utils.kodilog("Stripchat proxy: bind failed, falling back: {}".format(str(exc)))
        return None

    def _fetch_and_rewrite(extra_query=None):
        nonlocal selected_url
        try:
            fetch_round["count"] += 1
            upstream_url = selected_url
            forwarded_params = {}
            if isinstance(extra_query, dict):
                forwarded_params = {
                    key: values[0]
                    for key, values in extra_query.items()
                    if key in ("_HLS_msn", "_HLS_part") and values
                }
            if forwarded_params:
                selected_parts = list(urlparse(selected_url))
                selected_query = parse_qs(selected_parts[4], keep_blank_values=True)
                for key, value in forwarded_params.items():
                    selected_query[key] = [value]
                selected_parts[4] = urlencode(selected_query, doseq=True)
                upstream_url = urlunparse(selected_parts)
                utils.kodilog(
                    "Stripchat proxy: forwarding LL-HLS params {}".format(
                        forwarded_params
                    )
                )
            utils.kodilog(
                "Stripchat proxy: initial manifest GET {}".format(
                    upstream_url[:140]
                )
            )
            resp = session.get(upstream_url, timeout=HTTP_TIMEOUT_MANIFEST)
            utils.kodilog(
                "Stripchat proxy: initial status {}".format(resp.status_code)
            )
            utils.kodilog(
                "Stripchat proxy: manifest cookies resp={0} session={1}".format(
                    resp.cookies.get_dict(), session.cookies.get_dict()
                )
            )
            
            # Handle possible pkey expiration (403/404)
            if resp.status_code in (403, 404) and fetch_round["count"] > 1:
                utils.kodilog("Stripchat proxy: manifest returned {0}, attempting to refresh model details".format(resp.status_code))
                # This is a bit tricky as we don't have easy access to the full logic here
                # For now, just log it. A better fix involves a more global state.
            
            if resp.status_code != 200:
                return

            rewritten = _rewrite_mouflon_for_isa(resp.text, base_url)
            utils.kodilog(
                "Stripchat proxy: rewritten manifest size {}".format(
                    len(rewritten or "")
                )
            )
            if rewritten and "#EXTM3U" in rewritten:
                if "media.mp4" in rewritten:
                    utils.kodilog(
                        "Stripchat proxy: rewrite incomplete, media.mp4 still present"
                    )
                else:
                    utils.kodilog(
                        "Stripchat proxy: rewrite removed placeholder media.mp4 references"
                    )
                # Stripchat's LL-HLS segments are not reliably probeable outside
                # an active playback session. Serve the rewritten manifest as-is
                # and let the player drive the HLS session.
                rewritten = _proxy_segment_urls_in_manifest(rewritten, port)
                with state_lock:
                    state["content"] = rewritten.encode("utf-8")
                    state["last_selected_url"] = upstream_url
        except Exception as e:
            utils.kodilog("Stripchat proxy: fetch error: {}".format(str(e)))

    _fetch_and_rewrite()
    with state_lock:
        if not state["content"]:
            utils.kodilog("Stripchat: Manifest proxy initial fetch failed, falling back")
            return None

    class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    class ManifestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            with state_lock:
                state["last_activity"] = time.time()
            parsed_path = urlparse(self.path)
            if parsed_path.path == "/seg":
                params = parse_qs(parsed_path.query, keep_blank_values=True)
                encoded = params.get("u", [""])[0]
                cdn_url = _decode_proxy_target(encoded) if encoded else ""
                if not cdn_url:
                    self.send_response(400)
                    self.end_headers()
                    return
                try:
                    seg_resp = session.get(
                        cdn_url, timeout=HTTP_TIMEOUT_MEDIUM, stream=True
                    )
                    self.send_response(seg_resp.status_code)
                    self.send_header(
                        "Content-Type",
                        seg_resp.headers.get("Content-Type", "video/mp4"),
                    )
                    cl = seg_resp.headers.get("Content-Length")
                    if cl:
                        self.send_header("Content-Length", cl)
                    self.end_headers()
                    for chunk in seg_resp.iter_content(chunk_size=65536):
                        self.wfile.write(chunk)
                except Exception as e:
                    utils.kodilog(
                        "Stripchat proxy: segment fetch error: {}".format(str(e))
                    )
                    try:
                        self.send_response(503)
                        self.end_headers()
                    except Exception:
                        pass
            else:
                _fetch_and_rewrite(parse_qs(parsed_path.query, keep_blank_values=True))
                with state_lock:
                    content = state["content"]
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content)

        def log_message(self, fmt, *args): pass

    srv = _ThreadingHTTPServer(("127.0.0.1", port), ManifestHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def _shutdown_proxy(reason):
        if shutdown_started["value"]:
            return
        shutdown_started["value"] = True
        utils.kodilog("Stripchat proxy: shutting down ({})".format(reason))
        try:
            srv.shutdown()
        except Exception:
            pass
        try:
            srv.server_close()
        except Exception:
            pass
        try:
            session.close()
        except Exception:
            pass

    def _idle_watch():
        idle_timeout = 8.0
        while not shutdown_started["value"]:
            time.sleep(1.0)
            with state_lock:
                idle_for = time.time() - state.get("last_activity", time.time())
            if idle_for >= idle_timeout:
                _shutdown_proxy("idle {:.1f}s".format(idle_for))
                return

    threading.Thread(target=_idle_watch, daemon=True).start()

    utils.kodilog(
        "Stripchat proxy: ready at http://127.0.0.1:{}/manifest.m3u8".format(port)
    )
    return "http://127.0.0.1:{}/manifest.m3u8".format(port)


@site.register(default_mode=True)
def Main():
    if STRIPCHAT_DISABLED:
        _notify_stripchat_disabled()
        utils.eod()
        return
    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    site.add_dir(
        "[COLOR red]Refresh Stripchat images[/COLOR]",
        "",
        "clean_database",
        "",
        Folder=False,
    )

    bu = "https://stripchat.com/api/front/models?limit=80&parentTag=autoTagNew&sortBy=trending&offset=0&primaryTag="
    if female:
        site.add_dir(
            "[COLOR hotpink]Female HD[/COLOR]",
            "{0}girls&broadcastHD=true".format(bu),
            "List",
            "",
            "",
        )
        site.add_dir(
            "[COLOR hotpink]Female[/COLOR]", "{0}girls".format(bu), "List", "", ""
        )
    if couple:
        site.add_dir(
            "[COLOR hotpink]Couples HD[/COLOR]",
            "{0}couples&broadcastHD=true".format(bu),
            "List",
            "",
            "",
        )
        site.add_dir(
            "[COLOR hotpink]Couples[/COLOR]", "{0}couples".format(bu), "List", "", ""
        )
        site.add_dir(
            "[COLOR hotpink]Couples (Site)[/COLOR]",
            "https://stripchat.com/couples",
            "List2",
            "",
            "",
        )
    if male:
        site.add_dir(
            "[COLOR hotpink]Male HD[/COLOR]",
            "{0}men&broadcastHD=true".format(bu),
            "List",
            "",
            "",
        )
        site.add_dir("[COLOR hotpink]Male[/COLOR]", "{0}men".format(bu), "List", "", "")
    if trans:
        site.add_dir(
            "[COLOR hotpink]Transsexual HD[/COLOR]",
            "{0}trans&broadcastHD=true".format(bu),
            "List",
            "",
            "",
        )
        site.add_dir(
            "[COLOR hotpink]Transsexual[/COLOR]", "{0}trans".format(bu), "List", "", ""
        )
    utils.eod()


@site.register()
def List(url, page=1):
    if STRIPCHAT_DISABLED:
        _notify_stripchat_disabled()
        utils.eod()
        return None
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    # utils._getHtml will automatically use FlareSolverr if Cloudflare is detected
    try:
        utils.kodilog("Stripchat: Fetching model list from API")
        response, _ = utils.get_html_with_cloudflare_retry(
            url,
            referer=site.url,
            retry_on_empty=True,
        )
        if not response:
            utils.kodilog("Stripchat: Empty response from API")
            utils.notify("Error", "Could not load Stripchat models")
            return None
        data = json.loads(response)
        model_list = data["models"]
        utils.kodilog(
            "Stripchat: Successfully loaded {} models".format(len(model_list))
        )
    except Exception as e:
        utils.kodilog("Stripchat: Error loading model list: {}".format(str(e)))
        utils.notify("Error", "Could not load Stripchat models")
        return None

    cache_bust = int(time.time())
    for model in model_list:
        raw_name = model.get("username")
        if not raw_name:
            continue
        name = utils.cleanhtml(raw_name)
        videourl = model.get("hlsPlaylist") or ""
        img = _model_screenshot(model, cache_bust=cache_bust)
        fanart = img
        subject = ""
        if model.get("groupShowTopic"):
            subject += model.get("groupShowTopic") + "[CR]"
        if model.get("country"):
            subject += "[COLOR deeppink]Location: [/COLOR]{0}[CR]".format(
                utils.get_country(model.get("country"))
            )
        if model.get("languages"):
            langs = [utils.get_language(x) for x in model.get("languages")]
            subject += "[COLOR deeppink]Languages: [/COLOR]{0}[CR]".format(
                ", ".join(langs)
            )
        if model.get("broadcastGender"):
            subject += "[COLOR deeppink]Gender: [/COLOR]{0}[CR]".format(
                model.get("broadcastGender")
            )
        if model.get("viewersCount"):
            subject += "[COLOR deeppink]Watching: [/COLOR]{0}[CR][CR]".format(
                model.get("viewersCount")
            )
        if model.get("tags"):
            subject += "[COLOR deeppink]#[/COLOR]"
            tags = [t for t in model.get("tags") if "tag" not in t.lower()]
            subject += "[COLOR deeppink] #[/COLOR]".join(tags)
        site.add_download_link(
            name, videourl, "Playvid", img, subject, noDownload=True, fanart=fanart
        )

    total_items = data.get("filteredCount", 0)
    nextp = (page * 80) < total_items
    if nextp:
        next = (page * 80) + 1
        lastpg = -1 * (-total_items // 80)
        page += 1
        nurl = re.sub(r"offset=\d+", "offset={0}".format(next), url)
        site.add_dir(
            "Next Page.. (Currently in Page {0} of {1})".format(page - 1, lastpg),
            nurl,
            "List",
            site.img_next,
            page,
        )

    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            for domain_fragment in (".strpst.com", ".doppiocdn.com"):
                pattern = "%" + domain_fragment + "%"
                rows = conn.execute(
                    "SELECT id, cachedurl FROM texture WHERE url LIKE ?;",
                    (pattern,),
                ).fetchall()
                for row in rows:
                    conn.execute("DELETE FROM sizes WHERE idtexture = ?;", (row[0],))
                    try:
                        os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                    except Exception as e:
                        utils.kodilog(
                            "@@@@Cumination: Silent failure in stripchat: " + str(e)
                        )
                conn.execute("DELETE FROM texture WHERE url LIKE ?;", (pattern,))
            if showdialog:
                utils.notify("Finished", "Stripchat images cleared")
    except Exception as e:
        utils.kodilog("@@@@Cumination: Silent failure in stripchat: " + str(e))


@site.register()
def Playvid(url, name):
    if STRIPCHAT_DISABLED:
        _notify_stripchat_disabled()
        return
    vp = utils.VideoPlayer(name, IA_check="IA")
    vp.progress.update(25, "[CR]Loading video page[CR]")

    def _load_model_details(model_name):
        headers = {
            "User-Agent": utils.USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://stripchat.com",
            "Referer": "https://stripchat.com/{0}".format(model_name),
        }
        # The external widget API returns rich stream data (stream.url, stream.urls,
        # snapshotUrl etc.) and supports modelsList lookup by username.
        endpoint = (
            "https://stripchat.com/api/external/v4/widget/?limit=1&modelsList={0}"
        )
        try:
            utils.kodilog(
                "Stripchat: Fetching model details: {}".format(
                    endpoint.format(model_name)
                )
            )
            response, _ = utils.get_html_with_cloudflare_retry(
                endpoint.format(model_name),
                site.url,
                headers=headers,
                retry_on_empty=True,
            )
            if not response:
                utils.kodilog("Stripchat: Empty response from widget endpoint")
                return None
            payload = json.loads(response)
            models = payload.get("models") if isinstance(payload, dict) else None
            if models and len(models) > 0:
                for model in models:
                    if model.get("username", "").lower() == model_name.lower():
                        utils.kodilog(
                            "Stripchat: Successfully loaded model details for {}".format(
                                model_name
                            )
                        )
                        return model
                utils.kodilog(
                    "Stripchat: Widget API returned models but none matched {}".format(
                        model_name
                    )
                )
                if models:
                    utils.kodilog(
                        "Stripchat: First returned model was: {}".format(
                            models[0].get("username")
                        )
                    )
            else:
                utils.kodilog("Stripchat: No models in widget response")
        except json.JSONDecodeError as e:
            utils.kodilog("Stripchat: JSON decode error: {}".format(str(e)))
        except Exception as e:
            utils.kodilog("Stripchat: Error loading model details: {}".format(str(e)))
        return None

    def _pick_stream(model_data, fallback_url):
        candidates = []
        stream_info = model_data.get("stream") if model_data else None
        is_online_flag = None
        manifest_probe_cache = {}
        manifest_probe_errors = {}

        def _mirror_saaws_to_doppi(stream_url):
            if not isinstance(stream_url, str) or "saawsedge.com" not in stream_url:
                return None
            if utils.addon.getSetting("stripchat_mirror") == "false":
                return None
            return stream_url.replace(
                "edge-hls.saawsedge.com", "edge-hls.doppiocdn.com"
            )

        # Treat online flags as advisory only; keep stream candidates if present.
        if model_data:
            is_online_values = [
                model_data.get("isOnline"),
                model_data.get("isBroadcasting"),
            ]
            explicit_values = [v for v in is_online_values if isinstance(v, bool)]
            if explicit_values:
                is_online_flag = any(explicit_values)
                if not is_online_flag:
                    utils.kodilog(
                        "Stripchat: Model {} reported offline by API".format(name)
                    )

        if isinstance(stream_info, dict):
            # Explicit urls map (new API structure)
            urls_map = stream_info.get("urls") or stream_info.get("files") or {}
            hls_map = urls_map.get("hls") if isinstance(urls_map, dict) else {}
            if isinstance(hls_map, dict):
                for quality, data in hls_map.items():
                    quality_label = str(quality).lower()
                    if isinstance(data, dict):
                        for key in ("absolute", "https", "url", "src"):
                            stream_url = data.get(key)
                            if isinstance(stream_url, str) and stream_url.startswith(
                                "http"
                            ):
                                utils.kodilog(
                                    "Stripchat: Found stream candidate: {} - {}".format(
                                        quality_label, stream_url[:80]
                                    )
                                )
                                candidates.append((quality_label, stream_url))
                                break
                    elif isinstance(data, str) and data.startswith("http"):
                        utils.kodilog(
                            "Stripchat: Found stream candidate: {} - {}".format(
                                quality_label, data[:80]
                            )
                        )
                        candidates.append((quality_label, data))
            elif isinstance(urls_map, dict):
                # Flat quality dict: stream.urls = {"480p": "url", "240p": "url", ...}
                for quality, data in urls_map.items():
                    quality_label = str(quality).lower()
                    if isinstance(data, str) and data.startswith("http"):
                        utils.kodilog(
                            "Stripchat: Found quality stream: {} - {}".format(
                                quality_label, data[:80]
                            )
                        )
                        candidates.append((quality_label, data))
                    elif isinstance(data, dict):
                        for key in ("absolute", "https", "url", "src"):
                            stream_url = data.get(key)
                            if isinstance(stream_url, str) and stream_url.startswith(
                                "http"
                            ):
                                utils.kodilog(
                                    "Stripchat: Found quality stream: {} - {}".format(
                                        quality_label, stream_url[:80]
                                    )
                                )
                                candidates.append((quality_label, stream_url))
                                break
            # Some responses keep direct URL on stream['url']
            stream_url = stream_info.get("url")
            if isinstance(stream_url, str) and stream_url.startswith("http"):
                utils.kodilog(
                    "Stripchat: Found direct stream URL: {}".format(stream_url[:80])
                )
                candidates.append(("direct", stream_url))
        # Legacy field on model root
        if model_data and isinstance(model_data.get("hlsPlaylist"), str):
            hls_url = model_data["hlsPlaylist"]
            utils.kodilog("Stripchat: Found hlsPlaylist: {}".format(hls_url[:80]))
            candidates.append(("playlist", hls_url))
        if isinstance(fallback_url, str) and fallback_url.startswith("http"):
            utils.kodilog("Stripchat: Using fallback URL: {}".format(fallback_url[:80]))
            candidates.append(("fallback", fallback_url))

        mirrored = []
        for label, candidate_url in list(candidates):
            mirror_url = _mirror_saaws_to_doppi(candidate_url)
            if mirror_url and mirror_url != candidate_url:
                utils.kodilog(
                    "Stripchat: Added mirrored stream candidate: {} - {}".format(
                        label, mirror_url[:80]
                    )
                )
                mirrored.append(("{}-mirror".format(label), mirror_url))
        candidates.extend(mirrored)

        # Some list URLs are pinned to low variants like "<id>_240p.m3u8".
        # Try to promote those to "<id>.m3u8" (often "source"/best stream) when valid.
        def _promote_variant_to_source_url(stream_url):
            if not isinstance(stream_url, str) or ".m3u8" not in stream_url:
                return None
            match = re.search(r"/master/(\d+)_\d{3,4}p\.m3u8($|\?)", stream_url)
            if not match:
                return None

            source_url = stream_url.replace(
                "/master/{}_".format(match.group(1)),
                "/master/{}.".format(match.group(1)),
            )
            source_url = re.sub(
                r"/master/(\d+)\.\d{3,4}p\.m3u8",
                r"/master/\1.m3u8",
                source_url,
            )
            if source_url == stream_url:
                return None

            try:
                probe_headers = _stripchat_stream_headers(name)
                for probe_url in _iter_manifest_probe_urls(source_url):
                    probe_data = utils._getHtml(
                        probe_url,
                        site.url,
                        headers=probe_headers,
                        error="throw",
                    )
                    if isinstance(probe_data, str) and "#EXTM3U" in probe_data:
                        utils.kodilog(
                            "Stripchat: Promoted variant stream to source playlist: {}".format(
                                source_url[:80]
                            )
                        )
                        return source_url
            except Exception as e:
                utils.kodilog(
                    "Stripchat: Source playlist probe failed for {}: {}".format(
                        source_url[:80], str(e)
                    )
                )
            return None

        def _promote_variant_to_auto_url(stream_url):
            if not isinstance(stream_url, str) or ".m3u8" not in stream_url:
                return None
            match = re.search(r"/master/(\d+)_\d{3,4}p\.m3u8($|\?)", stream_url)
            if not match:
                return None

            auto_url = stream_url.replace(
                "/master/{}_".format(match.group(1)),
                "/master/{}_".format(match.group(1)),
            )
            auto_url = re.sub(
                r"/master/(\d+)_\d{3,4}p\.m3u8",
                r"/master/\1_auto.m3u8",
                auto_url,
            )
            if auto_url == stream_url:
                return None

            try:
                probe_headers = _stripchat_stream_headers(name)
                for probe_url in _iter_manifest_probe_urls(auto_url):
                    probe_data = utils._getHtml(
                        probe_url,
                        site.url,
                        headers=probe_headers,
                        error="throw",
                    )
                    if isinstance(probe_data, str) and "#EXTM3U" in probe_data:
                        utils.kodilog(
                            "Stripchat: Promoted variant stream to auto playlist: {}".format(
                                auto_url[:80]
                            )
                        )
                        return auto_url
            except Exception as e:
                utils.kodilog(
                    "Stripchat: Auto playlist probe failed for {}: {}".format(
                        auto_url[:80], str(e)
                    )
                )
            return None

        def _fetch_manifest_text(manifest_url):
            if not isinstance(manifest_url, str) or ".m3u8" not in manifest_url:
                return ""
            if manifest_url in manifest_probe_cache:
                return manifest_probe_cache[manifest_url]
            text = ""
            headers = _stripchat_stream_headers(name)
            last_error = None
            for probe_url in _iter_manifest_probe_urls(manifest_url):
                try:
                    text = utils._getHtml(
                        probe_url,
                        site.url,
                        headers=headers,
                        error="throw",
                    )
                    if isinstance(text, str) and "#EXTM3U" in text:
                        manifest_probe_errors.pop(manifest_url, None)
                        break
                except Exception as e:
                    last_error = e
                    utils.kodilog(
                        "Stripchat: Manifest probe failed for {}: {}".format(
                            probe_url[:80], str(e)
                        )
                    )
                    err = str(e).lower()
                    if (
                        "name or service not known" in err
                        or "could not resolve host" in err
                    ):
                        manifest_probe_errors[manifest_url] = "dns"
                text = ""
            if not isinstance(text, str) or "#EXTM3U" not in text:
                # Some CDN paths (notably doppiocdn media manifests) are easier to
                # inspect without custom headers; use requests as a probe fallback.
                for probe_url in _iter_manifest_probe_urls(manifest_url):
                    try:
                        resp = requests.get(
                            probe_url,
                            headers=headers,
                            timeout=HTTP_TIMEOUT_MANIFEST,
                        )
                        if resp.status_code == 200 and "#EXTM3U" in resp.text:
                            text = resp.text
                            manifest_probe_errors.pop(manifest_url, None)
                            break
                    except Exception:
                        pass
            if last_error and (not isinstance(text, str) or "#EXTM3U" not in text):
                utils.kodilog(
                    "Stripchat: Manifest probe exhausted fallback URLs for {}".format(
                        manifest_url[:80]
                    )
                )
            manifest_probe_cache[manifest_url] = text if isinstance(text, str) else ""
            return manifest_probe_cache[manifest_url]

        def _is_ad_or_stub_manifest(manifest_text):
            if not isinstance(manifest_text, str) or "#EXTM3U" not in manifest_text:
                return False
            lower = manifest_text.lower()
            if "#ext-x-mouflon-advert" in lower:
                return True
            if "/cpa/v2/" in lower:
                return True
            # Treat short VOD endlists as non-live/ad stubs for cam playback.
            if "#ext-x-playlist-type:vod" in lower and "#ext-x-endlist" in lower:
                return True
            return False

        def _candidate_is_ad_path(candidate_url):
            master_text = _fetch_manifest_text(candidate_url)
            if not master_text or "#EXTM3U" not in master_text:
                return False

            # If this manifest itself is an ad/stub, reject immediately.
            if _is_ad_or_stub_manifest(master_text):
                return True

            # If this is a master playlist, inspect child playlists as well.
            child_urls = [
                line.strip()
                for line in master_text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            for child_url in child_urls[:2]:
                child_text = _fetch_manifest_text(child_url)
                if _is_ad_or_stub_manifest(child_text):
                    return True
            return False

        def _derive_signed_media_candidate(master_url, source_label=""):
            master_text = _fetch_manifest_text(master_url)
            if not master_text or "#EXTM3U" not in master_text:
                return None, None

            mouflon = re.search(r"#EXT-X-MOUFLON:PSCH:(v\d+):([^\r\n]+)", master_text)
            if not mouflon:
                return None, None

            psch = mouflon.group(1)
            pkey = mouflon.group(2).strip()
            if not pkey:
                return None, None

            child_urls = [
                line.strip()
                for line in master_text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            ranked_child_urls = []
            for child_url in child_urls:
                quality = 0
                quality_match = re.search(r"_(\d{3,4})p(?:_blurred)?\.m3u8($|\?)", child_url)
                if quality_match:
                    try:
                        quality = int(quality_match.group(1))
                    except ValueError:
                        quality = 0
                ranked_child_urls.append((quality, child_url))

            ranked_child_urls.sort(key=lambda item: item[0], reverse=True)

            for _, child_url in ranked_child_urls:
                signed_child_url = _ensure_low_latency_playlist(_merge_query(
                    child_url,
                    {"psch": psch, "pkey": pkey},
                ))
                child_text = _fetch_manifest_text(signed_child_url)
                if not child_text or "#EXTM3U" not in child_text:
                    continue
                if _is_ad_or_stub_manifest(child_text):
                    continue
                media_lines = [
                    line.strip()
                    for line in child_text.splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                if any(line.startswith("../") for line in media_lines):
                    utils.kodilog(
                        "Stripchat: Rejected signed media candidate with parent-relative segments: {}".format(
                            signed_child_url[:80]
                        )
                    )
                    continue
                child_label = "media-signed"
                if source_label:
                    child_label = "media-signed-{}".format(source_label)
                utils.kodilog(
                    "Stripchat: Derived signed media candidate: {}".format(
                        signed_child_url[:80]
                    )
                )
                return child_label, signed_child_url
            return None, None

        promoted = []
        for label, candidate_url in list(candidates):
            source_url = _promote_variant_to_source_url(candidate_url)
            if source_url:
                promoted.append(("source-derived", source_url))
            auto_url = _promote_variant_to_auto_url(candidate_url)
            if auto_url:
                promoted.append(("auto-derived", auto_url))
            signed_label, signed_media_url = _derive_signed_media_candidate(
                candidate_url, label
            )
            if signed_media_url:
                promoted.append((signed_label, signed_media_url))
        candidates.extend(promoted)

        # After source promotion, derive signed child manifests again so the
        # source playlist can yield its own media child (often the best path).
        seen_candidate_urls = set(
            candidate_url
            for _, candidate_url in candidates
            if isinstance(candidate_url, str) and candidate_url
        )
        signed_followups = []
        for label, candidate_url in list(candidates):
            signed_label, signed_media_url = _derive_signed_media_candidate(
                candidate_url, label
            )
            if (
                signed_media_url
                and signed_media_url not in seen_candidate_urls
            ):
                signed_followups.append((signed_label, signed_media_url))
                seen_candidate_urls.add(signed_media_url)
        candidates.extend(signed_followups)

        if not candidates:
            utils.kodilog("Stripchat: No stream candidates found")
            return None, is_online_flag

        def quality_score(label, stream_url):
            if not label:
                label = ""
            score = 0
            label = label.lower()
            quality_value = 0
            match = re.search(r"(\d{3,4})p", label)
            if match:
                try:
                    quality_value = int(match.group(1))
                except ValueError:
                    quality_value = 0

            url_quality_value = 0
            if isinstance(stream_url, str):
                url_quality = re.search(r"_(\d{3,4})p(?:_blurred)?\.m3u8($|\?)", stream_url)
                if url_quality:
                    try:
                        url_quality_value = int(url_quality.group(1))
                    except ValueError:
                        url_quality_value = 0

            best_quality = max(quality_value, url_quality_value)
            if label == "media-signed":
                # Generic signed source manifests are less reliable than
                # explicit quality-specific media manifests for Stripchat LL-HLS.
                score = 8000 + best_quality
            elif "media-signed-auto" in label:
                score = 13000 + best_quality
            elif "media-signed" in label:
                # Signed media manifests are strongly preferred over master playlists
                # when the proxy is involved, as they have correct MOUFLON hashes.
                score = 12000 + best_quality
            elif "auto" in label:
                score = max(score, 11000 + best_quality)
            elif "source" in label:
                score = max(score, 10000 + best_quality)
            else:
                score = max(score, best_quality)

            # Fallback: infer quality from URL pattern when labels are generic.
            if isinstance(stream_url, str):
                is_generic_media_manifest = bool(
                    re.search(r"/\d+\.m3u8($|\?)", stream_url)
                ) and not bool(
                    re.search(r"/\d+_\d{3,4}p(?:_blurred)?\.m3u8($|\?)", stream_url)
                )
                if re.search(r"/\d+\.m3u8($|\?)", stream_url) and not re.search(
                    r"/\d+_\d{3,4}p\.m3u8($|\?)", stream_url
                ):
                    score = max(score, 7000 if "media-signed" in label else 9000)
                if re.search(r"/master/\d+\.m3u8($|\?)", stream_url):
                    score = max(score, 9000 + best_quality)
                if is_generic_media_manifest and "source-derived" in label:
                    score = min(score, 6500)
            return score

        evaluated = []
        for label, candidate_url in candidates:
            ad_path = _candidate_is_ad_path(candidate_url)
            reachable = manifest_probe_errors.get(candidate_url) != "dns"
            evaluated.append(
                {
                    "label": label,
                    "url": candidate_url,
                    "reachable": reachable,
                    "ad": ad_path,
                    "score": quality_score(label, candidate_url),
                }
            )

        # saawsedge frequently fails DNS in some networks; if we discovered any
        # non-saaws candidate, avoid selecting saaws URLs.
        has_non_saaws = any("saawsedge.com" not in c["url"] for c in evaluated)
        if has_non_saaws:
            filtered = [c for c in evaluated if "saawsedge.com" not in c["url"]]
            if filtered:
                utils.kodilog(
                    "Stripchat: Excluding saawsedge candidates in favor of reachable mirrored CDN"
                )
                evaluated = filtered

        preferred_reachable = [c for c in evaluated if c["reachable"] and not c["ad"]]
        preferred_unreachable = [
            c for c in evaluated if (not c["reachable"]) and (not c["ad"])
        ]
        ad_reachable = [c for c in evaluated if c["reachable"] and c["ad"]]
        if preferred_reachable:
            preferred = preferred_reachable
        elif ad_reachable:
            utils.kodilog(
                "Stripchat: Non-ad streams unresolved and reachable streams are ad-only; skipping playback"
            )
            return None, is_online_flag
        elif preferred_unreachable:
            utils.kodilog(
                "Stripchat: Only unresolved non-ad streams available; trying unresolved fallback"
            )
            preferred = preferred_unreachable
        else:
            utils.kodilog(
                "Stripchat: Only ad stream candidates available; skipping playback"
            )
            return None, is_online_flag

        preferred.sort(
            key=lambda c: (c["score"], 1 if "doppiocdn.com" in c["url"] else 0),
            reverse=True,
        )
        selected_url = _ensure_low_latency_playlist(preferred[0]["url"])
        selected_label = preferred[0]["label"]
        utils.kodilog(
            "Stripchat: Selected stream: {} - {}".format(
                selected_label, selected_url[:80]
            )
        )

        # Don't try to parse master playlists - just use the selected URL directly
        # The master playlist URL is already the correct stream to use
        # Parsing it and selecting variants often picks the wrong quality or causes auth failures
        utils.kodilog(
            "Stripchat: Using selected stream URL directly without master playlist parsing"
        )

        return selected_url, is_online_flag

    # Load current model details
    utils.kodilog("Stripchat: Loading details for model: {}".format(name))
    model_data = _load_model_details(name)

    if not model_data:
        vp.progress.close()
        utils.kodilog("Stripchat: Failed to load model details")
        utils.notify("Stripchat", "Model not found or offline")
        return

    _prime_stream_session(url, name)

    # Pick best stream URL
    stream_url, is_online_flag = _pick_stream(model_data, url)
    if not stream_url:
        vp.progress.close()
        utils.kodilog("Stripchat: No stream URL available")
        if is_online_flag is False:
            utils.notify("Stripchat", "Model is offline")
        else:
            utils.notify("Stripchat", "Unable to locate stream URL")
        return

    # Validate stream URL
    if not stream_url.startswith("http"):
        vp.progress.close()
        utils.kodilog("Stripchat: Invalid stream URL: {}".format(stream_url))
        utils.notify("Stripchat", "Invalid stream URL")
        return

    utils.kodilog("Stripchat: Final stream URL: {}".format(stream_url[:100]))
    vp.progress.update(85, "[CR]Found Stream[CR]")

    # Verify inputstream.adaptive is available for HLS streams
    # The check_inputstream() call will offer to install if missing
    try:
        from inputstreamhelper import Helper

        is_helper = Helper("hls")
        vp.progress.update(90, "[CR]Checking inputstream.adaptive[CR]")
        if not is_helper.check_inputstream():
            vp.progress.close()
            utils.kodilog(
                "Stripchat: inputstream.adaptive check failed - HLS streams require it"
            )
            utils.notify(
                "Stripchat",
                "inputstream.adaptive is required. Please install it from Kodi settings.",
                duration=8000,
            )
            return
    except Exception as e:
        utils.kodilog("Stripchat: Error checking inputstream: {}".format(str(e)))
        # Continue anyway - let utils.playvid handle it

    # Build headers for HLS stream
    stream_headers = _stripchat_stream_headers(name)
    ua = urllib_parse.quote(stream_headers["User-Agent"], safe="")
    origin_enc = urllib_parse.quote("https://stripchat.com", safe="")
    referer_enc = urllib_parse.quote(stream_headers["Referer"], safe="")
    accept_enc = urllib_parse.quote(stream_headers["Accept"], safe="")
    accept_lang = urllib_parse.quote(stream_headers["Accept-Language"], safe="")
    ia_headers = (
        "User-Agent={0}&Origin={1}&Referer={2}&Accept={3}&Accept-Language={4}".format(
            ua, origin_enc, referer_enc, accept_enc, accept_lang
        )
    )

    utils.kodilog("Stripchat: Starting playback")
    proxy_url = None
    needs_proxy = _should_use_manifest_proxy(stream_url)
    if utils.addon.getSetting("stripchat_proxy") != "false" and needs_proxy:
        utils.kodilog(
            "Stripchat: Attempting manifest proxy for {}".format(stream_url[:120])
        )
        proxy_url = _start_manifest_proxy(stream_url, name)

    if needs_proxy:
        if proxy_url:
            utils.kodilog("Stripchat: Using manifest proxy: {}".format(proxy_url))
            vp.play_from_direct_link(proxy_url)
            return

        vp.progress.close()
        if utils.addon.getSetting("stripchat_proxy") == "false":
            utils.kodilog(
                "Stripchat: Manifest proxy required but disabled in settings; refusing raw playback"
            )
            utils.notify(
                "Stripchat",
                "Proxy is disabled. Raw playback would hit 404 placeholder segments.",
                duration=7000,
            )
        else:
            utils.kodilog(
                "Stripchat: Manifest proxy failed; refusing raw playback because Stripchat placeholders 404"
            )
            utils.notify(
                "Stripchat",
                "Proxy setup failed. Raw playback would hit 404 placeholder segments.",
                duration=7000,
            )
        return

    if ia_headers:
        # If no proxy, we play with headers
        # Append manifest_headers=1 so ISA uses the provided headers for sub-manifests/segments
        full_url = stream_url + "|" + ia_headers + "&manifest_headers=1"
        vp.play_from_direct_link(full_url)
    else:
        vp.play_from_direct_link(stream_url)


@site.register()
def List2(url):
    if STRIPCHAT_DISABLED:
        _notify_stripchat_disabled()
        utils.eod()
        return
    site.add_download_link(
        "[COLOR red][B]Refresh[/B][/COLOR]",
        url,
        "utils.refresh",
        "",
        "",
        noDownload=True,
    )
    if utils.addon.getSetting("online_only") == "true":
        url = url + "/?online_only=1"
        site.add_download_link(
            "[COLOR red][B]Show all models[/B][/COLOR]",
            url,
            "online",
            "",
            "",
            noDownload=True,
        )
    else:
        site.add_download_link(
            "[COLOR red][B]Show only models online[/B][/COLOR]",
            url,
            "online",
            "",
            "",
            noDownload=True,
        )

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = utils._getHtml(url, site.url, headers=headers)

    # BeautifulSoup migration
    soup = utils.parse_html(data)
    if not soup:
        utils.eod()
        return

    # Check for window.LOADABLE_DATA first (modern client-side rendering)
    scripts = soup.find_all("script")
    found_models = False
    for script in scripts:
        script_text = script.string or ""
        if "window.LOADABLE_DATA" in script_text:
            try:
                # Extract JSON from window.LOADABLE_DATA = {...};
                json_match = re.search(
                    r"window\.LOADABLE_DATA\s*=\s*({.*?});", script_text
                )
                if json_match:
                    payload = json.loads(json_match.group(1))
                    model_list = []

                    # Dig through the nested structure
                    # It's usually in payload['categoryTagPage']['models'] or payload['models']
                    if "models" in payload:
                        model_list = payload["models"]
                    elif (
                        "categoryTagPage" in payload
                        and "models" in payload["categoryTagPage"]
                    ):
                        model_list = payload["categoryTagPage"]["models"]

                    if model_list:
                        found_models = True
                        for model in model_list:
                            raw_name = model.get("username")
                            if not raw_name:
                                continue
                            name = utils.cleanhtml(raw_name)
                            videourl = model.get("hlsPlaylist") or ""
                            img = _model_screenshot(model)
                            # Handle offline/profile links
                            if model.get("status") == "off":
                                name = "[COLOR hotpink][Offline][/COLOR] " + name
                                videourl = "  "

                            site.add_download_link(
                                name,
                                videourl,
                                "Playvid",
                                img,
                                "",
                                fanart=img,
                            )
                        break
            except Exception as e:
                utils.kodilog(
                    "Stripchat List2: Error parsing LOADABLE_DATA: {}".format(str(e))
                )

    if not found_models:
        # Fallback to traditional HTML parsing
        # Find the top_ranks or top_others section
        section = soup.find(class_="top_ranks") or soup.find(class_="top_others")
        if section:
            # Find all model entries with top_thumb class
            models = section.find_all(class_="top_thumb")
            for model in models:
                try:
                    link = model.find("a", href=True)
                    if not link:
                        continue
                    model_url = utils.safe_get_attr(link, "href", default="")

                    img_tag = model.find("img")
                    img = utils.safe_get_attr(img_tag, "src", ["data-src"], "")
                    if img and not img.startswith("http"):
                        img = "https:" + img

                    name_tag = model.find(class_="mn_lc")
                    name = utils.safe_get_text(name_tag, default="Unknown")

                    if "profile" in model_url:
                        name = "[COLOR hotpink][Offline][/COLOR] " + name
                        model_url = "  "
                    elif model_url.startswith("/"):
                        model_url = model_url[1:]

                    site.add_download_link(
                        name,
                        model_url,
                        "Playvid",
                        img,
                        "",
                        fanart=img,
                    )
                except Exception as e:
                    utils.kodilog(
                        "Stripchat List2: Error parsing model entry: {}".format(str(e))
                    )
                    continue

    utils.eod()


@site.register()
def List3(url):
    if STRIPCHAT_DISABLED:
        _notify_stripchat_disabled()
        utils.eod()
        return
    site.add_download_link(
        "[COLOR red][B]Refresh[/B][/COLOR]",
        url,
        "utils.refresh",
        "",
        "",
        noDownload=True,
    )
    if utils.addon.getSetting("online_only") == "true":
        url = url + "/?online_only=1"
        site.add_download_link(
            "[COLOR red][B]Show all models[/B][/COLOR]",
            url,
            "online",
            "",
            "",
            noDownload=True,
        )
    else:
        site.add_download_link(
            "[COLOR red][B]Show only models online[/B][/COLOR]",
            url,
            "online",
            "",
            "",
            noDownload=True,
        )

    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)

    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = utils._getHtml(url, site.url, headers=headers)

    # BeautifulSoup migration
    soup = utils.parse_html(data)
    if not soup:
        utils.eod()
        return

    # Check for window.LOADABLE_DATA first (modern client-side rendering)
    scripts = soup.find_all("script")
    found_models = False
    for script in scripts:
        script_text = script.string or ""
        if "window.LOADABLE_DATA" in script_text:
            try:
                # Extract JSON from window.LOADABLE_DATA = {...};
                json_match = re.search(
                    r"window\.LOADABLE_DATA\s*=\s*({.*?});", script_text
                )
                if json_match:
                    payload = json.loads(json_match.group(1))
                    model_list = []

                    if "models" in payload:
                        model_list = payload["models"]
                    elif (
                        "categoryTagPage" in payload
                        and "models" in payload["categoryTagPage"]
                    ):
                        model_list = payload["categoryTagPage"]["models"]

                    if model_list:
                        found_models = True
                        for model in model_list:
                            raw_name = model.get("username")
                            if not raw_name:
                                continue
                            name = utils.cleanhtml(raw_name)
                            videourl = model.get("hlsPlaylist") or ""
                            img = _model_screenshot(model)
                            # Handle offline/profile links
                            if model.get("status") == "off":
                                name = "[COLOR hotpink][Offline][/COLOR] " + name
                                videourl = "  "

                            site.add_download_link(
                                name,
                                videourl,
                                "Playvid",
                                img,
                                "",
                                fanart=img,
                            )
                        break
            except Exception as e:
                utils.kodilog(
                    "Stripchat List3: Error parsing LOADABLE_DATA: {}".format(str(e))
                )

    if not found_models:
        # Fallback to traditional HTML parsing
        # Find the top_ranks section
        section = soup.find(class_="top_ranks")
        if section:
            # Find all model entries with top_thumb class
            models = section.find_all(class_="top_thumb")
            for model in models:
                try:
                    link = model.find("a", href=True)
                    if not link:
                        continue
                    model_url = utils.safe_get_attr(link, "href", default="")

                    img_tag = model.find("img")
                    img = utils.safe_get_attr(img_tag, "src", ["data-src"], "")
                    if img and not img.startswith("http"):
                        img = "https:" + img

                    name_tag = model.find(class_="mn_lc")
                    name = utils.safe_get_text(name_tag, default="Unknown")

                    if "profile" in model_url:
                        name = "[COLOR hotpink][Offline][/COLOR] " + name
                        model_url = "  "
                    elif model_url.startswith("/"):
                        model_url = model_url[1:]

                    site.add_download_link(
                        name,
                        model_url,
                        "Playvid",
                        img,
                        "",
                        fanart=img,
                    )
                except Exception as e:
                    utils.kodilog(
                        "Stripchat List3: Error parsing model entry: {}".format(str(e))
                    )
                    continue

    utils.eod()


@site.register()
def online(url):
    if STRIPCHAT_DISABLED:
        _notify_stripchat_disabled()
        return
    if utils.addon.getSetting("online_only") == "true":
        utils.addon.setSetting("online_only", "false")
    else:
        utils.addon.setSetting("online_only", "true")
    utils.refresh()


if STRIPCHAT_DISABLED:
    site.default_mode = ""

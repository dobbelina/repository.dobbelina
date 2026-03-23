"""
Cumination
Copyright (C) 2026 Team Cumination

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from __future__ import annotations

import base64
import re
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "javseen",
    "[COLOR hotpink]JAVSeen[/COLOR]",
    "https://javseen.tv/",
    "cum-sites.png",
)


def _absolute_url(url):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urllib_parse.urljoin(site.url, url)


def _extract_next_page(soup):
    next_link = soup.select_one('link[rel="next"]')
    if next_link:
        href = utils.safe_get_attr(next_link, "href")
        if href:
            return _absolute_url(href)

    for link in soup.select(".pagination a[href]"):
        href = utils.safe_get_attr(link, "href")
        if href and href != "#" and "next" in utils.safe_get_text(link).lower():
            return _absolute_url(href)
    return ""


def _extract_direct_stream(html):
    if not html:
        return ""

    # Look for urlPlay variable or similar (common in turbovid, etc.)
    match = re.search(r"var\s+urlPlay\s*=\s*['\"]([^'\"]+\.(?:mp4|m3u8)[^'\"]*)['\"]", html, re.IGNORECASE)
    if match:
        return match.group(1).replace("\\/", "/")

    match = re.search(r"(https?://[^\"'<>\s]+\.(?:mp4|m3u8)[^\"'<>\s]*)", html, re.IGNORECASE)
    if match:
        return match.group(1).replace("\\/", "/")

    sources = re.findall(
        r'file\s*[:=]\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']',
        html,
        re.IGNORECASE,
    )
    if sources:
        return sources[0].replace("\\/", "/")

    return ""


def _extract_mirrors(html):
    if not html:
        return []

    mirrors = re.findall(r"playEmbed\('([^']+)'\)", html)
    
    encoded = re.findall(r'data-embed="([^"]+)"', html)
    for item in encoded:
        try:
            decoded = base64.b64decode(item).decode("utf-8")
            if decoded.startswith("http"):
                mirrors.append(decoded)
        except Exception:
            pass
            
    # Also look for common iframe embeds
    iframe_mirrors = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.IGNORECASE)
    for mirror in iframe_mirrors:
        if any(x in mirror for x in ("streamtape", "turbovid", "streamwish", "dood", "cloudwish", "mycloudz", "javseen_play")):
            mirrors.append(_absolute_url(mirror))
            
    return list(set(mirrors))


def _build_resolver_source(vp, mirror):
    match = re.search(r"https?://[^/]+/[etv]/([0-9A-Za-z]+)", mirror)
    if match:
        media_id = match.group(1)
        if any(x in mirror for x in ("cloudwish.", "streamwish.")):
            return vp.resolveurl.HostedMediaFile(
                host="streamwish.com",
                media_id="{}$${}".format(media_id, site.url),
                title="StreamWish",
            )
        if "streamtape." in mirror:
            return vp.resolveurl.HostedMediaFile(
                host="streamtape.net",
                media_id=media_id,
                title="StreamTape",
            )
        if any(host in mirror for host in ("doooood.", "dooood.", "dood.")):
            return vp.resolveurl.HostedMediaFile(
                host="doooood.com",
                media_id=media_id,
                title="DoodStream",
            )
        if "turbovid." in mirror or "turboviplay." in mirror:
            return vp.resolveurl.HostedMediaFile(
                host="turbovid.eu",
                media_id=media_id,
                title="TurboVid",
            )
        if any(x in mirror for x in ("mycloudz.", "vidhide.")):
            return vp.resolveurl.HostedMediaFile(
                host="vidhide.com",
                media_id=media_id,
                title="MyCloudz",
            )

    return None


def _order_mirrors(mirrors):
    preferred_hosts = (
        "streamtape",
        "turbovid",
        "streamwish",
        "dood",
        "cloudwish",
        "mycloudz",
    )
    seen = set()
    ordered = []
    for host in preferred_hosts:
        for mirror in mirrors:
            if mirror in seen:
                continue
            if host in mirror:
                seen.add(mirror)
                ordered.append(mirror)
    for mirror in mirrors:
        if mirror not in seen:
            seen.add(mirror)
            ordered.append(mirror)
    return ordered


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Recent[/COLOR]", site.url + "recent/", "List", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/video/?s=",
        "Search",
        site.img_search,
    )
    List(site.url + "recent/")


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    for item in soup.select(".video"):
        link = item.select_one("a.thumbnail[href]")
        if not link:
            continue

        video_url = _absolute_url(utils.safe_get_attr(link, "href"))
        title = utils.cleantext(
            utils.safe_get_attr(link, "title", default="")
            or utils.safe_get_text(item.select_one(".video-title"))
        )
        thumb = utils.get_thumbnail(item.select_one("img"))
        duration = utils.safe_get_text(item.select_one(".video-overlay.badge.transparent"))
        duration_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", duration)
        duration = duration_match.group(1) if duration_match else ""

        if title and video_url:
            site.add_download_link(title, video_url, "Playvid", thumb, title, duration=duration)

    next_url = _extract_next_page(soup)
    if next_url:
        site.add_dir("Next Page", next_url, "List", site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
        return
    List(url + urllib_parse.quote_plus(keyword))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    html = utils.getHtml(url, site.url)
    if not html:
        vp.play_from_link_to_resolve(url)
        return

    # Try mirrors embedded directly on the main page (data-embed base64 buttons)
    main_mirrors = _extract_mirrors(html)

    # Determine embed URL fallback
    embed_match = re.search(r'<iframe[^>]+src="([^"]+/embed/\d+/?)"', html, re.IGNORECASE)
    if not embed_match:
        video_id_match = re.search(r'javseen\.tv/(\d+)/', url)
        if video_id_match:
            embed_url = "https://javseen.tv/embed/{}/".format(video_id_match.group(1))
        else:
            embed_url = url
    else:
        embed_url = _absolute_url(embed_match.group(1))

    # Process mirrors recursively
    def process_url(current_url, referer, depth=0):
        if depth > 3:
            return False
            
        curr_html = utils.getHtml(current_url, referer)
        if not curr_html:
            return False
            
        # 1. Try direct stream
        direct = _extract_direct_stream(curr_html)
        if direct:
            vp.play_from_direct_link("{}|Referer={}".format(direct, current_url))
            return True
            
        # 2. Extract mirrors
        mirrors = _extract_mirrors(curr_html)
        ordered = _order_mirrors(mirrors)
        
        # 3. Try each mirror
        resolver_sources = []
        for mirror in ordered:
            # If it's another javseen internal page, follow it
            if any(x in mirror for x in ("javseen_play", "/embed/")):
                if process_url(mirror, current_url, depth + 1):
                    return True
            
            # Check for direct link on mirror (like turbovid.vip)
            # We fetch HTML for mirrors that are not internal
            m_html = utils.getHtml(mirror, current_url)
            if m_html:
                m_direct = _extract_direct_stream(m_html)
                if m_direct:
                    vp.play_from_direct_link("{}|Referer={}".format(m_direct, mirror))
                    return True
            
            # Try to build a resolver source
            source = _build_resolver_source(vp, mirror)
            if source:
                resolver_sources.append(source)
            elif any(host in mirror for host in ("streamtape", "turbovid", "streamwish", "dood", "mycloudz", "vidhide")):
                # Fallback: if we don't have a specific HostedMediaFile but it looks resolvable
                vp.play_from_link_to_resolve(mirror)
                return True
                
        if resolver_sources:
            vp._select_source(resolver_sources)
            return True
            
        return False

    # Try mirrors from main page first (saves HTTP round-trips through embed chain)
    if main_mirrors:
        ordered_main = _order_mirrors(main_mirrors)
        resolver_sources = []
        for mirror in ordered_main:
            m_html = utils.getHtml(mirror, url)
            if m_html:
                m_direct = _extract_direct_stream(m_html)
                if m_direct:
                    vp.play_from_direct_link("{}|Referer={}".format(m_direct, mirror))
                    return
            source = _build_resolver_source(vp, mirror)
            if source:
                resolver_sources.append(source)
            elif any(host in mirror for host in ("streamtape", "turbovid", "streamwish", "dood", "mycloudz", "vidhide")):
                vp.play_from_link_to_resolve(mirror)
                return
        if resolver_sources:
            vp._select_source(resolver_sources)
            return

    if process_url(embed_url, url):
        return

    # Ultimate fallback
    vp.play_from_link_to_resolve(url)

# -*- coding: utf-8 -*-
import hashlib
import html as html_module
import json
import os
import re
import sys
import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

site = AdultSite('archivebate', '[COLOR hotpink]Archivebate[/COLOR]', 'https://archivebate.com/', 'https://archivebate.com/logo/logo.png', 'archivebate')


class ArchivebateScraper:
    def __init__(self):
        self.base_url = "https://archivebate.com"
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        self.session = requests.Session() if HAS_REQUESTS else None
        self.platform_links = [
            ("YouTube", "https://archivebate.com/platform/eW91dHViZQ=="),
            ("Twitch", "https://archivebate.com/platform/dHdpdGNo"),
            ("OnlyFans", "https://archivebate.com/platform/b25seWZhbnM="),
            ("Instagram", "https://archivebate.com/platform/aW5zdGFncmFt"),
            ("TikTok", "https://archivebate.com/platform/dGlrdG9r"),
            ("BongaCams", "https://archivebate.com/platform/Ym9uZ2FjYW1z"),
            ("Cam4", "https://archivebate.com/platform/Y2FtNA=="),
            ("CamSoda", "https://archivebate.com/platform/Y2Ftc29kYQ=="),
            ("Chaturbate", "https://archivebate.com/platform/Y2hhdHVyYmF0ZQ=="),
            ("Stripchat", "https://archivebate.com/platform/c3RyaXBjaGF0"),
        ]
        self.gender_links = [
            ("All", ""),
            ("Female", "https://archivebate.com/gender/ZmVtYWxl"),
            ("Couple", "https://archivebate.com/gender/Y291cGxl"),
            ("Male", "https://archivebate.com/gender/bWFsZQ=="),
            ("Trans", "https://archivebate.com/gender/dHJhbnM="),
        ]

    def _headers(self, referer=None):
        return {
            "User-Agent": self.ua,
            "Referer": referer or (self.base_url + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _make_request(self, url, referer=None):
        if not HAS_REQUESTS:
            utils.kodilog("ERROR: requests module not available")
            return None
        if self.session is None:
            utils.kodilog("ERROR: session is None")
            return None
        try:
            response = self.session.get(url, headers=self._headers(referer), timeout=20)
            if response.status_code == 200:
                return response.text
            utils.kodilog("HTTP Error: " + str(response.status_code))
        except Exception as e:
            utils.kodilog("Request error: " + str(e))
        return None

    def _extract_livewire_component(self, page_html, component_name):
        matches = re.findall(r'wire:initial-data="([^"]+)"', page_html, re.IGNORECASE)
        for raw in matches:
            try:
                data = json.loads(html_module.unescape(raw))
                fingerprint = data.get("fingerprint") or {}
                if fingerprint.get("name") == component_name:
                    return data
            except:
                continue
        return None

    def _get_listing_target(self, url):
        parsed = urllib_parse.urlparse(url or "")
        path = parsed.path or "/"
        if "/profile/" in path:
            return "profile.model-videos", "load_profile_videos"
        if "/platform/" in path or "/gender/" in path:
            return "filter.platform", "load_platform_videos"
        return "home-videos", "loadVideos"

    def fetch_listing(self, url):
        if not HAS_REQUESTS or self.session is None:
            utils.kodilog("ERROR: requests not available")
            return "", None

        page_html = self._make_request(url)
        if not page_html:
            return "", None

        component_name, method_name = self._get_listing_target(url)
        utils.kodilog("Using component: " + component_name + ", method: " + method_name)

        component = self._extract_livewire_component(page_html, component_name)
        if not component:
            if component_name != "home-videos":
                component = self._extract_livewire_component(page_html, "home-videos")
                if component:
                    component_name = "home-videos"
                    method_name = "loadVideos"

            if not component:
                utils.kodilog("No Livewire component found")
                return "", None

        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]*)"', page_html, re.IGNORECASE)
        csrf_token = csrf_match.group(1) if csrf_match else ""

        endpoint = "{}/livewire/message/{}".format(self.base_url, component_name)
        payload = {
            "fingerprint": component.get("fingerprint", {}),
            "serverMemo": component.get("serverMemo", {}),
            "updates": [{
                "type": "callMethod",
                "payload": {
                    "id": component.get("fingerprint", {}).get("id", ""),
                    "method": method_name,
                    "params": [],
                },
            }]
        }

        response = None
        try:
            response = self.session.post(
                endpoint,
                headers={
                    "User-Agent": self.ua,
                    "Referer": url,
                    "Accept": "application/json, text/plain, */*",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRF-TOKEN": csrf_token,
                    "X-Livewire": "true",
                },
                json=payload,
                timeout=30,
            )
            if response.status_code != 200:
                utils.kodilog("Livewire HTTP error: " + str(response.status_code))
                return "", None
            data = response.json()
        except Exception as e:
            utils.kodilog("Livewire error: " + str(e))
            return "", None

        effects = data.get("effects") or {}
        listing_html = effects.get("html") or ""

        if not listing_html and "html" in data:
            listing_html = data["html"]

        next_url = None
        next_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*rel="next"', listing_html, re.IGNORECASE)
        if not next_match:
            next_match = re.search(r'<a[^>]+class="[^"]*page-link[^"]*"[^>]+href="([^"]+)"', listing_html, re.IGNORECASE)
        if next_match:
            next_url = next_match.group(1)
            if not next_url.startswith("http"):
                next_url = self.base_url + next_url

        return listing_html, next_url

    def _parse_date(self, date_text):
        """Parse various date formats and return formatted date string"""
        if not date_text:
            return ""

        date_text = date_text.strip().lower()

        # Patterns courants
        patterns = [
            # "2 days ago", "3 hours ago", "1 week ago"
            (r'(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago', lambda m: m.group(0)),
            # "2024-01-15", "15/01/2024"
            (r'(\d{4}-\d{2}-\d{2})', lambda m: m.group(1)),
            (r'(\d{2}/\d{2}/\d{4})', lambda m: m.group(1)),
            # "Jan 15, 2024", "15 Jan 2024"
            (r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})', lambda m: m.group(1)),
            (r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})', lambda m: m.group(1)),
            # "Today", "Yesterday"
            (r'\b(today|yesterday)\b', lambda m: m.group(1).capitalize()),
        ]

        for pattern, formatter in patterns:
            match = re.search(pattern, date_text, re.IGNORECASE)
            if match:
                return formatter(match)

        return date_text

    def extract_videos(self, listing_html):
        videos = []
        seen = set()

        blocks = re.findall(r'(<section class="video_item">[\s\S]*?<\/section>)', listing_html, re.IGNORECASE)
        utils.kodilog("Found " + str(len(blocks)) + " video blocks")

        for block in blocks:
            watch_match = re.search(r'<a href="(https://archivebate\.com/watch/\d+)"', block, re.IGNORECASE)
            if not watch_match:
                watch_match = re.search(r'href="(/watch/\d+)"', block, re.IGNORECASE)

            profile_match = re.search(r'<a href="(https://archivebate\.com/profile/[^"]+)">([^<]+)<\/a>', block, re.IGNORECASE)
            if not profile_match:
                profile_match = re.search(r'href="(/profile/[^"]+)">([^<]+)<', block, re.IGNORECASE)

            thumb_match = re.search(r'poster="([^"]+)"', block, re.IGNORECASE)
            if not thumb_match:
                thumb_match = re.search(r'src="([^"]+\.(?:jpg|jpeg|png|webp))[^"]*"', block, re.IGNORECASE)

            duration = ""
            duration_match = re.search(r'<span[^>]*>(\d+:\d+(?::\d+)?)</span>', block, re.IGNORECASE)
            if duration_match:
                duration = duration_match.group(1)
            else:
                dur_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?)', block)
                if dur_match:
                    duration = dur_match.group(1)

            # NOUVEAU: Extraction de la date
            date_uploaded = ""

            # Essayer différents sélecteurs pour la date
            # Pattern 1: attribut datetime
            date_match = re.search(r'<time[^>]+datetime="([^"]+)"[^>]*>([^<]*)</time>', block, re.IGNORECASE)
            if date_match:
                date_uploaded = self._parse_date(date_match.group(2) or date_match.group(1))
            else:
                # Pattern 2: class contenant "date"
                date_match = re.search(r'<span[^>]+class="[^"]*date[^"]*"[^>]*>([^<]+)</span>', block, re.IGNORECASE)
                if date_match:
                    date_uploaded = self._parse_date(date_match.group(1))
                else:
                    # Pattern 3: texte après le username/platform (souvent dans le même <p>)
                    meta_match = re.search(r'<p[^>]*>([^<]+(?:&middot;|·)[^<]+(?:&middot;|·)[^<]+)<\/p>', block, re.IGNORECASE)
                    if meta_match:
                        meta_text = html_module.unescape(meta_match.group(1))
                        parts = [p.strip() for p in re.split(r'&middot;|·|\|', meta_text) if p.strip()]
                        # La date est souvent la 3ème partie ou contient "ago"
                        for part in parts:
                            if any(x in part.lower() for x in ['ago', 'day', 'hour', 'week', 'month', '202', '/']):
                                date_uploaded = self._parse_date(part)
                                break
                    else:
                        # Pattern 4: chercher "ago" n'importe où dans le bloc
                        ago_match = re.search(r'(\d+\s+(?:minute|hour|day|week|month|year)s?\s+ago)', block, re.IGNORECASE)
                        if ago_match:
                            date_uploaded = ago_match.group(1)
                        else:
                            # Pattern 5: date formatée (Jan 15, 2024)
                            date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})', block, re.IGNORECASE)
                            if date_match:
                                date_uploaded = date_match.group(1)

            platform = ""
            meta_match = re.search(r'<p[^>]*>([^<]+(?:&middot;|·)[^<]+)<\/p>', block, re.IGNORECASE)
            if meta_match:
                meta_text = html_module.unescape(meta_match.group(1))
                parts = [p.strip() for p in re.split(r'&middot;|·|\|', meta_text) if p.strip()]
                if len(parts) >= 2:
                    platform = parts[1]

            if not watch_match or not profile_match:
                continue

            video_url = watch_match.group(1)
            if not video_url.startswith("http"):
                video_url = self.base_url + video_url

            if video_url in seen:
                continue
            seen.add(video_url)

            username = html_module.unescape(profile_match.group(2)).strip()
            thumb = thumb_match.group(1) if thumb_match else ""
            if thumb and not thumb.startswith("http"):
                thumb = self.base_url + thumb

            # Construction du titre avec date
            title_parts = [username]
            if platform:
                title_parts.append("[COLOR yellow]" + platform + "[/COLOR]")
            # NOUVEAU: Ajouter la date si disponible
            if date_uploaded:
                title_parts.append("[COLOR cyan]" + date_uploaded + "[/COLOR]")
            # if duration:
            #     title_parts.append("[COLOR lime]" + duration + "[/COLOR]")

            title = " | ".join(title_parts)

            videos.append({
                "title": title,
                "username": username,
                "platform": platform,
                "date_uploaded": date_uploaded,  # NOUVEAU: stocker la date
                "duration": duration,
                "url": video_url,
                "thumb": thumb,
            })

        return videos

    def get_platforms(self):
        return self.platform_links

    def get_genders(self):
        return [g for g in self.gender_links if g[1]]

    def resolve_video(self, url):
        html_text = self._make_request(url)
        if not html_text:
            return None

        embed_match = re.search(r'<iframe[^>]+src="(https://mixdrop\.[^"]+/[ef]/[^"]+)"', html_text, re.IGNORECASE)
        if not embed_match:
            embed_match = re.search(r'<input type="hidden" name="fid" value="(https://mixdrop\.[^"]+/f/[^"]+)"', html_text, re.IGNORECASE)
        if not embed_match:
            embed_match = re.search(r'(https://mixdrop\.[^"\']+/[ef]/[^"\']+)', html_text, re.IGNORECASE)

        if embed_match:
            return html_module.unescape(embed_match.group(1).strip())

        return None


_scraper = ArchivebateScraper()


@site.register(default_mode=True)
def Main():
    utils.kodilog("Starting Main")
    site.add_dir('[COLOR hotpink]Platforms[/COLOR]', "platforms", 'Categories', '', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', _scraper.base_url + "/api/v1/search?query=", 'Search', '', '')
    List(_scraper.base_url + "/")
    utils.eod()


@site.register()
def Categories(url):
    utils.kodilog("Categories: " + str(url))

    if url == "platforms":
        for label, target in _scraper.get_platforms():
            site.add_dir(label, target, 'List', '', '')

        for label, target in _scraper.get_genders():
            site.add_dir("Gender: " + label, target, 'List', '', '')

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        decoded_url = urllib_parse.unquote_plus(url)
        if keyword in decoded_url:
            SearchResults(decoded_url)
        else:
            search_url = decoded_url + urllib_parse.quote_plus(keyword)
            SearchResults(search_url)


@site.register()
def SearchResults(url):
    utils.kodilog("SearchResults: " + url)

    if not HAS_REQUESTS:
        utils.kodilog("ERROR: requests module not available")
        utils.notify('Error', 'Requests module not available')
        utils.eod()
        return

    if _scraper.session is None:
        utils.kodilog("ERROR: session is None")
        utils.notify('Error', 'Session not initialized')
        utils.eod()
        return

    home_html = _scraper._make_request(_scraper.base_url + "/")
    csrf_token = ""
    if home_html:
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]*)"', home_html, re.IGNORECASE)
        csrf_token = csrf_match.group(1) if csrf_match else ""

    response = None
    try:
        response = _scraper.session.get(
            url,
            headers={
                "User-Agent": _scraper.ua,
                "Referer": _scraper.base_url + "/",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRF-TOKEN": csrf_token,
            },
            timeout=20,
        )

        if response.status_code == 200:
            data = response.json()
            profiles = data.get("data", [])

            if not profiles:
                utils.notify(msg='No models found!')

                return ''

            for item in profiles:
                username = item.get("username", "").strip()
                platform = item.get("platform", "").strip()
                gender = item.get("gender", "").strip()

                if username:
                    title_parts = [username]
                    if platform:
                        title_parts.append("[COLOR yellow]" + platform + "[/COLOR]")
                    if gender:
                        title_parts.append(gender)
                    title = " | ".join(title_parts)

                    profile_url = "{}/profile/{}".format(_scraper.base_url, urllib_parse.quote(username))
                    site.add_dir(title, profile_url, 'List', '', '')

            meta = data.get("meta", {})
            current_page = int(meta.get("current_page", 1))
            last_page = int(meta.get("last_page", 1))

            if current_page < last_page:
                next_page = current_page + 1
                if 'page=' in url:
                    next_url = re.sub(r'page=\d+', 'page={}'.format(next_page), url)
                else:
                    separator = '&' if '?' in url else '?'
                    next_url = url + separator + "page={}".format(next_page)
                site.add_dir('[COLOR hotpink]Next Page >>[/COLOR]', next_url, 'SearchResults', '', '')
        else:
            if response is not None:
                utils.notify('Error', 'Search failed: ' + str(response.status_code))
            else:
                utils.notify('Error', 'Search failed: No response')

    except Exception as e:
        utils.kodilog("SearchResults error: " + str(e))
        utils.notify('Error', str(e))

    utils.eod()


@site.register()
def List(url):
    utils.kodilog("List: " + url)

    if not url.startswith("http"):
        url = _scraper.base_url + url

    listing_html, next_url = _scraper.fetch_listing(url)

    if not listing_html:
        utils.notify('Error', 'No videos found')
        utils.eod()
        return

    videos = _scraper.extract_videos(listing_html)
    utils.kodilog("Extracted " + str(len(videos)) + " videos")

    for video in videos:
        plot = "User: " + video['username']
        if video['platform']:
            plot += "\nPlatform: " + video['platform']
        # NOUVEAU: Ajouter la date dans le plot aussi
        if video.get('date_uploaded'):
            plot += "\nDate: " + video['date_uploaded']
        if video['duration']:
            plot += "\nDuration: " + video['duration']

        site.add_download_link(
            video['title'],
            video['url'],
            'Play',
            video['thumb'],
            plot,
            contextm='download',
            duration=video['duration']
        )

    if next_url:
        site.add_dir('[COLOR hotpink]Next Page >>[/COLOR]', next_url, 'List', site.img_next, '')

    utils.eod()


@site.register()
def Play(url, name, download=0):
    utils.kodilog("Play: " + url)

    embed_url = _scraper.resolve_video(url)

    if embed_url:
        utils.kodilog("Found embed: " + embed_url)
        try:
            import resolveurl
            resolved = resolveurl.resolve(embed_url)
            if resolved:
                utils.playvid(resolved, name, download)
                return
        except Exception as e:
            utils.kodilog("Resolve error: " + str(e))

    utils.notify('Error', 'Could not resolve video')
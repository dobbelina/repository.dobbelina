 # Cumination – Erome module (public only)
# Copyright (C) 2020 Whitecream (updated 2025)
#
# UPDATES / FIXES:
# - Fixed general search (removed deprecated add_search_history call).
# - Added current page / total pages display in pagination.
# - Added "Go to page" function with numeric input to jump to any page.
# - Added "Go to author page" context menu item for each album.
# - Added user search (via "Search User" menu) to view a specific user's albums.
# - Fixed age gate handling: now properly follows the confirmation link instead of
#   relying on a manually added cookie, eliminating repeated prompts.
# - Fixed urllib_quote typo (changed to urllib_parse.quote) in context menu.
# - Fixed double-encoding issue in the "Go to page" plugin URL.
# - Improved regex for confirmation link to be more flexible.
# - Added fallback /confirm endpoint if the regular link is not found.

import re
import os
import json
import traceback
import sys
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
from six.moves import urllib_parse, urllib_request, http_cookiejar
from urllib.error import HTTPError

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("erome", "[COLOR hotpink]Erome[/COLOR]", "https://www.erome.com/",
                 "https://www.erome.com/img/logo-erome-horizontal.png", "erome")

# ----------------------------------------------------------------------
# Cookie / session handling (only age gate cookie)
# ----------------------------------------------------------------------
COOKIE_DIR = xbmcvfs.translatePath(utils.addon.getAddonInfo('profile'))
if not xbmcvfs.exists(COOKIE_DIR):
    xbmcvfs.mkdirs(COOKIE_DIR)
COOKIE_FILE = os.path.join(COOKIE_DIR, 'erome_cookies.lwp')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


def log(msg, level=xbmc.LOGDEBUG):
    try:
        xbmc.log(msg, level)
    except:
        pass


def save_cookies(cj):
    """Save cookie jar to disk."""
    try:
        cj.save(COOKIE_FILE, ignore_discard=True, ignore_expires=True)
        log('Cookies saved to {}'.format(COOKIE_FILE), xbmc.LOGDEBUG)
    except Exception as e:
        log('Failed to save cookies: {}'.format(e), xbmc.LOGWARNING)


def get_session():
    cj = http_cookiejar.LWPCookieJar()
    if os.path.exists(COOKIE_FILE):
        try:
            cj.load(COOKIE_FILE, ignore_discard=True, ignore_expires=True)
            log('Loaded cookies from {}'.format(COOKIE_FILE), xbmc.LOGDEBUG)
        except Exception as e:
            log('Failed to load cookies: {}'.format(e), xbmc.LOGWARNING)

    opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(cj))
    opener.addheaders = [(k, v) for k, v in HEADERS.items()]
    return opener, cj


def fetch_url(url, opener, referer=None, dump_debug=False):
    req = urllib_request.Request(url)
    for key, value in HEADERS.items():
        req.add_header(key, value)
    if referer:
        req.add_header('Referer', referer)
    try:
        resp = opener.open(req, timeout=30)
        if resp.info().get('Content-Encoding') == 'gzip':
            import gzip
            buf = gzip.decompress(resp.read())
            html = buf.decode('utf-8', errors='ignore')
        else:
            html = resp.read().decode('utf-8', errors='ignore')
        log('fetch_url {} -> {} bytes'.format(url, len(html)))
        if dump_debug and utils.addon.getSetting('enh_debug') == 'true':
            try:
                dump_path = xbmcvfs.translatePath('special://temp/erome_debug.html')
                with open(dump_path, 'w') as f:
                    f.write(html)
                log('DEBUG: HTML dumped to {}'.format(dump_path), xbmc.LOGINFO)
            except:
                pass
        return html
    except HTTPError as e:
        if e.code == 404:
            log('fetch_url 404: {} not found'.format(url), xbmc.LOGWARNING)
            return '404'
        else:
            log('fetch_url HTTP error {}: {}'.format(e.code, e.reason), xbmc.LOGERROR)
            return ""
    except Exception as e:
        log('fetch_url error: {}'.format(e), xbmc.LOGERROR)
        return ""


def handle_age_gate(html, url, opener, cj):
    """
    Detect and bypass age gate. Returns (new_html, opener, cj).
    Always follows the confirmation link if present; never relies on manual cookie alone.
    """
    # Check if the page actually contains albums (by looking for album divs)
    has_albums = re.search(r'id="album-\d+"', html) is not None
    if has_albums:
        log('Page already contains albums, ignoring age gate', xbmc.LOGINFO)
        return html, opener, cj

    # If no albums and we don't see the age gate text, assume it's not an age gate page
    if 'I am 18 or older' not in html and 'sexually explicit material' not in html:
        return html, opener, cj

    log('*** Age confirmation page detected ***', xbmc.LOGINFO)

    # Helper to extract and follow the confirmation link
    def follow_confirm_link(html):
        # More flexible regex: case-insensitive, allow extra attributes
        confirm_link_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>I am 18 or older[^<]*</a>', html, re.IGNORECASE)
        if not confirm_link_match:
            # Try alternative phrasing
            confirm_link_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>enter</a>', html, re.IGNORECASE)
        if confirm_link_match:
            confirm_url = urllib_parse.urljoin(url, confirm_link_match.group(1))
            log('Submitting age confirmation to: {}'.format(confirm_url))
            try:
                opener.open(confirm_url)  # This should set the proper cookie
                save_cookies(cj)
                # Now fetch the original page again with the same opener (which now has the new cookie)
                new_html = fetch_url(url, opener, referer=site.url)
                if new_html and 'I am 18 or older' not in new_html:
                    log('Age confirmation successful, page reloaded')
                    return new_html
                else:
                    log('Age confirmation returned age gate again', xbmc.LOGWARNING)
            except Exception as e:
                log('Age confirmation request failed: {}'.format(e), xbmc.LOGERROR)
        return None

    # First try automatic following
    new_html = follow_confirm_link(html)
    if new_html:
        return new_html, opener, cj

    # If automatic fails, ask the user
    if xbmcgui.Dialog().yesno('Erome Age Verification',
                               'The site requires age confirmation.\n\n'
                               'Are you 18 years or older?',
                               nolabel='No', yeslabel='Yes'):
        log('User confirmed age, retrying confirmation link', xbmc.LOGINFO)
        # Try again (maybe the page structure is the same)
        new_html = follow_confirm_link(html)
        if new_html:
            return new_html, opener, cj
        else:
            # Last resort: try a known confirmation endpoint (common pattern)
            try:
                confirm_url = urllib_parse.urljoin(url, '/confirm')
                opener.open(confirm_url)
                save_cookies(cj)
                new_html = fetch_url(url, opener, referer=site.url)
                if new_html and 'I am 18 or older' not in new_html:
                    log('Age confirmation via /confirm succeeded', xbmc.LOGINFO)
                    return new_html, opener, cj
            except:
                pass
            utils.notify('Erome', 'Age confirmation failed – please try again later')
            return html, opener, cj

    utils.notify('Erome', 'Age confirmation cancelled')
    return html, opener, cj


# ----------------------------------------------------------------------
# Helper to construct thumbnail from video URL (fallback)
# ----------------------------------------------------------------------
def construct_thumb_from_video(video_url):
    pattern = r'https://v(\d+)\.erome\.com/(\d+)/([^/]+)/([^_]+)_\d+p\.mp4'
    match = re.search(pattern, video_url)
    if match:
        server = match.group(1)
        album_id = match.group(2)
        folder = match.group(3)
        base = match.group(4)
        return f'https://s{server}.erome.com/{album_id}/{folder}/thumbs/{base}.jpg'
    return None


# ----------------------------------------------------------------------
# Main menu – public only
# ----------------------------------------------------------------------
@site.register(default_mode=True)
def Main():
    try:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?o=new&q=', 'Search', site.img_search)
        site.add_dir('[COLOR orange]Search User[/COLOR]', site.url + '', 'UserSearch', site.img_search)
        List(site.url + 'explore/new')
    except Exception as e:
        log('CRASH in Main: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
        utils.notify('Erome Error', str(e))


# ----------------------------------------------------------------------
# Pagination helpers
# ----------------------------------------------------------------------
def get_pagination_info(html, current_url):
    """
    Extract pagination info from HTML.
    Returns (base_url, current_page, total_pages) or (None, None, None) if not found.
    """
    try:
        pagination = re.search(r'<ul[^>]+class="[^"]*pagination[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL | re.IGNORECASE)
        if not pagination:
            return None, None, None
        pag_html = pagination.group(1)

        active_match = re.search(r'<li[^>]+class="[^"]*active[^"]*"[^>]*>.*?<a[^>]*>(\d+)</a>', pag_html, re.DOTALL | re.IGNORECASE)
        if not active_match:
            active_match = re.search(r'<li[^>]+class="[^"]*active[^"]*"[^>]*>.*?<span[^>]*>(\d+)</span>', pag_html, re.DOTALL | re.IGNORECASE)
        current_page = int(active_match.group(1)) if active_match else 1

        page_links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(\d+)</a>', pag_html)
        page_numbers = [int(num) for _, num in page_links]
        total_pages = max(page_numbers) if page_numbers else 1

        if page_links:
            sample_href = page_links[0][0]
            if '?page=' in sample_href:
                parsed = urllib_parse.urlparse(current_url)
                new_query = re.sub(r'&?page=\d+&?', '', parsed.query).strip('&')
                base = urllib_parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
            elif '/page/' in sample_href:
                parsed = urllib_parse.urlparse(current_url)
                new_path = re.sub(r'/page/\d+', '', parsed.path)
                base = urllib_parse.urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
            else:
                base = current_url
            return base, current_page, total_pages
        return current_url, current_page, total_pages
    except Exception as e:
        log('Error in get_pagination_info: {}'.format(e), xbmc.LOGWARNING)
        return None, None, None


def _add_pagination(html, current_url):
    try:
        next_match = re.search(r'<link[^>]+rel="next"[^>]+href="([^"]+)"', html)
        if not next_match:
            next_match = re.search(r'<a[^>]+class="pagination-next"[^>]+href="([^"]+)"[^>]*>', html)
        if next_match:
            next_url = urllib_parse.urljoin(current_url, next_match.group(1).replace('&amp;', '&'))
            site.add_dir('[COLOR orange]Next Page[/COLOR]', next_url, 'List', site.img_next)

        base_url, current_page, total_pages = get_pagination_info(html, current_url)
        if base_url and current_page and total_pages:
            page_format = 'query'
            if next_match:
                nxt = next_match.group(1)
                if '/page/' in nxt:
                    page_format = 'path'
            else:
                page_links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\d+</a>', html)
                if page_links and '/page/' in page_links[0]:
                    page_format = 'path'

            # Build plugin URL for GotoPage – quote base_url to include in query string
            goto_plugin_url = '{}?mode=erome.GotoPage&base={}&current={}&total={}&format={}'.format(
                sys.argv[0],
                urllib_parse.quote(base_url, safe=''),
                current_page,
                total_pages,
                page_format
            )
            listitem = xbmcgui.ListItem('[COLOR orange]Page {} / {} - Go to page...[/COLOR]'.format(current_page, total_pages))
            listitem.setArt({'thumb': site.img_next, 'icon': site.img_next})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=goto_plugin_url, listitem=listitem, isFolder=True)
    except Exception as e:
        log('Error in pagination: {}'.format(e), xbmc.LOGWARNING)


# ----------------------------------------------------------------------
# Main listing function
# ----------------------------------------------------------------------
@site.register()
def List(url):
    try:
        log('List called with URL: {}'.format(url))
        opener, cj = get_session()
        html = fetch_url(url, opener, referer=site.url)
        if html == '404':
            utils.notify('Erome', 'Page not found')
            return
        if not html:
            utils.notify('Erome', 'Failed to load page')
            return

        html, opener, cj = handle_age_gate(html, url, opener, cj)
        if not html:
            return

        albums = []
        album_pattern = r'<div[^>]+id="album-\d+".*?>(.*?)</div>\s*</div>\s*</div>'
        album_blocks = re.findall(album_pattern, html, re.DOTALL | re.IGNORECASE)
        if not album_blocks:
            album_blocks = re.findall(r'<div[^>]+id="album-\d+".*?>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)

        for block in album_blocks:
            url_match = re.search(r'<a[^>]+class="album-link"[^>]+href="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
            if not url_match:
                continue
            album_url = urllib_parse.urljoin(site.url, url_match.group(1))

            thumb_match = re.search(r'<img[^>]+data-src="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
            if not thumb_match:
                thumb_match = re.search(r'<img[^>]+src="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
            thumb_url = thumb_match.group(1) if thumb_match else ''
            img_url = thumb_url + '|Referer={}'.format(site.url) if thumb_url else ''

            title_match = re.search(r'<a[^>]+class="album-title"[^>]*>([^<]+)</a>', block, re.DOTALL | re.IGNORECASE)
            title = utils.cleantext(title_match.group(1)) if title_match else ''

            author_match = re.search(r'<span[^>]+class="album-user"[^>]*>([^<]+)</span>', block, re.DOTALL | re.IGNORECASE)
            author = utils.cleantext(author_match.group(1)) if author_match else 'unknown'

            videos_match = re.search(r'<span[^>]+class="album-videos"[^>]*>.*?(\d+)', block, re.DOTALL | re.IGNORECASE)
            videos = videos_match.group(1) if videos_match else '0'

            images_match = re.search(r'<span[^>]+class="album-images"[^>]*>.*?(\d+)', block, re.DOTALL | re.IGNORECASE)
            images = images_match.group(1) if images_match else '0'

            display_name = '{} [by {} - [COLOR hotpink]{} videos[/COLOR], [COLOR orange]{} images[/COLOR]]'.format(title, author, videos, images)
            albums.append((album_url, img_url, display_name, author, title, videos, images))

        if not albums:
            log('No albums found on this page')
            utils.notify('Erome', 'No albums found')
            _add_pagination(html, url)
            utils.eod()
            return

        seen = set()
        for album_url, img_url, display_name, author, title, videos, images in albums:
            if album_url in seen:
                continue
            seen.add(album_url)

            listitem = xbmcgui.ListItem(label=display_name)
            if img_url:
                listitem.setArt({'thumb': img_url, 'icon': img_url, 'poster': img_url})
            listitem.setInfo('video', {
                'title': title,
                'plot': 'Author: {}\nVideos: {}\nImages: {}'.format(author, videos, images),
                'studio': author,
                'mediatype': 'set'
            })

            context_menu = []
            if author and author != 'unknown':
                author_plugin_url = 'plugin://plugin.video.cumination/?mode=erome.UserSearch&username={}&url={}'.format(
                    urllib_parse.quote(author), urllib_parse.quote(site.url))
                context_menu.append(('Go to author page', 'Container.Update({})'.format(author_plugin_url)))
            if context_menu:
                listitem.addContextMenuItems(context_menu, replaceItems=False)

            plugin_url = '{}?mode=erome.List2&url={}'.format(sys.argv[0], urllib_parse.quote('{}|section=both'.format(album_url)))
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=plugin_url, listitem=listitem, isFolder=True)

        _add_pagination(html, url)
        utils.eod()

    except Exception as e:
        log('CRASH in List: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
        utils.notify('Erome Error', str(e))


# ----------------------------------------------------------------------
# Goto page function
# ----------------------------------------------------------------------
@site.register()
def GotoPage(base=None, current=None, total=None, format='query'):
    try:
        if not base:
            return
        current = int(current) if current else 1
        total = int(total) if total else 0

        dialog = xbmcgui.Dialog()
        page_str = dialog.numeric(0, 'Enter page number (1-{})'.format(total) if total else 'Enter page number')
        if not page_str:
            return
        try:
            page = int(page_str)
        except:
            utils.notify('Erome', 'Invalid page number')
            return

        if total > 0 and (page < 1 or page > total):
            utils.notify('Erome', 'Page number out of range')
            return

        # base is already raw (decoded by Kodi)
        if format == 'query':
            if '?' in base:
                page_url = base + '&page={}'.format(page)
            else:
                page_url = base + '?page={}'.format(page)
        else:  # path
            if base.endswith('/'):
                page_url = base + 'page/{}'.format(page)
            else:
                page_url = base + '/page/{}'.format(page)

        List(page_url)
    except Exception as e:
        log('CRASH in GotoPage: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
        utils.notify('Erome Error', str(e))


# ----------------------------------------------------------------------
# Album detail listing
# ----------------------------------------------------------------------
def extract_video_from_json(html):
    patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
        r'window\.__DATA__\s*=\s*({.*?});',
        r'<script[^>]+type="application/json"[^>]*>(.*?)</script>',
        r'var\s+media\s*=\s*({.*?});'
    ]
    for pat in patterns:
        match = re.search(pat, html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                videos = []
                def find_media(obj):
                    if isinstance(obj, dict):
                        url = None
                        thumb = None
                        for k, v in obj.items():
                            if k in ('url', 'src', 'video', 'mp4', 'webm') and isinstance(v, str) and v.startswith('http'):
                                url = v
                            if k in ('thumb', 'thumbnail', 'poster') and isinstance(v, str) and v.startswith('http'):
                                thumb = v
                            elif isinstance(v, (dict, list)):
                                find_media(v)
                        if url:
                            videos.append((url, thumb))
                    elif isinstance(obj, list):
                        for item in obj:
                            find_media(item)
                find_media(data)
                return videos
            except:
                continue
    return []


@site.register()
def List2(url):
    try:
        if '|section=' in url:
            base, section = url.split('|section=')
        else:
            base = url
            section = 'both'

        opener, cj = get_session()
        html = fetch_url(base, opener, referer=site.url, dump_debug=True)
        if html == '404':
            utils.notify('Erome', 'Album not found')
            return
        if not html:
            utils.notify('Erome', 'Failed to load album')
            return

        html, opener, cj = handle_age_gate(html, base, opener, cj)
        if not html:
            return

        if section == 'both':
            has_vids = 'class="video"' in html
            has_pics = re.search(r'class="img-front', html) is not None

            if has_vids and not has_pics:
                log('Album has only videos, opening directly', xbmc.LOGDEBUG)
                List2(base + '|section=vids')
                return
            elif has_pics and not has_vids:
                log('Album has only images, opening directly', xbmc.LOGDEBUG)
                List2(base + '|section=pics')
                return
            elif has_vids and has_pics:
                if has_vids:
                    site.add_dir('[COLOR hotpink]Videos[/COLOR]', base + '|section=vids', 'List2', '')
                if has_pics:
                    site.add_dir('[COLOR orange]Photos[/COLOR]', base + '|section=pics', 'List2', '')
            else:
                utils.notify('Erome', 'No media found')
            utils.eod()
            return

        video_items = extract_video_from_json(html) if section == 'vids' else []
        if video_items:
            for i, (vid_url, thumb) in enumerate(video_items, 1):
                if not thumb:
                    thumb = construct_thumb_from_video(vid_url)
                img_url = (thumb + '|Referer={}'.format(site.url)) if thumb else ''
                vid_url_full = vid_url + '|Referer={}'.format(site.url)
                site.add_download_link('Video {}'.format(i), vid_url_full, 'Playvid', img_url)
                log('Found video from JSON {}: {}'.format(i, vid_url), xbmc.LOGDEBUG)
            utils.eod()
            return

        media_blocks = re.split(r'<div[^>]+class="media-group', html)
        if len(media_blocks) > 1:
            media_blocks.pop(0)

        item_count = 0
        for block in media_blocks:
            block = block.split('class="clearfix"')[0]

            if section == 'vids' and 'class="video"' in block:
                img_div = re.search(r'<div[^>]+class="img"[^>]+data-html="(#video\d+)"', block, re.DOTALL | re.IGNORECASE)
                if not img_div:
                    video_direct = re.search(r'<video[^>]+src="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
                    if video_direct:
                        vid_url = video_direct.group(1)
                        thumb_match = re.search(r'poster="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
                        thumb = thumb_match.group(1) if thumb_match else ''
                        if not thumb:
                            thumb = construct_thumb_from_video(vid_url)
                        duration = ''
                        dur_match = re.search(r'<span[^>]+class="duration"[^>]*>([^<]+)</span>', block, re.DOTALL | re.IGNORECASE)
                        if dur_match:
                            duration = dur_match.group(1).strip()
                        item_count += 1
                        img_url = thumb + '|Referer={}'.format(site.url) if thumb else ''
                        vid_url_full = vid_url + '|Referer={}'.format(site.url)
                        site.add_download_link('Video {}'.format(item_count), vid_url_full, 'Playvid', img_url, duration=duration)
                        log('Found direct video {}: {}'.format(item_count, vid_url), xbmc.LOGDEBUG)
                        continue
                    video_data = re.search(r'<div[^>]+data-video="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
                    if video_data:
                        vid_url = video_data.group(1)
                        thumb_match = re.search(r'data-thumb="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
                        thumb = thumb_match.group(1) if thumb_match else ''
                        if not thumb:
                            img_match = re.search(r'<img[^>]+src="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
                            if img_match:
                                thumb = img_match.group(1)
                        if not thumb:
                            thumb = construct_thumb_from_video(vid_url)
                        duration = ''
                        dur_match = re.search(r'<span[^>]+class="duration"[^>]*>([^<]+)</span>', block, re.DOTALL | re.IGNORECASE)
                        if dur_match:
                            duration = dur_match.group(1).strip()
                        item_count += 1
                        img_url = thumb + '|Referer={}'.format(site.url) if thumb else ''
                        vid_url_full = vid_url + '|Referer={}'.format(site.url)
                        site.add_download_link('Video {}'.format(item_count), vid_url_full, 'Playvid', img_url, duration=duration)
                        log('Found data-video {}: {}'.format(item_count, vid_url), xbmc.LOGDEBUG)
                        continue
                    video_link = re.search(r'<a[^>]+href="([^"]+\.(?:mp4|webm|m3u8))"', block, re.DOTALL | re.IGNORECASE)
                    if video_link:
                        vid_url = video_link.group(1)
                        thumb_match = re.search(r'<img[^>]+src="([^"]+)"', block, re.DOTALL | re.IGNORECASE)
                        thumb = thumb_match.group(1) if thumb_match else ''
                        if not thumb:
                            thumb = construct_thumb_from_video(vid_url)
                        duration = ''
                        dur_match = re.search(r'<span[^>]+class="duration"[^>]*>([^<]+)</span>', block, re.DOTALL | re.IGNORECASE)
                        if dur_match:
                            duration = dur_match.group(1).strip()
                        item_count += 1
                        img_url = thumb + '|Referer={}'.format(site.url) if thumb else ''
                        vid_url_full = vid_url + '|Referer={}'.format(site.url)
                        site.add_download_link('Video {}'.format(item_count), vid_url_full, 'Playvid', img_url, duration=duration)
                        log('Found video link {}: {}'.format(item_count, vid_url), xbmc.LOGDEBUG)
                        continue
                    else:
                        log('No video found in block with any pattern', xbmc.LOGDEBUG)
                        continue

                hidden_id = img_div.group(1)
                img_div_text = img_div.group(0)

                thumb = ''
                thumb_match = re.search(r'<img[^>]+class="[^"]*lasyload[^"]*"[^>]+data-src="([^"]+)"', img_div_text, re.DOTALL | re.IGNORECASE)
                if not thumb_match:
                    thumb_match = re.search(r'<img[^>]+src="([^"]+)"', img_div_text, re.DOTALL | re.IGNORECASE)
                if not thumb_match:
                    bg_match = re.search(r'style="[^"]*background-image:\s*url\([\'"]?([^\'")]+)[\'"]?\)', img_div_text, re.DOTALL | re.IGNORECASE)
                    if bg_match:
                        thumb = bg_match.group(1)
                else:
                    thumb = thumb_match.group(1)

                if not thumb:
                    thumb_match = re.search(r'data-thumb="([^"]+)"', img_div_text, re.DOTALL | re.IGNORECASE)
                    if thumb_match:
                        thumb = thumb_match.group(1)

                hidden_div = re.search(r'<div[^>]+id="{}"[^>]*>(.*?)</div>'.format(hidden_id[1:]), block, re.DOTALL | re.IGNORECASE)
                if not hidden_div:
                    log('Hidden div {} not found in block'.format(hidden_id), xbmc.LOGDEBUG)
                    continue
                hidden_html = hidden_div.group(1)

                source_match = re.search(r'<source[^>]+src="([^"]+)"', hidden_html, re.DOTALL | re.IGNORECASE)
                if not source_match:
                    source_match = re.search(r'<video[^>]+src="([^"]+)"', hidden_html, re.DOTALL | re.IGNORECASE)
                if not source_match:
                    log('No source found in hidden div', xbmc.LOGDEBUG)
                    continue
                vid_url = source_match.group(1)

                if not thumb:
                    thumb = construct_thumb_from_video(vid_url)

                quality_match = re.search(r'label="([^"]+)"', hidden_html, re.DOTALL | re.IGNORECASE)
                quality = quality_match.group(1) if quality_match else ''

                duration = ''
                dur_match = re.search(r'<span[^>]+class="duration"[^>]*>([^<]+)</span>', block, re.DOTALL | re.IGNORECASE)
                if dur_match:
                    duration = dur_match.group(1).strip()

                item_count += 1
                img_url = thumb + '|Referer={}'.format(site.url) if thumb else ''
                vid_url_full = vid_url + '|Referer={}'.format(site.url)
                site.add_download_link('Video {}'.format(item_count), vid_url_full, 'Playvid', img_url,
                                       duration=duration, quality=quality)
                log('Found video {}: {}'.format(item_count, vid_url), xbmc.LOGDEBUG)

            elif section == 'pics' and 'class="video"' not in block:
                img_matches = re.finditer(
                    r'<img[^>]+class="img-front[^"]*"[^>]+(?:data-)?src="([^"]+)"',
                    block, re.DOTALL
                )
                for img_match in img_matches:
                    item_count += 1
                    img_url = img_match.group(1) + '|Referer={}'.format(site.url)
                    site.add_img_link('Photo {}'.format(item_count), img_url, 'Showpic')

        if item_count == 0:
            log('No media found in section {} – HTML snippet: {}'.format(section, html[:2000].replace('\x00', '\\x00')), xbmc.LOGDEBUG)
            utils.notify('Erome', 'No media found in this section')
        utils.eod()
    except Exception as e:
        log('CRASH in List2: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
        utils.notify('Erome Error', str(e))


# ----------------------------------------------------------------------
# Search functions
# ----------------------------------------------------------------------
@site.register()
def Search(url, keyword=None):
    try:
        if not keyword:
            site.search_dir(url, 'Search')
        else:
            query = urllib_parse.quote_plus(keyword)
            search_url = site.url + 'search?q={}&o=new'.format(query)
            List(search_url)
    except Exception as e:
        log('CRASH in Search: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
        utils.notify('Erome Error', str(e))


@site.register()
def UserSearch(username=None, url=None):
    try:
        if not username:
            keyboard = utils.xbmc.Keyboard('', 'Enter Erome username')
            keyboard.doModal()
            if keyboard.isConfirmed():
                username = keyboard.getText().strip()
            else:
                return
        if username:
            user_url = urllib_parse.urljoin(site.url, username)
            opener, cj = get_session()
            html = fetch_url(user_url, opener, referer=site.url)
            if html == '404':
                utils.notify('Erome', 'User "{}" not found'.format(username))
                return
            if not html:
                utils.notify('Erome', 'Failed to load user page')
                return
            List(user_url)
    except Exception as e:
        log('CRASH in UserSearch: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
        utils.notify('Erome Error', str(e))


@site.register()
def Showpic(url, name):
    utils.showimage(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(url)

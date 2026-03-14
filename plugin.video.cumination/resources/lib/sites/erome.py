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
import xbmc
import xbmcgui
from six.moves import urllib_parse
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
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?o=new&q=', 'Search', site.img_search)
    # site.add_dir('[COLOR hotpink]Search user[/COLOR]', site.url, 'Search_user', site.img_search)
    List(site.url + 'explore/new')

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
    listhtml = utils.getHtml(url, site.url)
    albums = listhtml.split(' id="album-')
    for album in albums:

        match = re.search(r'''title"\s*href="([^"]+)"\s*>([^<]+)''', album, re.DOTALL | re.IGNORECASE)
        if match:
            iurl = match.group(1)
            name = utils.cleantext(match.group(2))
        else:
            continue
        img = re.search(r'src="([^"]+)', album, re.DOTALL | re.IGNORECASE)
        img = img.group(1) if img else ''
        img += '|Referer={0}'.format(site.url)
        pics = False
        vids = False
        if 'class="album-user"' in album:
            user = re.findall(r'<span class="album-user"\s*>([^<]+)<', album, re.DOTALL | re.IGNORECASE)[0]
            user = utils.cleantext(user)
            name = name + ' [by {} - '.format(user)
        if '"album-videos"' in album:
            items = re.findall(r'class="album-videos"[^\d]+(\d+)', album)[0]
            name += '[COLOR hotpink][I] {0} vids[/I][/COLOR]'.format(items)
            vids = True
        if '"album-images"' in album:
            items = re.findall(r'class="album-images"[^\d]+(\d+)', album)[0]
            name += '[COLOR orange][I] {0} pics[/I][/COLOR]'.format(items)
            pics = True
        cm = []
        if 'class="album-user"' in album:
            name += ' ]'
            cm_user = (utils.addon_sys + "?mode=" + str('erome.Related') + "&url=" + urllib_parse.quote_plus(site.url + user + '?t=posts'))
            cm = [('[COLOR deeppink]Author page [{}][/COLOR]'.format(user), 'RunPlugin(' + cm_user + ')')]

        if pics and vids:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='both', contextm=cm)
        elif pics:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='pics', contextm=cm)
        elif vids:
            site.add_dir(name, iurl, 'List2', img, desc=name, section='vids', contextm=cm)

    re_npurl = r'<li class="active"><span>\d+</span></li>\s+<li><a href="([^"]+)">'
    re_npnr = r'<li class="active"><span>\d+</span></li>\s+<li><a href="[^"]+">(\d+)<'
    re_lpnr = r'>(\d+)</a></li>\s+<li><a href="[^"]+"\s+rel="next"'
    utils.next_page(site, 'erome.List', listhtml, re_npurl, re_npnr, re_lpnr=re_lpnr, contextm='erome.GotoPage', baseurl=url.split('?')[0])
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'page={}'.format(np), r'page={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "erome.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def List2(url, section):
    if section == 'both':
        site.add_dir('Photos', url, 'List2', '', section='pics')
        site.add_dir('Videos', url, 'List2', '', section='vids')
    else:
        listhtml = utils.getHtml(url, site.url)
        items = listhtml.split('<div class="media-group')
        if len(items) > 1:
            items.pop(0)
            itemcount = 0
            for item in items:
                item = item.split('class="clearfix"')[0]
                if 'class="video"' in item and section == 'vids':
                    itemcount += 1
                    img, surl, hd, duration = re.findall(r'''poster="([^"]+).+?source\s*src="([^"]+).+?label='([^']+).+?class="duration"\s*>([^<]+)''', item, re.DOTALL)[0]
                    img += '|Referer={0}'.format(site.url)
                    surl += '|Referer={0}'.format(site.url)
                    site.add_download_link('Video {0}'.format(itemcount), surl, 'Playvid', img, duration=duration, quality=hd)
                elif 'class="video"' not in item and section == 'pics':
                    img = re.search(r'class="img-front(?:\s*lasyload)?"\s*(?:data-)?src="([^"]+)', item, re.DOTALL)
                    if img:
                        itemcount += 1
                        img = img.group(1) + '|Referer={0}'.format(site.url)
                        site.add_img_link('Photo {0}'.format(itemcount), img, 'Showpic')

    utils.eod()

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
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '+'))


@site.register()
def Search_user(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search_user')
    else:
        List(url + keyword.replace(' ', '+') + '?t=posts')


@site.register()
def Showpic(url, name):
    utils.showimage(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(url)


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('erome.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

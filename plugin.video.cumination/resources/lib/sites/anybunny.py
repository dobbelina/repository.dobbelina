'''
    Cumination
    Copyright (C) 2015 Whitecream

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
'''

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc
import xbmcgui
import ssl
from http.cookiejar import MozillaCookieJar
from urllib.error import HTTPError, URLError
from urllib import request
import html
import time
from urllib.parse import urljoin, urlparse


site = AdultSite("anybunny", "[COLOR hotpink]Anybunny[/COLOR]", "https://anybunny.org/", "anybunny.png", "anybunny")

VIEW_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Referer': site.url,
}


@site.register(default_mode=True)
def Main():
    # site.add_dir('[COLOR hotpink]Categories - images[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - all[/COLOR]', site.url, 'Categories2', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'new/', 'Search', site.img_search)
    # List(site.url + 'new/twins')
    Categories(site.url)
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        utils.notify(msg='No videos found!')
        return

    delimiter = r"<li\s+data-id='|class='nuyrfe"
    re_videopage = "href='([^']+)'"
    re_name = "alt='(.+?)'/>"
    re_img = r"src='([^']+)'"
    re_duration = r"'>([\d:]+)</div>"
    re_quality = r"'>(HD)\s*</div>"

    cm = []
    cm_related = (utils.addon_sys + "?mode=anybunny.Related&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    utils.videos_list(site, 'anybunny.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration, re_quality=re_quality, contextm=cm)

    re_npurl = 'href="([^"]+)">Next'
    re_npnr = r'\?p=(\d+)">Next'
    utils.next_page(site, 'anybunny.List', listhtml, re_npurl, re_npnr, contextm='anybunny.GotoPage')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    attempts = 0
    while '<title>anybunny' not in cathtml.lower() and attempts < 5:
        time.sleep(1)
        cathtml = utils._getHtml(url, '')
        attempts += 1

    match = re.compile(r"href='/top/([^']+)'>.*?src='([^']+)'\s*alt='([^']+)'", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match = sorted(match, key=lambda x: x[2])
    for catid, img, name in match:
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Categories2(url):
    cathtml = utils.getHtml(url, '')
    attempts = 0
    while '<title>anybunny' not in cathtml.lower() and attempts < 5:
        time.sleep(1)
        cathtml = utils._getHtml(url, '')
        attempts += 1

    match = re.compile(r"href='/top/([^']+)'>([^<]+)</a> <a>([^)]+\))", re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catid, name, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        catpage = site.url + 'new/' + catid
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        List(url + keyword.replace(' ', '_'))


@site.register()
def GotoPage(url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        url = re.sub(r'\?p=\d+', r'?p={}'.format(pg), url, re.IGNORECASE)
        contexturl = (utils.addon_sys + "?mode=" + "anybunny.List&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('anybunny.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    video_url = resolve_anybunny(url, return_all=False)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    if not video_url:
        utils.notify(msg='Video not found!')
        return
    video_url = video_url + '|User-Agent=' + VIEW_USER_AGENT
    vp.play_from_direct_link(video_url)


def fetch(url, headers=None, cookie_jar=None):
    if cookie_jar is None:
        cookie_jar = MozillaCookieJar()
    opener = request.build_opener(
        request.HTTPCookieProcessor(cookie_jar),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    req_headers = {**DEFAULT_HEADERS, **(headers or {})}
    response = opener.open(request.Request(url, headers=req_headers), timeout=30)
    try:
        return response.read().decode('utf-8', 'replace'), cookie_jar
    finally:
        response.close()


def clean_media_url(value):
    value = html.unescape(value).replace('\\/', '/').strip().strip('"\'<>')
    value = re.sub(r'^\[\d+\]', '', value)
    value = re.split(r':cast:', value, maxsplit=1, flags=re.IGNORECASE)[0]
    return value.rstrip('),;')


def extract_iframe_url(page_text, page_url):
    match = re.search(r'<iframe\b[^>]*\bsrc\s*=\s*(?:(["\'])(.*?)\1|([^\s>]+))', page_text, re.DOTALL | re.IGNORECASE)
    if match:
        value = match.group(2) if match.group(2) else match.group(3)
        return urljoin(page_url, html.unescape(value))
    return None


def extract_quality(url):
    """Extract quality/resolution from URL for sorting."""
    quality_match = re.search(r'(\d+)[pP]', url)
    if quality_match:
        return int(quality_match.group(1))

    url_lower = url.lower()
    if '/hd/' in url_lower or '/1080/' in url_lower:
        return 1080
    if '/720/' in url_lower:
        return 720
    if '/sd/' in url_lower or '/480/' in url_lower:
        return 480
    if '/360/' in url_lower:
        return 360
    return 0


def extract_all_media_urls(text):
    """Extract all video URLs sorted by quality (highest first)."""
    # Try player.js quality-labeled format: [240p]url,[480p]url,[720p]url
    playerjs_match = re.search(r'file\s*:\s*["\'](\[.*?\]https?://[^\'"]+)["\']', text, re.DOTALL | re.IGNORECASE)

    if playerjs_match:
        urls_with_quality = []
        for part in re.split(r',(?=\[)', playerjs_match.group(1)):
            quality_match = re.search(r'\[(\d+)p?\]', part, re.IGNORECASE)
            url_match = re.search(r'(https?://[^\s\[\]"\'<>:]+\.(?:mp4|m3u8)[^\s\[\]"\'<>:]*)', part, re.IGNORECASE)
            if quality_match and url_match:
                urls_with_quality.append((int(quality_match.group(1)), clean_media_url(url_match.group(1))))

        if urls_with_quality:
            urls_with_quality.sort(reverse=True, key=lambda x: x[0])
            return [url for _, url in urls_with_quality]

    # Fallback: extract URLs and sort by quality heuristics
    patterns = (
        r'(?:file|src)\s*:\s*["\']([^"\']+)',
        r'<source\b[^>]*\bsrc\s*=\s*(["\'])(.*?)\1',
        r'https?://[^\s"\'<>]+?\.(?:mp4|m3u8)(?:\?[^\s"\'<>]*)?',
    )

    found_urls = {}
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
            value = clean_media_url(match.group(match.lastindex) if match.lastindex else match.group(0))
            if value.startswith(('http://', 'https://')):
                base_url = value.split('?')[0]
                found_urls[base_url] = value

    urls_with_quality = [(extract_quality(url), url) for url in found_urls.values()]
    urls_with_quality.sort(reverse=True, key=lambda x: x[0])
    return [url for _, url in urls_with_quality]


def media_belongs_to_page(media_url, page_url):
    """Check if media URL belongs to the page (not cached/recommended content)."""
    path = urlparse(page_url).path.lower()
    if path.startswith('/view/'):
        return True

    media_path = urlparse(media_url).path.lower()
    page_id = re.search(r'/(?:t|too)/?(\d+)', path)
    if page_id:
        return page_id.group(1) in media_path

    page_parts = [part for part in re.split(r'[^a-z0-9]+', path) if len(part) > 5]
    return any(part in media_path for part in page_parts)


def follow_redirects(url, referer):
    opener = request.build_opener(request.HTTPSHandler(context=ssl.create_default_context()))
    headers = {**DEFAULT_HEADERS, 'Referer': referer}

    for method, extra_headers in (('HEAD', {}), ('GET', {'Range': 'bytes=0-0'})):
        try:
            response = opener.open(request.Request(url, headers={**headers, **extra_headers}, method=method), timeout=30)
            try:
                return response.geturl()
            finally:
                response.close()
        except (HTTPError, URLError):
            if method == 'GET':
                raise
    return url


def resolve_anybunny(url, return_all=False):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or parsed.netloc.lower() != 'anybunny.org':
        raise ValueError('URL Anybunny invalid')

    is_view_url = parsed.path.lower().startswith('/view/')
    page_headers = {'Referer': site.url}
    if is_view_url:
        page_headers['User-Agent'] = VIEW_USER_AGENT

    cookie_jar = None
    iframe_url = None
    page_text = ''

    # Try to fetch page and find iframe (retry up to 5 times)
    for _ in range(5):
        page_text, cookie_jar = fetch(url, headers=page_headers, cookie_jar=cookie_jar)

        # For non-view URLs, try direct extraction first
        if not is_view_url and not return_all:
            all_urls = extract_all_media_urls(page_text)
            for media_url in all_urls:
                if '.mp4' in media_url.lower() and media_belongs_to_page(media_url, url):
                    return follow_redirects(media_url, url)

        iframe_url = extract_iframe_url(page_text, url)
        if iframe_url:
            break
        time.sleep(0.5)

    # No iframe found - try direct extraction for return_all
    if not iframe_url:
        if return_all and not is_view_url:
            all_urls = extract_all_media_urls(page_text)
            valid_urls = [u for u in all_urls if media_belongs_to_page(u, url)]
            if valid_urls:
                try:
                    follow_redirects(valid_urls[0], url)
                    return valid_urls
                except (HTTPError, URLError):
                    pass
        return [] if return_all else None

    # Fetch player iframe
    player_text, _ = fetch(
        iframe_url,
        headers={'Referer': url, 'User-Agent': VIEW_USER_AGENT if is_view_url else DEFAULT_HEADERS['User-Agent']},
        cookie_jar=cookie_jar,
    )

    all_urls = extract_all_media_urls(player_text)
    if not all_urls:
        return [] if return_all else None

    if return_all:
        # Validate first URL for non-view pages
        if not is_view_url:
            try:
                follow_redirects(all_urls[0], iframe_url)
            except (HTTPError, URLError):
                return []
        return all_urls

    # Return single best URL (prefer mp4 for non-view pages)
    best_url = all_urls[0]
    if not is_view_url:
        for url_candidate in all_urls:
            if '.mp4' in url_candidate.lower():
                best_url = url_candidate
                break
        return follow_redirects(best_url, iframe_url)
    return best_url

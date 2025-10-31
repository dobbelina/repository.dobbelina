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

import re
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite('thothub', '[COLOR hotpink]ThotHub[/COLOR]', 'https://thothub.to/', 'thothub.png', 'thothub')


@site.register(default_mode=True)
def Main():
    # Home feed (latest)
    List(site.url)
    # Basic navigation helpers
    site.add_dir('[COLOR hotpink]Search[/COLOR]', urllib_parse.urljoin(site.url, '?s='), 'Search', site.img_search)
    utils.eod()


def _extract_list_items(html):
    items = []
    # Common card patterns (WordPress-like, lazy images, etc.)
    patterns = [
        r'<article[^>]*?>(.+?)</article>',
        r'<div[^>]+class="(?:post|card|video)[^>]*>(.+?)</div>'
    ]
    blocks = []
    for pat in patterns:
        blocks = re.compile(pat, re.DOTALL | re.IGNORECASE).findall(html)
        if blocks:
            break
    if not blocks:
        # Avoid scanning the whole page, which can pick up header/menu links
        return []

    for block in blocks:
        href = re.search(r'<a[^>]+href="([^"]+)"', block, re.IGNORECASE)
        img = re.search(r'<img[^>]+(?:data-src|data-lazy-src|src)="([^"]+)"', block, re.IGNORECASE)
        title = re.search(r'(?:title|alt)="([^"]+)"', block, re.IGNORECASE)
        if not href or not title:
            # Try a looser match
            m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(?:\s*<[^>]+>)*\s*([^<]{5,200})', block, re.DOTALL | re.IGNORECASE)
            if m:
                href = type('M', (), {'group': lambda self, i, _m=m: _m.group(i)})()
                title = type('M', (), {'group': lambda self, i, _m=m: _m.group(i)})()
        if href and title:
            url = href.group(1)
            # Skip obvious non-video links (menus, tags, authors, homepage)
            if any(x in url for x in ['/tag/', '/category/', '/author/', '/about', '/contact']) or url.rstrip('/') == site.url.rstrip('/'):
                continue
            name = utils.cleantext(title.group(1))
            thumb = img.group(1) if img else ''
            if thumb.startswith('//'):
                thumb = 'https:' + thumb
            items.append((url, name, thumb))
    # Deduplicate by URL
    seen = set()
    uniq = []
    for u, n, t in items:
        if u not in seen:
            uniq.append((u, n, t))
            seen.add(u)
    return uniq


def _find_next_page(html):
    # Try rel="next", or WordPress page-numbers
    m = re.search(r'rel=\"next\"\s*href=\"([^\"]+)\"', html, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'class=\"next page-numbers\"\s*href=\"([^\"]+)\"', html, re.IGNORECASE)
    if m:
        return m.group(1)
    # Fallback: generic next link
    m = re.search(r'\bnext\b[^>]*href=\"([^\"]+)\"', html, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


@site.register()
def List(url):
    # Try common listing endpoints until we find items
    candidates = []
    base = site.url.rstrip('/') + '/'
    candidates.append(url)
    candidates.append(urllib_parse.urljoin(base, 'videos/'))
    candidates.append(urllib_parse.urljoin(base, 'page/1/'))
    candidates.append(urllib_parse.urljoin(base, 'latest/'))

    listhtml = ''
    items = []
    for cu in candidates:
        try:
            listhtml = utils.getHtml(cu, site.url)
        except Exception:
            continue
        items = _extract_list_items(listhtml)
        if items:
            break

    for videopage, name, img in items:
        if videopage.startswith('/'):
            videopage = urllib_parse.urljoin(site.url, videopage)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    if listhtml:
        nurl = _find_next_page(listhtml)
        if nurl:
            if nurl.startswith('/'):
                nurl = urllib_parse.urljoin(site.url, nurl)
            site.add_dir('[COLOR hotpink]Next Page...[/COLOR]', nurl, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    # Let the generic resolver scrape embeds/iframes and play
    vp.play_from_site_link(url, site.url)


@site.register()
def Search(url, keyword=None):
    # WordPress-like search fallback
    search_url = url
    if not keyword:
        site.search_dir(search_url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        if '?' in search_url:
            search_url = search_url + title
        else:
            search_url = urllib_parse.urljoin(site.url, '?s=' + title)
        List(search_url)

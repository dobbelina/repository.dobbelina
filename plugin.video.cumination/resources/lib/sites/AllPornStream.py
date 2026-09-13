'''
    Cumination
    Copyright (C) 2022 Team Cumination

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
import json
import html
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('allpornstream', '[COLOR hotpink]AllPornStream[/COLOR]', 'https://allpornstream.com/', 'allpornstream.png')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'actors', 'Actors', site.img_cat)
    site.add_dir('[COLOR hotpink]Producers[/COLOR]', site.url + 'producers', 'Producers', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?search=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, site.url)
    except Exception:
        return None

    match = re.finditer(
        r'<div[^>]+data-thumb-id="([^"]+)"[^>]+data-href="([^"]+)"[^>]+data-slug="([^"]+)"[^>]+data-title="([^"]+)"([\s\S]*?)(?=<div class="group relative flex h-full|\Z)',
        listhtml,
        re.IGNORECASE,
    )
    
    for item in match:
        _, href, slug, title, block = item.groups()
        video_url = urllib_parse.urljoin(site.url, slug or href)
        if "/post/" not in video_url:
            continue

        title = utils.cleantext(title)
        if not title:
            continue

        thumb = _extract_best_image(block, item.group(0))

        duration = ""
        dur = re.search(r'<span[^>]*>\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\s*</span>', block)
        if dur:
            duration = dur.group(1)

        contextmenu = []
        contexturl = (utils.addon_sys + "?mode=allpornstream.Lookupinfo" + "&url=" + urllib_parse.quote_plus(video_url))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(title, video_url, 'Playvid', thumb, title, contextm=contextmenu, duration=duration)

    next_url = _extract_next_page(listhtml, url)
    if not next_url:
        count = len([m for m in re.finditer(r'data-thumb-id=', listhtml)])
        if count >= 50:
            next_url = _manual_next_page_url(url)
    
    if next_url:
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR]', next_url, 'List', site.img_next)
    
    utils.eod()


def _extract_best_image(block, full_match):
    thumb = ""
    
    srcset_match = re.search(r'<img[^>]+srcSet="([^"]+)"', block, re.IGNORECASE)
    if srcset_match:
        thumb = _select_best_from_srcset(srcset_match.group(1))
    
    if not thumb:
        img = re.search(r'<img[^>]+data-src="([^"]+)"', block, re.IGNORECASE)
        if img:
            thumb = img.group(1)
    
    if not thumb:
        img = re.search(r'<img[^>]+src="([^"]+)"', block, re.IGNORECASE)
        if img:
            thumb = img.group(1)
    
    if not thumb:
        images = re.search(r'data-images="([^"]+)"', full_match, re.IGNORECASE)
        if images:
            image_text = html.unescape(images.group(1))
            first = re.search(r'https?://[^",\]]+', image_text)
            if first:
                thumb = first.group(0)
    
    if not thumb:
        thumb_match = re.search(r'data-(?:thumb|poster)="([^"]+)"', block, re.IGNORECASE)
        if thumb_match:
            thumb = thumb_match.group(1)
    
    return _proxied_image(thumb)


def _select_best_from_srcset(srcset_value):
    if not srcset_value:
        return ""
    
    srcset_value = html.unescape(srcset_value)
    best_url = ""
    best_width = -1
    fallback_larger_url = ""
    fallback_larger_width = 99999
    
    for candidate in srcset_value.split(','):
        candidate = candidate.strip()
        if not candidate:
            continue
        
        parts = candidate.rsplit(' ', 1)
        image_url = parts[0].strip()
        width = 0
        
        if len(parts) > 1:
            width_match = re.search(r'(\d+)w', parts[1])
            if width_match:
                width = int(width_match.group(1))
        
        if 320 <= width <= 1920 and width > best_width:
            best_width = width
            best_url = image_url
        elif width > 1920 and width < fallback_larger_width:
            fallback_larger_width = width
            fallback_larger_url = image_url
    
    if not best_url and fallback_larger_url:
        best_url = fallback_larger_url
    
    return best_url


@site.register()
def Categories(url):
    _render_directory(url, 'categories')


@site.register()
def Actors(url):
    _render_directory(url, 'actors')


@site.register()
def Producers(url):
    _render_directory(url, 'producers')


def _render_directory(url, section):
    try:
        page_html = utils.getHtml(url or site.url + section, site.url)
    except Exception:
        return None

    items = _extract_serialized_directory_items(page_html, section)
    
    if not items:
        items = _extract_directory_links(page_html, section)

    for item in items:
        label = item['label']
        if item.get('count'):
            label += ' [COLOR hotpink]({} videos)[/COLOR]'.format(item['count'])
        site.add_dir(label, item['url'], 'List', item['thumb'])

    np = re.search(r'class="pagination".+?href="([^"]+)"[^>]*>Next', page_html, re.IGNORECASE | re.DOTALL)
    if np:
        next_page = np.group(1)
        if next_page.startswith('/'):
            next_page = site.url + next_page[1:]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR]', next_page, section.capitalize(), site.img_next)
    
    utils.eod()


def _extract_serialized_directory_items(page_html, section):
    key = {'actors': 'actor', 'categories': 'category', 'producers': 'producer'}.get(section)
    if not key:
        return []

    text = _decode_next_strings(page_html)
    pattern = r'\{[^{}]*"' + re.escape(key) + r'"\s*:\s*"[^"]+"[^{}]*\}'
    items = []
    seen = set()

    for match in re.finditer(pattern, text, re.IGNORECASE):
        try:
            data = json.loads(match.group(0))
        except Exception:
            continue
        
        raw_name = data.get(key) or ""
        if not raw_name:
            continue
            
        label = _display_directory_name(raw_name, section)
        slug = _slugify(raw_name)
        dedupe_key = raw_name.lower()
        
        if not label or not slug or dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        images = data.get("thumbs_urls") or data.get("images") or []
        thumb = _proxied_image(images[0]) if images else ''
        count = int(data.get("count") or data.get("videos_count") or 0)
        
        url = urllib_parse.urljoin(site.url, "/{}/{}".format(section, slug))
        items.append({
            'label': label,
            'url': url,
            'thumb': thumb,
            'count': count
        })
    
    return items


def _extract_directory_links(page_html, section):
    items = []
    seen = set()
    pattern = r'<a\b(?=[^>]*href="/' + re.escape(section) + r'/[^"]+")[^>]*>[\s\S]*?</a>'
    
    for match in re.finditer(pattern, page_html, re.IGNORECASE):
        anchor = match.group(0)
        href_match = re.search(r'href="(/' + re.escape(section) + r'/[^"]+)"', anchor, re.IGNORECASE)
        if not href_match:
            continue
            
        href = href_match.group(1)
        url = urllib_parse.urljoin(site.url, href)
        if url in seen:
            continue
        seen.add(url)

        label = ""
        title = re.search(r'title="View all videos (?:with|from|in) ([^"]+)"', anchor, re.IGNORECASE)
        if title:
            label = utils.cleantext(title.group(1))
        if not label:
            alt = re.search(r'<img[^>]+alt="([^"]+)"', anchor, re.IGNORECASE)
            if alt:
                label = utils.cleantext(alt.group(1))
        if not label:
            text = re.sub(r'<[^>]+>', '', anchor)
            label = utils.cleantext(text)
        
        if not label or label.lower() in ("actors", "categories", "producers"):
            continue

        thumb = ""
        srcset_match = re.search(r'<img[^>]+srcSet="([^"]+)"', anchor, re.IGNORECASE)
        if srcset_match:
            thumb = _select_best_from_srcset(srcset_match.group(1))
        
        if not thumb:
            img = re.search(r'<img[^>]+data-src="([^"]+)"', anchor, re.IGNORECASE)
            if img:
                thumb = img.group(1)
        
        if not thumb:
            img = re.search(r'<img[^>]+src="([^"]+)"', anchor, re.IGNORECASE)
            if img:
                thumb = img.group(1)
        
        thumb = _proxied_image(thumb)
        
        items.append({
            'label': label,
            'url': url,
            'thumb': thumb,
            'count': 0
        })
    
    items.sort(key=lambda x: x['label'].lower())
    return items


def _decode_next_strings(page_html):
    chunks = []
    for raw in re.findall(r'self\.__next_f\.push\(\[1,"([\s\S]*?)"\]\)</script>', page_html):
        try:
            chunks.append(bytes(raw, "utf-8").decode("unicode_escape"))
        except Exception:
            chunks.append(raw)
    return "\n".join(chunks) if chunks else page_html


def _display_directory_name(text, section):
    text = html.unescape(text or "").strip()
    if section == "actors":
        return text
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)
    text = text.replace("-", " ").replace("_", " ")
    return " ".join(part.capitalize() for part in text.split())


def _slugify(text):
    text = html.unescape(text or "")
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", "-", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _proxied_image(src):
    if not src:
        return ""
    
    src = html.unescape(src).strip()
    
    if src.startswith("https://apstream.org") or src.startswith("http://apstream.org"):
        if "width=" in src:
            src = re.sub(r'width=\d+', 'width=1920', src)
        else:
            src += "&width=1920&quality=90" if "?" in src else "?width=1920&quality=90"
        return src
    
    if src.startswith("/api/images?"):
        if "width=" in src:
            src = re.sub(r'width=\d+', 'width=1920', src)
            if "quality=" not in src:
                src += "&quality=90"
        else:
            src += "&width=1920&quality=90" if "?" in src else "?width=1920&quality=90"
        return urllib_parse.urljoin(site.url, src)
    
    if src.startswith("http"):
        proxy_url = "/api/images?src={}&width=1920&quality=90".format(
            urllib_parse.quote(src, safe="")
        )
        return urllib_parse.urljoin(site.url, proxy_url)
    
    return urllib_parse.urljoin(site.url, src)


def _extract_next_page(page_html, current_url):
    links = re.findall(r'href="([^"]*(?:\?|&)page=(\d+)[^"]*)"', page_html, re.IGNORECASE)
    if not links:
        return ""
    
    current_page = 1
    parsed = urllib_parse.urlparse(current_url)
    params = urllib_parse.parse_qs(parsed.query)
    try:
        current_page = int((params.get("page") or ["1"])[0])
    except Exception:
        current_page = 1
    
    candidates = []
    for href, number in links:
        try:
            page = int(number)
        except Exception:
            continue
        if page > current_page:
            candidates.append((page, urllib_parse.urljoin(site.url, href)))
    
    if candidates:
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]
    return ""


def _manual_next_page_url(current_url):
    parsed = urllib_parse.urlparse(current_url)
    params = urllib_parse.parse_qs(parsed.query, keep_blank_values=True)
    try:
        current_page = int((params.get("page") or ["1"])[0])
    except Exception:
        current_page = 1
    params["page"] = [str(current_page + 1)]
    query = urllib_parse.urlencode(params, doseq=True)
    return urllib_parse.urlunparse(parsed._replace(query=query))


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    try:
        page_html = utils.getHtml(url, site.url)
    except Exception:
        vp.progress.close()
        utils.notify('Oh oh', 'Could not load video page')
        return
    
    text = _decode_next_strings(page_html)
    links = []
    seen = set()
    
    for embed_url in re.findall(r'"embed_url"\s*:\s*"(https?://[^"]+)"', text, re.IGNORECASE):
        embed_url = re.sub(r"\s+", "", html.unescape(embed_url).replace("\\/", "/")).strip()
        if embed_url and embed_url not in seen:
            seen.add(embed_url)
            links.append(embed_url)
    
    for pattern in [
        r'(https?://(?:streamtape|doodstream|dood\.|dooood|miiixdrop|mixdrop|m1xdrop|voe\.sx|lulustream|lulu|mydaddy\.cc)[^\s"\'<>\\]+)',
    ]:
        for url_found in re.findall(pattern, text, re.IGNORECASE):
            url_found = re.sub(r"\s+", "", html.unescape(url_found).replace("\\/", "/")).strip()
            if url_found and url_found not in seen:
                seen.add(url_found)
                links.append(url_found)
    
    if not links:
        vp.progress.close()
        utils.notify('Oh oh', 'No video host found')
        return
    
    vp.play_from_link_list(links)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = url + urllib_parse.quote_plus(keyword.strip())
        List(searchUrl)


@site.register()
def Lookupinfo(url):
    try:
        page_html = utils.getHtml(url, site.url)
    except Exception:
        return
    
    lookup_list = [
        ("Cat", r'href="(/categories/[^"]+)"[^>]*>[\s\S]*?<span[^>]*>([^<]+)</span>', ''),
        ("Actor", r'href="(/actors/[^"]+)"[^>]*>[\s\S]*?<span[^>]*>([^<]+)</span>', ''),
        ("Producer", r'href="(/producers/[^"]+)"[^>]*>[\s\S]*?<span[^>]*>([^<]+)</span>', ''),
    ]

    lookupinfo = utils.LookupInfo('', url, 'allpornstream.List', lookup_list)
    lookupinfo.getinfo()
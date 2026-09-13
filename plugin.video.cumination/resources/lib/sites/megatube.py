"""
    Cumination
    Copyright (C) 2024

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
import html
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('megatube', "[COLOR hotpink]MegaTube[/COLOR]", 'https://www.megatube.xxx/', 'megatube.png', 'megatube')


def get_page(url, referer=None):
    try:
        return utils.getHtml(url, referer)
    except Exception:
        return None


def kvs_decode_url(encoded_url, license_code):
    if not encoded_url.startswith('function/0/'):
        return encoded_url
    
    encoded = encoded_url[11:]
    license_part = license_code.replace('$', '').replace('0', '')
    result = []
    
    for i, char in enumerate(encoded):
        shift = ord(license_part[i]) % 26 if i < len(license_part) else i % 26
        char_code = ord(char)
        
        if 97 <= char_code <= 122:
            result.append(chr(((char_code - 97 - shift) % 26) + 97))
        elif 65 <= char_code <= 90:
            result.append(chr(((char_code - 65 - shift) % 26) + 65))
        else:
            result.append(char)
    
    decoded = ''.join(result)
    try:
        import base64
        decoded = base64.b64decode(decoded).decode('utf-8')
    except Exception:
        pass
    
    return decoded


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Most Popular[/COLOR]', site.url + 'most-popular/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Longest[/COLOR]', site.url + 'longest/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars/', 'Models', site.img_models)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'most-popular/')
    utils.eod()


@site.register()
def List(url, page=1):
    page = int(page) if page and str(page).isdigit() else 1
    
    if page > 1:
        url = get_page_url(url, page)
    
    html_content = get_page(url, site.url)
    
    if not html_content or 'No videos found' in html_content or len(html_content) < 1000:
        utils.notify('MegaTube', 'No video found')
        utils.eod()
        return
    
    videos = extract_videos(html_content)
    
    if not videos:
        videos = extract_videos_alt(html_content)
    
    if not videos:
        utils.notify('MegaTube', 'No video found')
        utils.eod()
        return
    
    for video in videos:
        site.add_download_link(
            video['label'],
            video['url'],
            'megatube.Playvid',
            video['thumb'],
            desc=video['info'].get('plot', ''),
            duration='',
            quality=video.get('quality', '')
        )
    
    next_url = extract_next_page(html_content, url, page)
    if next_url:
        site.add_dir('Next Page', next_url, 'List', site.img_next, page=page+1)
    
    utils.eod()


def extract_videos(html_content):
    videos = []
    seen = set()
    
    blocks = re.findall(r'<div[^>]+class=["\'][^"\']*item[^"\']*["\'][^>]*>(.*?)</div>\s*</div>\s*</div>', html_content, re.DOTALL | re.IGNORECASE)
    
    if not blocks:
        blocks = re.findall(r'<div[^>]+class=["\'][^"\']*(?:item|thumb)[^"\']*["\'][^>]*>(.*?)</div>', html_content, re.DOTALL | re.IGNORECASE)
    
    for block in blocks:
        href_match = re.search(r'<a[^>]+href=["\']([^"\']*/videos/\d+/[^"\']*)["\']', block, re.IGNORECASE)
        if not href_match:
            continue
        
        video_url = fix_url(href_match.group(1))
        if not video_url or video_url in seen:
            continue
        seen.add(video_url)
        
        title = ''
        title_match = re.search(r'<a[^>]+title=["\']([^"\']+)["\']', block, re.IGNORECASE)
        if title_match:
            title = clean_text(title_match.group(1))
        
        if not title:
            alt_match = re.search(r'<img[^>]+alt=["\']([^"\']+)["\']', block, re.IGNORECASE)
            if alt_match:
                title = clean_text(alt_match.group(1))
        
        if not title or title.lower() in ('videos', 'rss', ''):
            continue
        
        thumb = ''
        for pattern in [
            r'<img[^>]+class=["\'][^"\']*thumb[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]+data-src=["\']([^"\']+)["\']',
            r'data-mediumthumb=["\']([^"\']+)["\']',
            r'(https?://img\d+\.mt-static\.com/[^"\']+)'
        ]:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                thumb = fix_url(match.group(1))
                break
        
        duration = ''
        dur_match = re.search(r'(\d+m:\d+s)', block, re.IGNORECASE)
        if dur_match:
            duration = dur_match.group(1)
        else:
            dur_div_match = re.search(r'<span[^>]+class=["\'][^"\']*duration[^"\']*["\'][^>]*>([^<]+)</span>', block, re.IGNORECASE)
            if dur_div_match:
                duration = clean_text(dur_div_match.group(1))
        
        label = title
        if duration:
            label = '{} [COLOR hotpink]({})[/COLOR]'.format(title, duration)
        
        quality = ''
        qual_match = re.search(r'<span[^>]+class=["\'][^"\']*quality[^"\']*["\'][^>]*>([^<]+)</span>', block, re.IGNORECASE)
        if qual_match:
            quality = qual_match.group(1).strip()
        
        videos.append({
            'label': label,
            'url': video_url,
            'thumb': thumb,
            'quality': quality,
            'info': {
                'title': title,
                'plot': title,
                'duration': duration
            }
        })
    
    return videos


def extract_videos_alt(html_content):
    videos = []
    seen = set()
    
    matches = re.findall(r'<a[^>]+href=["\']([^"\']*/videos/\d+/[^"\']*)["\'][^>]*>(.*?)</a>', html_content, re.DOTALL | re.IGNORECASE)
    
    for href, content in matches:
        video_url = fix_url(href)
        if video_url in seen or not video_url:
            continue
        seen.add(video_url)
        
        title_match = re.search(r'title=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'>([^<]+)<', content)
        
        title = clean_text(title_match.group(1)) if title_match else ''
        
        if not title or title.lower() in ('videos', 'rss'):
            continue
        
        thumb = ''
        img_match = re.search(r'src=["\']([^"\']*mt-static\.com[^"\']*)["\']', content, re.IGNORECASE)
        if img_match:
            thumb = fix_url(img_match.group(1))
        
        if not thumb:
            medium_match = re.search(r'data-mediumthumb=["\']([^"\']+)["\']', content, re.IGNORECASE)
            if medium_match:
                thumb = fix_url(medium_match.group(1))
        
        videos.append({
            'label': title,
            'url': video_url,
            'thumb': thumb,
            'quality': '',
            'info': {
                'title': title,
                'plot': title,
                'duration': ''
            }
        })
    
    return videos


def extract_next_page(html_content, current_url, page):
    next_page = page + 1
    
    if 'from_videos:{}'.format(next_page) in html_content:
        return get_page_url(current_url, next_page)
    
    if re.search(r'data-parameters=["\'][^"\']*from:0?{}(?:["\';]|$)'.format(next_page), html_content, re.IGNORECASE):
        return get_page_url(current_url, next_page)
    
    parsed_next = urllib_parse.urlparse(get_page_url(current_url, next_page))
    if re.search(r'href=["\'][^"\']*{}["\']'.format(re.escape(parsed_next.path)), html_content, re.IGNORECASE):
        return get_page_url(current_url, next_page)
    
    return None


def get_page_url(base_url, page_num):
    if page_num <= 1:
        return base_url
    
    parsed = urllib_parse.urlparse(base_url)
    query = urllib_parse.parse_qs(parsed.query)
    
    if 'q' in query or '/search/' in parsed.path:
        query['from_videos'] = [str(page_num)]
        return urllib_parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urllib_parse.urlencode(query, doseq=True), parsed.fragment))
    
    if '.porn' in parsed.path:
        query['page'] = [str(page_num)]
        return urllib_parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urllib_parse.urlencode(query, doseq=True), parsed.fragment))
    
    path = parsed.path
    if not path.endswith('/'):
        path += '/'
    
    if re.search(r'/\d+/$', path):
        path = re.sub(r'/\d+/$', '/{}/'.format(page_num), path)
    else:
        path += '{}/'.format(page_num)
    
    return urllib_parse.urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))


def clean_text(value):
    value = re.sub(r'<[^>]+>', ' ', value or '')
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


def fix_url(value):
    if not value:
        return ''
    return urllib_parse.urljoin(site.url, html.unescape(value).strip())


@site.register()
def Categories(url):
    html_content = get_page(url, site.url)
    
    if not html_content:
        utils.notify('MegaTube', 'Error loading categories')
        utils.eod()
        return
    
    seen = set()
    next_url = ''
    
    cat_matches = re.findall(r'<a[^>]+href=["\'](/[^"\']*\.porn)["\'][^>]*>(.*?)</a>', html_content, re.DOTALL | re.IGNORECASE)
    
    for href, body in cat_matches:
        cat_url = fix_url(href)
        if not cat_url or cat_url in seen:
            continue
        seen.add(cat_url)
        
        title = ''
        title_match = re.search(r'<img[^>]+(?:alt|title)=["\']([^"\']+)["\']', body, re.IGNORECASE)
        if title_match:
            title = clean_text(title_match.group(1))
        
        if not title:
            title = href.strip('/').replace('.porn', '').replace('-', ' ').title()
        
        if not title or title.isdigit() or title.lower() in ('next', 'last', ''):
            continue
        
        img = site.img_cat
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
        if img_match:
            img = fix_url(img_match.group(1))
        
        site.add_dir(title, cat_url, 'List', img)
    
    if not seen:
        for anchor_match in re.finditer(r'<a\b([^>]*)href=["\']([^"\']+)["\']([^>]*)>([\s\S]{0,1800}?)<\/a>', html_content, re.IGNORECASE):
            attrs = '{} {}'.format(anchor_match.group(1), anchor_match.group(3))
            href = anchor_match.group(2)
            body = anchor_match.group(4)
            clean_body = clean_text(body)
            
            from_match = re.search(r'from:(\d+)', attrs, re.IGNORECASE)
            if clean_body.lower() == 'next' or from_match:
                if href and not href.startswith('#'):
                    next_url = fix_url(href)
                continue
            
            is_category = href.endswith('.porn') or '/categories/' in href or '/category/' in href
            if not is_category:
                continue
            
            cat_url = fix_url(href)
            if not cat_url or cat_url in seen:
                continue
            seen.add(cat_url)
            
            title = ''
            title_match = re.search(r'<img\b[^>]*\s(?:alt|title)=[\'"]([^\'"]+)[\'"]', body, re.IGNORECASE)
            if title_match:
                title = clean_text(title_match.group(1))
            
            if not title:
                span_match = re.search(r'<span[^>]*>([^<]+)</span>', body, re.IGNORECASE)
                if span_match:
                    title = clean_text(span_match.group(1))
            
            if not title:
                title = clean_body
            
            if not title or title.isdigit() or title.lower() in ('next', 'last', ''):
                continue
            
            img = site.img_cat
            img_match = re.search(r'(https?://img\d+\.mt-static\.com/[^"\']+)', body, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'data-mediumthumb=["\']([^"\']+)["\']', body, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'<img\b[^>]*\ssrc=[\'"]([^\'"]+)[\'"]', body, re.IGNORECASE)
            
            if img_match:
                img = fix_url(img_match.group(1))
            
            site.add_dir(title, cat_url, 'List', img)
    
    if next_url:
        site.add_dir('Next Page', next_url, 'Categories', site.img_next)
    
    utils.eod()


@site.register()
def Models(url):
    html_content = get_page(url, site.url)
    
    if not html_content:
        utils.notify('MegaTube', 'Error loading models')
        utils.eod()
        return
    
    seen = set()
    next_url = ''
    
    model_matches = re.findall(r'<a[^>]+href=["\'](/pornstars/[^"\']+)["\'][^>]*>(.*?)</a>', html_content, re.DOTALL | re.IGNORECASE)
    
    for href, body in model_matches:
        if 'from' in href.lower():
            continue
        
        model_url = fix_url(href)
        if not model_url or model_url in seen:
            continue
        seen.add(model_url)
        
        if not re.search(r'<img', body, re.IGNORECASE):
            continue
        
        title = ''
        title_match = re.search(r'<img[^>]+(?:alt|title)=["\']([^"\']+)["\']', body, re.IGNORECASE)
        if title_match:
            title = clean_text(title_match.group(1))
        
        if not title:
            title = href.rstrip('/').split('/')[-1].replace('-', ' ').title()
        
        if not title:
            continue
        
        img = site.img_models
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
        if img_match:
            img = fix_url(img_match.group(1))
        
        site.add_dir(title, model_url, 'List', img)
    
    if not seen:
        for anchor_match in re.finditer(r'<a\b([^>]*)href=["\']([^"\']+)["\']([^>]*)>([\s\S]{0,1800}?)<\/a>', html_content, re.IGNORECASE):
            attrs = '{} {}'.format(anchor_match.group(1), anchor_match.group(3))
            href = anchor_match.group(2)
            body = anchor_match.group(4)
            clean_body = clean_text(body)
            
            from_match = re.search(r'from:(\d+)', attrs, re.IGNORECASE)
            if clean_body.lower() == 'next' or from_match:
                if href and not href.startswith('#'):
                    next_url = fix_url(href)
                continue
            
            if '/pornstars/' not in href:
                continue
            
            if not re.search(r'<img\b', body, re.IGNORECASE):
                continue
            
            model_url = fix_url(href)
            if not model_url or model_url in seen:
                continue
            seen.add(model_url)
            
            title_match = re.search(r'<img\b[^>]*\s(?:alt|title)=[\'"]([^\'"]+)[\'"]', body, re.IGNORECASE)
            title = clean_text(title_match.group(1) if title_match else clean_body)
            
            if not title:
                continue
            
            img_match = re.search(r'(https?://img\d+\.mt-static\.com/[^"\']+)', body, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'data-mediumthumb=["\']([^"\']+)["\']', body, re.IGNORECASE)
            if not img_match:
                img_match = re.search(r'<img\b[^>]*\ssrc=[\'"]([^\'"]+)[\'"]', body, re.IGNORECASE)
            
            img = fix_url(img_match.group(1)) if img_match else site.img_models
            
            site.add_dir(title, model_url, 'List', img)
    
    if next_url:
        site.add_dir('Next Page', next_url, 'Models', site.img_next)
    
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        search_url = '{}{}/'.format(url, keyword.replace(' ', '-'))
        List(search_url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, '[CR]Loading...[CR]')
    
    html_content = get_page(url, site.url)
    
    if not html_content:
        utils.notify('MegaTube', 'Error loading video')
        vp.progress.close()
        return
    
    license_code = ''
    license_match = re.search(r'license_code\s*:\s*[\'"]([^\'"]+)[\'"]', html_content, re.IGNORECASE)
    if license_match:
        license_code = html.unescape(license_match.group(1)).strip()
    
    urls = {}
    
    for key, value in re.findall(r'(video_url|video_alt_url\d*):\s*[\'"]([^\'"]+)["\']', html_content, re.IGNORECASE):
        stream_url = kvs_decode_url(html.unescape(value).replace('\\/', '/').strip(), license_code)
        if '.mp4' in stream_url and ('get_file/' in stream_url or stream_url.startswith('http')):
            urls[key] = stream_url
    
    for href in re.findall(r'href=["\']([^"\']+\.mp4/?[^"\']*)["\']', html_content, re.IGNORECASE):
        stream_url = kvs_decode_url(html.unescape(href).replace('\\/', '/').strip(), license_code)
        if '.mp4' in stream_url and ('get_file/' in stream_url or stream_url.startswith('http')):
            urls.setdefault('download', stream_url)
    
    for source in re.findall(r'<source\b[^>]*\bsrc=["\']([^"\']+\.mp4/?[^"\']*)["\']', html_content, re.IGNORECASE):
        stream_url = kvs_decode_url(html.unescape(source).replace('\\/', '/').strip(), license_code)
        if '.mp4' in stream_url and ('get_file/' in stream_url or stream_url.startswith('http')):
            urls.setdefault('source', stream_url)
    
    order = ['video_alt_url5', 'video_alt_url4', 'video_alt_url3', 'video_alt_url2', 'video_alt_url', 'video_url', 'source', 'download']
    
    videourl = None
    for key in order:
        if key in urls:
            videourl = urls[key]
            break
    
    if videourl:
        videourl = videourl + '|Referer=' + urllib_parse.quote_plus(url) + '&User-Agent=' + urllib_parse.quote_plus(utils.USER_AGENT)
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_site_link(url)
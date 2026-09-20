# -*- coding: utf-8 -*-
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
import json
import base64
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('onlyjerk', '[COLOR hotpink]OnlyJerk[/COLOR]', 'https://onlyjerk.net/', 
                 'https://onlyjerk.net/wp-content/uploads/2024/01/apple-icon-180x180-1.png', 'onlyjerk')


def safe_base64_decode(encoded_str):
    try:
        if not encoded_str or len(encoded_str) < 4:
            return None
        padding = 4 - len(encoded_str) % 4
        if padding != 4:
            encoded_str += '=' * padding
        decoded = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        return decoded if decoded.startswith('http') else None
    except:
        return None


def is_preview_url(url):
    if not url:
        return True
    preview_indicators = ['preview', 'short', '8s', 'teaser', 'clip', '/p/', '-p-', '_preview_', 'shortvid']
    url_lower = url.lower()
    for indicator in preview_indicators:
        if indicator in url_lower:
            return True
    return False


def find_video_blocks(html):
    """Trouve les blocs vidéo"""
    patterns = [
        (r'<div[^>]*class="[^"]*tdb_module_loop_2[^"]*".*?</div>\s*</div>\s*</div>', "tdb_module_loop_2"),
        (r'<div[^>]*class="[^"]*td_module_flex[^"]*td_module_wrap[^"]*".*?</div>\s*</div>\s*</div>\s*</div>', "td_module_flex"),
        (r'<div[^>]*class="[^"]*td_module_wrap[^"]*".*?</div>\s*</div>', "td_module_wrap"),
        (r'<article[^>]*class="[^"]*post[^"]*".*?</article>', "article_post"),
    ]
    
    for pattern, name in patterns:
        blocks = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        if blocks:
            return blocks, name
    
    return [], "none"


def extract_video_info(block):
    """Extrait titre, URL et thumbnail d'un bloc"""
    try:
        block = block.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        title_match = re.search(
            r'<h3[^>]*class="[^"]*td-module-title[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>([^<]+)',
            block, re.DOTALL
        )
        
        if not title_match:
            title_match = re.search(
                r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>([^<]{5,})',
                block, re.DOTALL
            )
        
        if not title_match:
            return None
        
        video_url = title_match.group(1)
        title = title_match.group(3) if len(title_match.groups()) > 2 else title_match.group(2)
        title = re.sub(r'<[^>]+>', '', title).strip()
        
        if not video_url.startswith('http'):
            video_url = site.url + video_url.lstrip('/')
        
        if '/category/' in video_url or '/tag/' in video_url or '/page/' in video_url:
            return None
        
        thumbnail = ''
        thumb_match = re.search(r'background-image:\s*url\(["\']?([^"\'\)]+)["\']?\)', block, re.IGNORECASE)
        if thumb_match:
            thumbnail = thumb_match.group(1)
        else:
            thumb_match = re.search(r'data-src="([^"]+)"', block)
            if thumb_match:
                thumbnail = thumb_match.group(1)
            else:
                thumb_match = re.search(r'src="([^"]+)"[^>]*class="[^"]*entry-thumb', block)
                if thumb_match:
                    thumbnail = thumb_match.group(1)
        
        return {
            'url': video_url,
            'title': title,
            'thumb': thumbnail,
        }
        
    except Exception:
        return None


@site.register(default_mode=True)
def Main(url=''):
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'Search', '')
    List(site.url + 'latest-videos/')


@site.register()
def Categories(url=''):
    try:
        html = utils.getHtml(url, site.url)
        categories_found = []
        
        cat_blocks = re.findall(
            r'<li[^>]*class="[^"]*menu-item-type-taxonomy[^"]*menu-item-object-category[^"]*".*?</li>',
            html, re.DOTALL | re.IGNORECASE
        )
        
        for block in cat_blocks:
            url_match = re.search(r'href="([^"]+)"', block)
            if url_match:
                cat_url = url_match.group(1)
                name_match = re.search(r'<div[^>]*class="[^"]*tdb-menu-item-text[^"]*"[^>]*>([^<]+)</div>', block)
                if not name_match:
                    name_match = re.search(r'>([^<]+)</a>', block)
                
                if name_match:
                    cat_name = name_match.group(1).strip()
                    cat_name = utils.cleantext(cat_name)
                    if cat_name and len(cat_name) > 1:
                        if not cat_url.startswith('http'):
                            cat_url = site.url + cat_url.lstrip('/')
                        if (cat_name, cat_url) not in categories_found:
                            categories_found.append((cat_name, cat_url))
        
        if len(categories_found) < 3:
            mobile_menu = re.search(
                r'<ul id="menu-header-menu-1"(.*?)</ul>',
                html, re.DOTALL | re.IGNORECASE
            )
            if mobile_menu:
                menu_html = mobile_menu.group(1)
                cat_matches = re.findall(
                    r'<li[^>]*class="[^"]*menu-item-type-taxonomy[^"]*menu-item-object-category[^"]*".*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
                    menu_html, re.DOTALL | re.IGNORECASE
                )
                for cat_url, cat_name in cat_matches:
                    cat_name = utils.cleantext(cat_name.strip())
                    if cat_name and len(cat_name) > 1:
                        if not cat_url.startswith('http'):
                            cat_url = site.url + cat_url.lstrip('/')
                        if (cat_name, cat_url) not in categories_found:
                            categories_found.append((cat_name, cat_url))
        
        if len(categories_found) < 3:
            categories_found = [
                ('OnlyFans', 'https://onlyjerk.net/onlyfans/'),
                ('Camwhores', 'https://onlyjerk.net/camwhores/'),
                ('Private Ticket', 'https://onlyjerk.net/private-ticket/'),
                ('Asian', 'https://onlyjerk.net/asian/'),
                ('Fansly', 'https://onlyjerk.net/fansly/'),
                ('ManyVids', 'https://onlyjerk.net/manyvids/'),
                ('Porn', 'https://onlyjerk.net/porn/'),
                ('Trending', 'https://onlyjerk.net/trending/'),
                ('Featured', 'https://onlyjerk.net/featured/'),
                ('Exclusive', 'https://onlyjerk.net/exclusive/'),
                ('Top Weekly', 'https://onlyjerk.net/popular-recent/'),
                ('Most Viewed', 'https://onlyjerk.net/most-viewed/'),
            ]
        
        for name, caturl in categories_found:
            site.add_dir(name, caturl, 'List', '')
        
        utils.eod()
    except Exception:
        pass


@site.register()
def List(url=''):
    try:
        html = utils.getHtml(url, site.url)
        
        blocks, pattern_name = find_video_blocks(html)
        
        if not blocks:
            utils.notify('OnlyJerk', 'No videos found')
            return
        
        videos = []
        for block in blocks:
            info = extract_video_info(block)
            if info and info['url'] not in [v['url'] for v in videos]:
                videos.append(info)
        
        if not videos:
            utils.notify('OnlyJerk', 'No valid videos extracted')
            return
        
        for video in videos:
            site.add_download_link(video['title'], video['url'], 'Playvid', 
                                 video['thumb'], fanart=video['thumb'])
        
        current_page = 1
        page_match = re.search(r'/page/(\d+)/', url)
        if page_match:
            current_page = int(page_match.group(1))
        
        next_page_num = current_page + 1
        next_url = None
        
        next_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*aria-label=["\']next-page["\']', html, re.IGNORECASE)
        if next_match:
            next_url = next_match.group(1)
        
        if not next_url:
            next_pattern = rf'href=["\']([^"\']*page/{next_page_num}/[^"\']*)["\'"]'
            next_match = re.search(next_pattern, html, re.IGNORECASE)
            if next_match:
                next_url = next_match.group(1)
        
        if not next_url and current_page == 1:
            next_match = re.search(r'href=["\']([^"\']*latest-videos/page/2/[^"\']*)["\'"]', html, re.IGNORECASE)
            if next_match:
                next_url = next_match.group(1)
        
        if not next_url and current_page == 1 and 'latest-videos' in url:
            next_url = site.url + 'latest-videos/page/2/'
        
        if next_url:
            next_url = next_url.strip()
            if '#' in next_url:
                next_url = next_url.split('#')[0]
            
            if next_url and next_url not in ['/', '#']:
                if not next_url.startswith('http'):
                    next_url = site.url + next_url.lstrip('/')
                
                if next_url != url:
                    site.add_dir(f'[COLOR hotpink]Next Page ({next_page_num})[/COLOR]', next_url, 'List', '')
        
        utils.eod()
    except Exception:
        pass


@site.register()
def Search(url='', keyword=None):
    try:
        if not keyword:
            if 's=' in url:
                kw_match = re.search(r'[?&]s=([^&]+)', url)
                if kw_match:
                    keyword = urllib_parse.unquote_plus(kw_match.group(1))
            
            if not keyword:
                site.search_dir(url, 'Search')
                return
        
        if 's=' not in url:
            search_url = site.url + '?s=' + urllib_parse.quote_plus(keyword)
        else:
            search_url = url
        
        html = utils.getHtml(search_url, site.url)
        
        blocks, pattern_name = find_video_blocks(html)
        
        if not blocks:
            utils.notify('OnlyJerk', 'No results found')
            return
        
        videos = []
        for block in blocks:
            info = extract_video_info(block)
            if info and info['url'] not in [v['url'] for v in videos]:
                videos.append(info)
        
        if not videos:
            utils.notify('OnlyJerk', 'No valid videos found')
            return
        
        for video in videos:
            site.add_download_link(video['title'], video['url'], 'Playvid', 
                                 video['thumb'], fanart=video['thumb'])
        
        current_page = 1
        page_match = re.search(r'/page/(\d+)/', search_url)
        if page_match:
            current_page = int(page_match.group(1))
        
        next_page_num = current_page + 1
        next_url = None
        
        next_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*aria-label=["\']next-page["\']', html, re.IGNORECASE)
        if next_match:
            next_url = next_match.group(1)
        
        if not next_url:
            kw_match = re.search(r'[?&]s=([^&]+)', search_url)
            if kw_match:
                search_kw = kw_match.group(1)
                next_pattern = rf'href="([^"]*page/{next_page_num}/[^"]*\?s={re.escape(search_kw)}[^"]*)"'
                next_match = re.search(next_pattern, html, re.IGNORECASE)
                if next_match:
                    next_url = next_match.group(1)
        
        if not next_url:
            next_match = re.search(rf'href="([^"]*page/{next_page_num}/[^"]*)"', html, re.IGNORECASE)
            if next_match:
                next_url = next_match.group(1)
        
        if next_url:
            next_url = next_url.strip()
            if '#' in next_url:
                next_url = next_url.split('#')[0]
            
            if next_url and next_url not in ['/', '#']:
                if not next_url.startswith('http'):
                    next_url = site.url + next_url.lstrip('/')
                if next_url != search_url:
                    site.add_dir(f'[COLOR hotpink]Next Page ({next_page_num})[/COLOR]', next_url, 'Search', '')
        
        utils.eod()
    except Exception:
        pass


@site.register()
def Playvid(url='', name='', download=None):
    vp = utils.VideoPlayer(name, download)
    
    try:
        html = utils.getHtml(url, site.url)
        
        sources = []
        seen_urls = set()
        
        enc_matches = re.findall(r'<iframe[^>]*data-enc=["\']([^"\']+)["\'][^>]*>', html)
        for encoded in enc_matches:
            decoded = safe_base64_decode(encoded)
            if decoded and decoded not in seen_urls:
                seen_urls.add(decoded)
                is_prev = is_preview_url(decoded)
                label = f"External {'[PREVIEW]' if is_prev else '[FULL]'}"
                sources.append((label, decoded, is_prev))
        
        jsonld_matches = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
        for json_str in jsonld_matches:
            try:
                data = json.loads(json_str)
                items = data if isinstance(data, list) else [data]
                if isinstance(data, dict) and '@graph' in data:
                    items = data['@graph']
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'VideoObject':
                        content_url = item.get('contentUrl', '')
                        if content_url and content_url not in seen_urls and content_url.startswith('http'):
                            seen_urls.add(content_url)
                            is_prev = is_preview_url(content_url)
                            label = f"CDN {'[PREVIEW]' if is_prev else '[FULL]'}"
                            sources.append((label, content_url, is_prev))
            except:
                pass
        
        if not sources:
            utils.notify('Error', 'No video sources found')
            return
        
        full_sources = [(label, url) for label, url, is_prev in sources if not is_prev]
        preview_sources = [(label, url) for label, url, is_prev in sources if is_prev]
        
        if full_sources:
            target_sources = full_sources
        else:
            target_sources = preview_sources
            utils.notify('Warning', 'Only preview available')
        
        RESOLVEURL_AVAILABLE = False
        try:
            import resolveurl
            RESOLVEURL_AVAILABLE = True
        except:
            pass
        
        for label, vid_url in target_sources:
            try:
                if '.mp4' in vid_url or 'b-cdn.net' in vid_url:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://onlyjerk.net/',
                    }
                    header_string = '&'.join([f"{k}={urllib_parse.quote(v)}" for k, v in headers.items()])
                    final_url = f"{vid_url}|{header_string}"
                    vp.play_from_direct_link(final_url)
                    return
                
                elif RESOLVEURL_AVAILABLE:
                    if any(host in vid_url for host in ['vidara.to', 'voe.sx', 'luluvdo.com', 'streamtape', 'dood']):
                        hmf = resolveurl.HostedMediaFile(url=vid_url)
                        if hmf.valid_url():
                            resolved = hmf.resolve()
                            if resolved:
                                vp.play_from_direct_link(resolved)
                                return
                else:
                    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': url}
                    header_string = '&'.join([f"{k}={urllib_parse.quote(v)}" for k, v in headers.items()])
                    final_url = f"{vid_url}|{header_string}"
                    vp.play_from_direct_link(final_url)
                    return
                    
            except:
                continue
        
        utils.notify('Error', 'All sources failed')
                
    except:
        pass


@site.register()
def Tags(url=''):
    try:
        html = utils.getHtml(url, site.url)
        tags = re.findall(r'<a[^>]*href="[^"]*/tag/([^"/]+)/?"[^>]*class="[^"]*pill-tag[^"]*"[^>]*>([^<]+)', html)
        if tags:
            items = [f"{name} ({tag})" for tag, name in tags]
            utils.dialog.ok('Tags', '\n'.join(items[:20]))
    except:
        pass
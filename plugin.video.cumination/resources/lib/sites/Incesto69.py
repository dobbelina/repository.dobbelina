'''
    Cumination
    Copyright (C) 2024 Team Cumination

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
import xbmc
import xbmcgui
import xbmcaddon
import json
import gzip
import io
import os
import re
from six.moves import urllib_parse
from six.moves import urllib_request
from resources.lib import utils
from resources.lib.adultsite import AdultSite

addon = xbmcaddon.Addon()
site = AdultSite('incesto69', '[COLOR hotpink]Incesto69[/COLOR]', 'https://incesto69.com/', 'incesto69.png')
BASE_URL = 'https://incesto69.com'
DEFAULT_THUMB = 'https://incesto69.com/favicon.ico'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def log(msg):
    xbmc.log(f'[INCESTO69] {msg}', xbmc.LOGINFO)

def get_html(url):
    try:
        req = urllib_request.Request(url, headers=headers)
        response = urllib_request.urlopen(req, timeout=30)
        return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f'HTML Error: {str(e)}')
        return None

def get_json(url):
    try:
        response = utils.getHtml(url, BASE_URL, headers={
            'User-Agent': headers['User-Agent'],
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': BASE_URL
        })
        try:
            return json.loads(response)
        except:
            buf = io.BytesIO(response.encode('utf-8') if isinstance(response, str) else response)
            with gzip.GzipFile(fileobj=buf) as f:
                return json.loads(f.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)}

def get_thumbnail_for_slug(slug, source_hint=None):
    """Génère l'URL de vignette à partir du slug avec fallback multiple"""
    if not slug:
        return DEFAULT_THUMB
    
    if source_hint == 'milfnut':
        sources = ['milfnut', 'wp']
    elif source_hint == 'wp':
        sources = ['wp', 'milfnut']
    else:
        sources = ['wp', 'milfnut']
    
    extensions = ['.jpg', '.webp', '.png']
    
    for source in sources:
        for ext in extensions:
            thumb_url = f'https://stream.incesto69.com/thumbnails/{source}/{slug}{ext}'
            return f'{thumb_url}|Referer={urllib_parse.quote(BASE_URL)}'
    
    return DEFAULT_THUMB

def get_video_thumbnail(video):
    """Thumbnails pour les données API (Main, ListVideos, etc.)"""
    if not video:
        return DEFAULT_THUMB
    
    slug = video.get('slug', '')
    if not slug:
        return DEFAULT_THUMB
    
    cdn_url = video.get('cdnUrl', '')
    if 'milfnut' in cdn_url:
        source_hint = 'milfnut'
    elif 'wp' in cdn_url:
        source_hint = 'wp'
    else:
        source_hint = None
    
    thumb = video.get('thumbnailUrl', '')
    if thumb and thumb not in ['null', 'undefined', '']:
        thumb = thumb.replace('\\/', '/')
        if thumb.startswith('http'):
            if 'stream.incesto69.com' in thumb:
                return f'{thumb}|Referer={urllib_parse.quote(BASE_URL)}'
            return thumb
    
    thumb = video.get('previewUrl', '')
    if thumb and thumb not in ['null', 'undefined', '']:
        thumb = thumb.replace('\\/', '/')
        if thumb.startswith('http'):
            if 'stream.incesto69.com' in thumb:
                return f'{thumb}|Referer={urllib_parse.quote(BASE_URL)}'
            return thumb
    
    return get_thumbnail_for_slug(slug, source_hint)

def get_local_thumb(slug):
    """Télécharge le thumbnail localement si les headers posent problème"""
    if not slug:
        return DEFAULT_THUMB
    
    cache_dir = os.path.join(utils.profileDir, 'thumbs_cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_file = os.path.join(cache_dir, f'{slug}.jpg')
    
    if os.path.exists(cache_file):
        return cache_file
    
    for source in ['wp', 'milfnut']:
        thumb_url = f'https://stream.incesto69.com/thumbnails/{source}/{slug}.jpg'
        try:
            req = urllib_request.Request(thumb_url, headers={
                'User-Agent': headers['User-Agent'],
                'Referer': BASE_URL
            })
            response = urllib_request.urlopen(req, timeout=10)
            with open(cache_file, 'wb') as f:
                f.write(response.read())
            return cache_file
        except:
            continue
    
    return DEFAULT_THUMB

@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', f'{BASE_URL}/api/categories', 'incesto69.ListCategories', '')
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', f'{BASE_URL}/pornstars', 'incesto69.ListPornstars', '')
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', f'{BASE_URL}/channels', 'incesto69.ListChannels', '')
    site.add_dir('[COLOR yellow]Search[/COLOR]', f'{BASE_URL}/search?q=', 'incesto69.Search', '')
    
    try:
        url = f'{BASE_URL}/api/videos?sort=newest'
        data = get_json(url)
        
        if data and 'error' not in data and data.get('data'):
            videos = data.get('data', [])
            next_cursor = data.get('nextCursor')
            has_more = data.get('hasMore', False)
            view_counts = data.get('viewCounts', {})
            
            for video in videos:
                title = video.get('title', 'Unknown')
                video_id = video.get('id', '')
                thumb = get_video_thumbnail(video)
                duration = video.get('duration', 0)
                views = view_counts.get(str(video_id), video.get('views', 0))
                cdn_url = video.get('cdnUrl', '')
                
                duration_str = ''
                if duration:
                    mins = int(duration) // 60
                    secs = int(duration) % 60
                    duration_str = f'{mins}:{secs:02d}'
                
                site.add_download_link(title, cdn_url, 'incesto69.PlayVideo', thumb, 
                                      f'Views: {views}', duration=duration_str)
            
            if has_more and next_cursor:
                if '?' in url:
                    base = url.split('?')[0]
                    params = url.split('?')[1].split('&')
                    new_params = [p for p in params if not p.startswith('cursor=')]
                    next_url = base + '?' + '&'.join(new_params) + f'&cursor={next_cursor}'
                else:
                    next_url = f'{url}&cursor={next_cursor}'
                site.add_dir('[COLOR hotpink]Next Page >>[/COLOR]', next_url, 'incesto69.ListVideos', '', '2')
    except Exception as e:
        log(f'Error loading latest videos: {str(e)}')
    
    utils.eod()

@site.register()
def ListVideos(url, page=1):
    log(f'ListVideos: {url}')
    
    data = get_json(url)
    
    if 'error' in data:
        utils.notify('Error', data['error'])
        utils.eod()
        return
    
    videos = data.get('data', [])
    next_cursor = data.get('nextCursor')
    has_more = data.get('hasMore', False)
    view_counts = data.get('viewCounts', {})
    
    log(f'Videos: {len(videos)}, hasMore: {has_more}')
    
    for video in videos:
        title = video.get('title', 'Unknown')
        video_id = video.get('id', '')
        thumb = get_video_thumbnail(video)
        fanart = thumb
        duration = video.get('duration', 0)
        views = view_counts.get(str(video_id), video.get('views', 0))
        cdn_url = video.get('cdnUrl', '')
        
        duration_str = ''
        if duration:
            mins = int(duration) // 60
            secs = int(duration) % 60
            duration_str = f'{mins}:{secs:02d}'
        
        site.add_download_link(title, cdn_url, 'incesto69.PlayVideo', thumb, 
                              f'Views: {views}', duration=duration_str, fanart=fanart)
    
    if has_more and next_cursor:
        if '?' in url:
            base = url.split('?')[0]
            params = url.split('?')[1].split('&')
            new_params = [p for p in params if not p.startswith('cursor=')]
            next_url = base + '?' + '&'.join(new_params) + f'&cursor={next_cursor}'
        else:
            next_url = f'{url}&cursor={next_cursor}'
        
        log(f'Next: {next_url}')
        site.add_dir('[COLOR hotpink]Next Page >>[/COLOR]', next_url, 'incesto69.ListVideos', '', str(int(page) + 1))
    
    utils.eod()

@site.register()
def ListCategories(url):
    data = get_json(url)
    
    if isinstance(data, list):
        categories = data
    elif isinstance(data, dict) and 'data' in data:
        categories = data['data']
    else:
        utils.notify('Error', 'No categories')
        utils.eod()
        return
    
    for cat in categories:
        name = cat.get('name', 'Unknown')
        slug = cat.get('slug', '')
        thumb = cat.get('thumbnailUrl', '') or DEFAULT_THUMB
        count = cat.get('videoCount', 0)
        
        cat_url = f'{BASE_URL}/api/videos?category={slug}&sort=newest'
        site.add_dir(f'{name} [{count}]', cat_url, 'incesto69.ListVideos', thumb, '1')
    
    utils.eod()

@site.register()
def ListPornstars(url):
    log(f'Pornstars: {url}')
    
    html = get_html(url)
    if not html:
        utils.notify('Error', 'Cannot load HTML')
        utils.eod()
        return
    
    # Pattern amélioré avec thumbnail
    pattern = r'<a[^>]+href="/pornstar/([a-z0-9-]+)"[^>]*>.*?<img[^>]+src="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>.*?<span[^>]*>(\d+)'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    if not matches:
        # Fallback sans nombre mais avec thumbnail
        pattern = r'<a[^>]+href="/pornstar/([a-z0-9-]+)"[^>]*>.*?<img[^>]+src="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        seen = set()
        for match in matches:
            if len(match) >= 3:
                slug, img_url, name = match[0], match[1], match[2]
            else:
                slug, img_url = match[0], ''
                name = slug.replace('-', ' ').title()
            
            if slug not in seen:
                seen.add(slug)
                
                # Fix URL image
                if img_url:
                    img_url = img_url.replace('\\/', '/')
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = BASE_URL + img_url
                
                star_url = f'{BASE_URL}/api/videos?pornstar={slug}&sort=newest'
                site.add_dir(name, star_url, 'incesto69.ListVideos', img_url or DEFAULT_THUMB, '1')
        utils.eod()
        return
    
    seen = set()
    for slug, img_url, name, count in matches:
        if slug and slug not in seen:
            seen.add(slug)
            name = name.strip()
            display_name = f'{name} [COLOR hotpink]({count})[/COLOR]'
            
            # Fix URL image
            if img_url:
                img_url = img_url.replace('\\/', '/')
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = BASE_URL + img_url
            
            star_url = f'{BASE_URL}/api/videos?pornstar={slug}&sort=newest'
            site.add_dir(display_name, star_url, 'incesto69.ListVideos', img_url or DEFAULT_THUMB, '1')
    
    utils.eod()

@site.register()
def ListChannels(url):
    log(f'Channels: {url}')
    
    html = get_html(url)
    if not html:
        utils.notify('Error', 'Cannot load HTML')
        utils.eod()
        return
    
    # Pattern avec image, nom et count
    pattern = r'<a[^>]+href="/channel/([a-z0-9-]+)"[^>]*>.*?<img[^>]+src="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>.*?<span[^>]*>(\d+)'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    if not matches:
        # Fallback sans count mais avec thumbnail
        pattern = r'<a[^>]+href="/channel/([a-z0-9-]+)"[^>]*>.*?<img[^>]+src="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        seen = set()
        for match in matches:
            if len(match) >= 3:
                slug, img_url, name = match[0], match[1], match[2]
            else:
                slug, img_url = match[0], ''
                name = slug.replace('-', ' ').title()
            
            if slug not in seen:
                seen.add(slug)
                
                # Fix URL image
                if img_url:
                    img_url = img_url.replace('\\/', '/')
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = BASE_URL + img_url
                
                chan_url = f'{BASE_URL}/api/videos?channel={slug}&sort=newest'
                site.add_dir(name, chan_url, 'incesto69.ListVideos', img_url or DEFAULT_THUMB, '1')
        utils.eod()
        return
    
    seen = set()
    for slug, img_url, name, count in matches:
        if slug and slug not in seen:
            seen.add(slug)
            name = name.strip()
            display_name = f'{name} [COLOR hotpink]({count})[/COLOR]'
            
            # Fix URL image
            if img_url:
                img_url = img_url.replace('\\/', '/')
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = BASE_URL + img_url
            
            chan_url = f'{BASE_URL}/api/videos?channel={slug}&sort=newest'
            site.add_dir(display_name, chan_url, 'incesto69.ListVideos', img_url or DEFAULT_THUMB, '1')
    
    utils.eod()

@site.register()
def Search(url, keyword=None):
    """Recherche avec thumbnails corrigés"""
    if not keyword:
        site.search_dir(url, 'incesto69.Search')
    else:
        try:
            search_url = f'{BASE_URL}/search?q={urllib_parse.quote_plus(keyword)}'
            log(f'Search URL: {search_url}')
            
            html = get_html(search_url)
            if not html:
                utils.notify('Error', 'Search failed')
                utils.eod()
                return
            
            # Nettoyer le HTML des backslashes échappés
            html_clean = html.replace('\\/', '/')
            
            videos = []
            seen = set()
            
            # Pattern amélioré pour capturer thumbnail et titre
            pattern = r'<a[^>]+href="/([a-z0-9-]{10,})"[^>]*>.*?<img[^>]+(?:data-image|src)="([^"]*)"[^>]*(?:alt="([^"]*)")?[^>]*>.*?(?:<span[^>]*>(\d+:\d+)</span>)?'
            matches = re.findall(pattern, html_clean, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                slug = match[0]
                thumb_url = match[1]
                alt_text = match[2] if len(match) > 2 and match[2] else ''
                duration = match[3] if len(match) > 3 and match[3] else ''
                
                # Filtrer les slugs invalides
                if slug in seen or any(x in slug for x in ['search', 'videos', 'categories', 'pornstars', 'channels', 'terms', 'privacy', 'api', 'about']):
                    continue
                if len(slug) < 5:
                    continue
                
                seen.add(slug)
                
                # Extraire le titre
                title = alt_text if alt_text else slug.replace('-', ' ').title()
                
                # Construire l'URL de la vignette
                if thumb_url and 'incesto69.com' in thumb_url:
                    if thumb_url.startswith('//'):
                        thumb_url = 'https:' + thumb_url
                    if 'stream.incesto69.com' in thumb_url:
                        thumb_url = f'{thumb_url}|Referer={BASE_URL}'
                else:
                    thumb_url = get_thumbnail_for_slug(slug)
                
                page_url = f'{BASE_URL}/{slug}'
                
                videos.append({
                    'title': title.strip(),
                    'url': page_url,
                    'thumb': thumb_url,
                    'duration': duration,
                    'slug': slug
                })
            
            log(f'Found {len(videos)} videos')
            
            if not videos:
                site.add_dir('[COLOR red]No results found[/COLOR]', '', '', '')
            else:
                for v in videos:
                    site.add_download_link(
                        v['title'], 
                        v['url'],
                        'incesto69.PlayVideo', 
                        v['thumb'], 
                        '', 
                        duration=v['duration']
                    )
                    
        except Exception as e:
            log(f'Search error: {e}')
            import traceback
            log(traceback.format_exc())
            utils.notify('Error', f'Search failed: {str(e)}')
        
        utils.eod()

@site.register()
def PlayVideo(url, name, download=None):
    """Lecture de la vidéo - gère les différents formats d'URL"""
    try:
        log(f'PlayVideo called: {url}')
        
        # Si c'est déjà un lien direct .mp4 avec le bon format
        if '.mp4' in url and url.startswith('http'):
            if '/videos/' in url:
                log(f'Full MP4 URL: {url}')
                utils.playvid(url, name, download)
                return
            log(f'Trying direct MP4: {url}')
            utils.playvid(url, name, download)
            return
        
        # Extraire le slug de l'URL
        slug = url.rstrip('/').split('/')[-1]
        log(f'Slug: {slug}')
        
        # Méthode 1: Essayer différents formats d'URL
        possible_urls = [
            f'https://stream.incesto69.com/videos/milfnut/{slug}.mp4',
            f'https://stream.incesto69.com/videos/wp/{slug}.mp4',
            f'https://stream.incesto69.com/{slug}.mp4',
        ]
        
        for test_url in possible_urls:
            try:
                log(f'Testing URL: {test_url}')
                req = urllib_request.Request(test_url, headers=headers, method='HEAD')
                response = urllib_request.urlopen(req, timeout=10)
                if response.getcode() in [200, 206]:
                    log(f'URL works: {test_url}')
                    utils.playvid(test_url, name, download)
                    return
            except Exception as e:
                log(f'URL failed: {e}')
                continue
        
        # Méthode 2: Extraire du HTML de la page
        log(f'Fetching HTML: {url}')
        html = get_html(url)
        
        if html:
            # Chercher le tag video
            video_match = re.search(r'<video[^>]+src="([^"]+)"', html)
            if video_match:
                video_url = video_match.group(1)
                log(f'Found video in tag: {video_url}')
                utils.playvid(video_url, name, download)
                return
            
            # Chercher la source
            source_match = re.search(r'<source[^>]+src="([^"]+)"[^>]+type="video/mp4"', html)
            if source_match:
                video_url = source_match.group(1)
                log(f'Found source: {video_url}')
                utils.playvid(video_url, name, download)
                return
            
            # Chercher n'importe quel URL .mp4 avec /videos/
            mp4_match = re.search(r'(https?://stream\.incesto69\.com/videos/[^"\']+\.mp4)', html)
            if mp4_match:
                video_url = mp4_match.group(1)
                log(f'Found MP4 in HTML: {video_url}')
                utils.playvid(video_url, name, download)
                return
        
        log('No video URL found')
        utils.notify('Error', 'Video URL not found')
            
    except Exception as e:
        log(f'PlayVideo error: {e}')
        import traceback
        log(traceback.format_exc())
        utils.notify('Error', f'Playback failed: {str(e)}')
"""
Cumination
Copyright (C) 2026 Team Cumination

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

site = AdultSite(
    "pimpbunny",
    "[COLOR hotpink]PimpBunny[/COLOR]",
    "https://pimpbunny.com/",
    "https://pimpbunny.com/static/images/logo.png",
    "pimpbunny",
)

@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Search[/COLOR]", site.url + "search/videos/", "Search", site.img_search)
    site.add_dir("[COLOR hotpink]Categories[/COLOR]", site.url + "categories/videos/", "Categories", site.img_cat)
    site.add_dir("[COLOR hotpink]Most Viewed[/COLOR]", site.url + "videos/?sort_by=video_viewed", "List", site.img_cat)
    site.add_dir("[COLOR hotpink]Best Rated[/COLOR]", site.url + "videos/?sort_by=rating", "List", site.img_cat)
    
    # List latest videos directly on main screen
    List(site.url + "videos/")

@site.register()
def List(url):
    html, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    
    # Cards have class ui-card-video__Iv9u1W or similar
    cards = soup.select('[class*="card-video"]')
    for card in cards:
        link_tag = card.select_one('a[href*="/videos/"]')
        if not link_tag:
            continue
            
        videopage = link_tag.get('href')
        if not videopage.startswith('http'):
            videopage = urllib_parse.urljoin(site.url, videopage)
            
        title_tag = card.select_one('[class*="title"]')
        name = utils.safe_get_text(title_tag)
        if not name:
            name = link_tag.get('title') or "Video"
            
        img_tag = card.select_one('img')
        img = utils.get_thumbnail(img_tag)
        if img:
            if not img.startswith('http'):
                img = urllib_parse.urljoin(site.url, img)
            # Add session headers (UA/Cookies) for thumbnails
            img = utils.get_kodi_url(img, referer=url)
            
        duration_tag = card.select_one('[class*="duration"]')
        duration = utils.safe_get_text(duration_tag)
        
        site.add_download_link(name, videopage, "Playvid", img, name, duration=duration)

    # Pagination
    next_link = soup.select_one('a[class*="pagination-next"], a[rel="next"]')
    if next_link:
        next_url = next_link.get('href')
        if next_url:
            next_url = urllib_parse.urljoin(site.url, next_url)
            site.add_dir("Next Page", next_url, "List", site.img_next)

    utils.eod()

@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    html, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    if not html:
        return

    # Extract MP4 links with qualities
    # Example pattern from analysis: https://pimpbunny.com/get_file/33/.../525991_1080p.mp4/
    links = re.findall(r'https?://[^\s"\'<>]+(?:\.mp4)[^\s"\'<>]*', html)
    
    # Clean up links (remove trailing slashes if they interfere)
    links = list(set(links))
    
    # Filter out preview images and other junk
    video_links = [l for l in links if '/get_file/' in l]
    
    if not video_links:
        # Fallback to direct page scraping for video tag
        soup = utils.parse_html(html)
        video_tag = soup.select_one('video')
        if video_tag and video_tag.get('src'):
            video_links.append(video_tag.get('src'))
            
    if video_links:
        # Quality mapping
        qualities = []
        for l in video_links:
            q = 0
            if '2160p' in l: q = 2160
            elif '1440p' in l: q = 1440
            elif '1080p' in l: q = 1080
            elif '720p' in l: q = 720
            elif '480p' in l: q = 480
            elif '360p' in l: q = 360
            qualities.append((q, l))
            
        # Sort by quality descending
        qualities.sort(key=lambda x: x[0], reverse=True)
        best_link = qualities[0][1]
        
        # Add session headers (UA/Cookies) and referer for video playback
        best_link = utils.get_kodi_url(best_link, referer=url)
        vp.play_from_direct_link(best_link)
    else:
        utils.notify("PimpBunny", "Could not find video link")

@site.register()
def Categories(url):
    html, _ = utils.get_html_with_cloudflare_retry(url, referer=site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    # Categories usually have class ui-card-category__...
    cats = soup.select('[class*="card-category"]')
    for cat in cats:
        link_tag = cat.select_one('a[href]')
        if not link_tag:
            continue
            
        cat_url = link_tag.get('href')
        if not cat_url.startswith('http'):
            cat_url = urllib_parse.urljoin(site.url, cat_url)
            
        title_tag = cat.select_one('[class*="title"]')
        name = utils.safe_get_text(title_tag)
        
        img_tag = cat.select_one('img')
        img = utils.get_thumbnail(img_tag)
        if img:
            if not img.startswith('http'):
                img = urllib_parse.urljoin(site.url, img)
            # Add session headers (UA/Cookies) for category thumbnails
            img = utils.get_kodi_url(img, referer=url)
            
        site.add_dir(name, cat_url, "List", img)
        
    utils.eod()

@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # PimpBunny search URL format: /search/videos/?q=keyword
        search_url = site.url + "search/videos/?q=" + keyword.replace(" ", "+")
        List(search_url)

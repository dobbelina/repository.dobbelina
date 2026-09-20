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

import re
import html
import time
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('avjoy', '[COLOR hotpink]Avjoy[/COLOR]', 'https://en.avjoy.me/', 'https://en.avjoy.me/static/images/logo.png', 'avjoy')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/videos/', 'Search', site.img_search)
    List(site.url + 'videos?o=mr')


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, site.url)
    except Exception:
        return None

    delimiter = '<div class="col-'
    re_videopage = r'<a\s+href="(/video/[^"]+)"'
    re_name = r'img[^>]+title="([^"]+)"'
    re_img = r'img[^>]+src="([^"]+)"'
    # Correction: capture la durée après le span HD ou directement
    re_duration = r'<div class="duration">(?:\s*<span[^>]*>[^<]*</span>)?\s*([^<\s][^<]*)'

    utils.videos_list(site, 'avjoy.Playvid', listhtml, delimiter, re_videopage, re_name, re_img, re_duration=re_duration)

    np_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*prevnext[^"]*"[^>]*>[^<]*<i[^>]*fa-caret-right', listhtml, re.IGNORECASE)
    if np_match:
        npurl = urllib_parse.urljoin(site.url, np_match.group(1))
        page_match = re.search(r'page=(\d+)', npurl)
        page_num = page_match.group(1) if page_match else '?'
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({})'.format(page_num), npurl, 'List', site.img_next)
    
    utils.eod()


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, site.url)
    except Exception:
        utils.eod()
        return

    main_section = re.search(r'<h1>Categories</h1>(.*?)</div>\s*</div>\s*</div>\s*<div class="footer-container', cathtml, re.DOTALL | re.IGNORECASE)
    if main_section:
        cathtml = main_section.group(1)
    
    pattern = r'<a href="(/videos/[^"]+)">\s*<div class="thumb-overlay">\s*<img src="([^"]+)"[^>]+title="([^"]+)".*?<div class="category-title">\s*<div[^>]*>([^<]+)</div>\s*<div[^>]*>([^<]+)</div>'
    match = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(cathtml)
    
    seen = {}
    for catpage, thumb, img_title, name, count in match:
        if catpage not in seen:
            seen[catpage] = True
            name = utils.cleantext(html.unescape(name.strip()))
            if count:
                name += ' [COLOR hotpink]({})[/COLOR]'.format(count.strip())
            caturl = urllib_parse.urljoin(site.url, catpage)
            imgurl = urllib_parse.urljoin(site.url, thumb)
            site.add_dir(name, caturl, 'List', imgurl)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        searchUrl = url + keyword.replace(' ', '-')
        List(searchUrl)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    headers = {'Referer': site.url}
    videohtml = utils.getHtml(url, site.url, headers=headers)
    
    sources = {}
    for source_match in re.finditer(r'<source\b[^>]+>', videohtml, re.IGNORECASE):
        tag = source_match.group(0)
        src_match = re.search(r'src=[\'"]([^\'"]+)[\'"]', tag, re.IGNORECASE)
        if not src_match:
            continue
        src = html.unescape(src_match.group(1).strip())
        if '.mp4' not in src:
            continue
        
        res_match = re.search(r'(?:res|label|quality)=[\'"]([^\'"]+)[\'"]', tag, re.IGNORECASE)
        quality = res_match.group(1) if res_match else 'SD'
        
        quality_str = re.sub(r'\D', '', quality) if re.search(r'\d', quality) else quality
        if quality_str.isdigit():
            quality_str = quality_str + 'p'
        
        sources[quality_str] = urllib_parse.urljoin(site.url, src)
    
    if not sources:
        utils.notify('Oh oh', 'No video found')
        vp.progress.close()
        return
    
    valid_sources = {}
    for quality, stream_url in sources.items():
        if not _is_stream_expired(stream_url):
            valid_sources[quality] = stream_url
    
    if not valid_sources:
        utils.notify('Oh oh', 'Video link expired')
        vp.progress.close()
        return
    
    if len(valid_sources) == 1:
        videourl = list(valid_sources.values())[0]
    else:
        videourl = utils.prefquality(valid_sources, sort_by=lambda x: int(re.sub(r'\D', '', x)) if re.search(r'\d', x) else 0, reverse=True)
    
    if not videourl:
        vp.progress.close()
        return
    
    play_headers = {
        'User-Agent': utils.USER_AGENT,
        'Referer': url,
        'Origin': site.url
    }
    
    header_string = urllib_parse.urlencode(play_headers)
    videourl = f"{videourl}|{header_string}"
    
    vp.progress.update(90, "[CR]Playing video[CR]")
    vp.play_from_direct_link(videourl)


def _is_stream_expired(stream_url):
    if not stream_url:
        return True
    
    for param in ('expires', 'expire', 'e'):
        m = re.search(rf'[?&]{param}=(\d+)', stream_url, re.IGNORECASE)
        if m:
            try:
                expires_ts = int(m.group(1))
                if time.time() + 60 > expires_ts:
                    return True
            except Exception:
                pass
    
    path_expiry = re.search(r'/video/[^/]+/(\d{10})/[^/]+\.mp4', stream_url)
    if path_expiry:
        try:
            expires_ts = int(path_expiry.group(1))
            if time.time() + 60 > expires_ts:
                return True
        except Exception:
            pass
    
    return False
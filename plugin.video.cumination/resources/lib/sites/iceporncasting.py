# -*- coding: utf-8 -*-
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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('iceporncasting', '[COLOR hotpink]IcePornCasting[/COLOR]', 'https://iceporncasting.net/', 'iceporncasting.png')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + '1f/channels/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'latest-casting-videos/')


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, site.url)
    except Exception as e:
        utils.kodilog('IcePornCasting: Error loading page {0} - {1}'.format(url, str(e)), 2)
        return None

    if 'Nothing found' in listhtml or 'search-no-results' in listhtml:
        utils.notify('Search', 'No results found')
        utils.eod()
        return

    articles = re.findall(
        r'<article[^>]*class="[^"]*thumb-block[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]+)".*?<img[^>]+src="([^"]+)".*?<span[^>]*class="[^"]*duration[^"]*"[^>]*>(?:<i[^>]*>[^<]*</i>)?\s*([^<]+)</span>.*?</article>',
        listhtml, re.DOTALL | re.IGNORECASE
    )

    if not articles:
        articles = re.findall(
            r'<article[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]+)".*?<img[^>]+src="([^"]+)".*?</article>',
            listhtml, re.DOTALL | re.IGNORECASE
        )
        articles = [(a, b, c, '') for a, b, c in articles]

    if not articles:
        utils.notify('Info', 'No videos found')
        utils.eod()
        return

    for videopage, name, img, duration in articles:
        name = utils.cleantext(name.strip())
        duration = duration.strip() if duration else ''
        
        if duration:
            name = '{0} [COLOR hotpink]{1}[/COLOR]'.format(name, duration)
        
        contextmenu = []
        contexturl = (utils.addon_sys + "?mode=iceporncasting.Lookupinfo" + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))
        
        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    np_match = re.search(r'<a[^>]+class="[^"]*next[^"]*"[^>]*href="([^"]+)"', listhtml, re.DOTALL | re.IGNORECASE)
    if not np_match:
        np_match = re.search(r'<a[^>]+href="([^"]*/page/\d+/)"[^>]*>Next</a>', listhtml, re.DOTALL | re.IGNORECASE)
    if not np_match:
        np_match = re.search(r'<a[^>]+href="([^"]*page/\d+/\?s=[^"]*)"[^>]*>Next</a>', listhtml, re.DOTALL | re.IGNORECASE)
    
    if np_match:
        npurl = np_match.group(1)
        if not npurl.startswith('http'):
            npurl = site.url + npurl.lstrip('/')
        site.add_dir('Next Page...', npurl, 'List', site.img_next)
    
    utils.eod()


@site.register()
def Pornstars(url):
    try:
        html = utils.getHtml(url, site.url)
    except Exception as e:
        utils.kodilog('IcePornCasting: Error loading pornstars - {0}'.format(str(e)), 2)
        return None
    
    match = re.findall(
        r'<article[^>]*class="[^"]*thumb-block[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]+)".*?<img[^>]+src="([^"]+)".*?</article>',
        html, re.DOTALL | re.IGNORECASE
    )
    
    if not match:
        match = re.findall(
            r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*pornstar[^"]*"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>',
            html, re.DOTALL | re.IGNORECASE
        )
        match = [(a, c, b) for a, b, c in match]

    seen = set()
    for psurl, name, img in match:
        name = name.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        name = utils.cleantext(name)
        if not psurl.startswith('http'):
            psurl = site.url + psurl.lstrip('/')
        site.add_dir(name, psurl, 'List', img if img else site.img_cat)

    if not seen:
        utils.notify('Info', 'No pornstars found')
        
    np_match = re.search(r'<a[^>]+class="[^"]*next[^"]*"[^>]*href="([^"]+)"', html, re.DOTALL | re.IGNORECASE)
    if np_match:
        npurl = np_match.group(1)
        if not npurl.startswith('http'):
            npurl = site.url + npurl.lstrip('/')
        site.add_dir('Next Page...', npurl, 'Pornstars', site.img_next)
        
    utils.eod()


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, site.url)
    except Exception as e:
        utils.kodilog('IcePornCasting: Error loading categories - {0}'.format(str(e)), 2)
        return None
    
    match = re.compile(
        r'<article[^>]*class="[^"]*thumb-block[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]+)".*?<span[^>]*class="[^"]*cat-title[^"]*"[^>]*>([^<]+)</span>.*?</article>',
        re.DOTALL | re.IGNORECASE
    ).findall(cathtml)
    
    if not match:
        match = re.compile(
            r'<article[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*title="([^"]+)".*?<span[^>]*class="[^"]*cat-title[^"]*"[^>]*>([^<]+)</span>.*?</article>',
            re.DOTALL | re.IGNORECASE
        ).findall(cathtml)

    seen = set()
    for caturl, title, name in match:
        caturl = caturl.strip()
        name = name.strip()
        
        if not name or len(name) < 2:
            continue
        if caturl in seen:
            continue
        if re.search(r'-\d+/$', caturl) and '/channel/' not in caturl and '/casting-channel/' not in caturl:
            continue
        seen.add(caturl)
        
        name = utils.cleantext(name)
        if not caturl.startswith('http'):
            caturl = site.url + caturl.lstrip('/')
        site.add_dir(name, caturl, 'List', site.img_cat)

    if not seen:
        utils.notify('Info', 'No categories found')
        
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        search_url = url + urllib_parse.quote_plus(keyword)
        List(search_url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    
    try:
        videohtml = utils.getHtml(url, site.url)
    except Exception as e:
        utils.notify('Oh oh', 'Could not load video page')
        utils.kodilog('IcePornCasting: Error loading video page - {0}'.format(str(e)), 2)
        return
    
    mirrors = []
    
    iframe_pattern = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', videohtml, re.DOTALL | re.IGNORECASE)
    for iframe_url in iframe_pattern:
        if iframe_url.startswith('//'):
            iframe_url = 'https:' + iframe_url
        elif iframe_url.startswith('/'):
            iframe_url = site.url.rstrip('/') + iframe_url
        if iframe_url not in mirrors:
            mirrors.append(iframe_url)
    
    embed_match = re.search(r'<meta[^>]+itemprop=["\']embedUrl["\'][^>]+content=["\']([^"\']+)["\']', videohtml, re.DOTALL | re.IGNORECASE)
    if embed_match:
        embed_url = embed_match.group(1)
        if embed_url.startswith('//'):
            embed_url = 'https:' + embed_url
        if embed_url not in mirrors:
            mirrors.append(embed_url)

    if not mirrors:
        utils.notify('Oh oh', 'No video found')
        return

    for mirror in mirrors[:]:
        if 'xvideos.com' in mirror:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://www.xvideos.com/',
                    'Origin': 'https://www.xvideos.com'
                }
                embed_html = utils.getHtml(mirror, url, headers=headers)
                
                video_urls = []
                quality_pattern = re.findall(r'(https?://[^"\']+\.xvideos-cdn\.com[^"\']+video_(\d+)p\.mp4[^"\']*)', embed_html, re.IGNORECASE)
                for vid_url, quality in quality_pattern:
                    video_urls.append((int(quality), vid_url))
                
                if video_urls:
                    video_urls.sort(key=lambda x: x[0], reverse=True)
                    best_quality, best_url = video_urls[0]
                    
                    header_str = '|'.join(['{0}={1}'.format(k, urllib_parse.quote(v, safe='')) for k, v in headers.items()])
                    full_url = '{0}|{1}'.format(best_url, header_str)
                    
                    vp.play_from_direct_link(full_url)
                    return
                else:
                    mp4_fallback = re.findall(r'(https?://[^"\']+\.mp4[^"\']*)', embed_html, re.IGNORECASE)
                    if mp4_fallback:
                        header_str = '|'.join(['{0}={1}'.format(k, urllib_parse.quote(v, safe='')) for k, v in headers.items()])
                        full_url = '{0}|{1}'.format(mp4_fallback[0], header_str)
                        vp.play_from_direct_link(full_url)
                        return
                        
            except Exception as e:
                utils.kodilog('IcePornCasting: XVideos extraction error - {0}'.format(str(e)), 2)
    
    for mirror in mirrors[:]:
        if 'lulust.com' in mirror or 'lulustream' in mirror or 'luluvdo' in mirror:
            try:
                utils.kodilog('IcePornCasting: Resolving lulust/luluvdo - {0}'.format(mirror), 0)
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': url,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                embed_html = utils.getHtml(mirror, url, headers=headers)
                
                sources = re.findall(r'sources:\s*\[\s*\{[^}]*file:\s*["\']([^"\']+)["\'][^}]*label:\s*["\'](\d+p?)["\']', embed_html, re.IGNORECASE)
                
                if not sources:
                    sources = re.findall(r'(?:file|src):\s*["\'](https?://[^"\']+\.(?:mp4|m3u8)[^"\']*)["\']', embed_html, re.IGNORECASE)
                    sources = [(s, 'auto') for s in sources]
                
                if not sources:
                    video_match = re.search(r'<video[^>]+src=["\']([^"\']+)["\']', embed_html, re.IGNORECASE)
                    if video_match:
                        sources = [(video_match.group(1), 'auto')]
                
                if sources:
                    if len(sources) > 1 and isinstance(sources[0], tuple):
                        def get_quality(item):
                            try:
                                return int(item[1].replace('p', ''))
                            except:
                                return 0
                        sources.sort(key=get_quality, reverse=True)
                        video_url = sources[0][0]
                    else:
                        video_url = sources[0][0] if isinstance(sources[0], tuple) else sources[0]
                    
                    header_str = '|'.join(['{0}={1}'.format(k, urllib_parse.quote(v, safe='')) for k, v in headers.items()])
                    full_url = '{0}|{1}'.format(video_url, header_str)
                    
                    vp.play_from_direct_link(full_url)
                    return
                    
            except Exception as e:
                utils.kodilog('IcePornCasting: Lulust error - {0}'.format(str(e)), 2)
    
    vp.play_from_link_list(mirrors)


@site.register()
def Lookupinfo(url):
    try:
        html = utils.getHtml(url, site.url)
    except:
        return
        
    lookup_list = [
        ("Cat", r'<a[^>]+href="([^"]+/casting-channel/[^"]+)"[^>]*>([^<]+)<', ''),
        ("Tag", r'<a[^>]+href="([^"]+/tag/[^"]+)"[^>]*>([^<]+)<', ''),
    ]
    
    lookupinfo = utils.LookupInfo(site.url, url, 'iceporncasting.List', lookup_list)
    lookupinfo.getinfo()
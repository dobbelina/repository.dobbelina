"""
Cumination site scraper for Pornditt
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
    "pornditt",
    "[COLOR hotpink]Pornditt[/COLOR]",
    "https://pornditt.com/",
    "pornditt.png",
    "pornditt",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        "{0}categories/".format(site.url),
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]",
        "{0}models/".format(site.url),
        "Pornstars",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        "{0}search/".format(site.url),
        "Search",
        site.img_search,
    )
    List("{0}latest-updates/".format(site.url))


@site.register()
def Categories(url):
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    
    # KVS categories structure
    try:
        items = soup.select('.list-categories .item')
    except Exception as e:
        utils.kodilog("pornditt Categories select error: {}".format(e))
        items = []

    for item in items:
        try:
            cat_url = utils.safe_get_attr(item, "href")
            if not cat_url:
                continue
            
            name_tag = item.select_one('.title')
            name = utils.safe_get_text(name_tag, default="").strip()
            
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, "src")
            
            if name and cat_url:
                site.add_dir(name, cat_url, "List", img)
        except Exception as e:
            utils.kodilog("pornditt Categories error: {}".format(e))
            continue
            
    utils.eod()


@site.register()
def Pornstars(url):
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    
    try:
        items = soup.select('.list-models .item')
    except Exception as e:
        utils.kodilog("pornditt Pornstars select error: {}".format(e))
        items = []

    for item in items:
        try:
            model_url = utils.safe_get_attr(item, "href")
            if not model_url:
                continue
            
            name_tag = item.select_one('.title')
            name = utils.safe_get_text(name_tag, default="").strip()
            
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, "src")
            
            if name and model_url:
                site.add_dir(name, model_url, "List", img)
        except Exception as e:
            utils.kodilog("pornditt Pornstars error: {}".format(e))
            continue
            
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    
    try:
        items = soup.select('.list-videos .item')
    except Exception as e:
        utils.kodilog("pornditt List select error: {}".format(e))
        items = []

    for item in items:
        try:
            link = item.select_one('a[href]')
            if not link:
                continue
                
            videopage = utils.safe_get_attr(link, "href")
            title = utils.safe_get_attr(link, "title")
            
            img_tag = link.select_one('img')
            img = utils.safe_get_attr(img_tag, "data-original", ["src"])
            
            duration_tag = item.select_one('.duration')
            duration = utils.safe_get_text(duration_tag, default="").strip()
            
            quality_tag = item.select_one('.is-hd')
            quality = "HD" if quality_tag else ""
            
            if videopage and title:
                site.add_download_link(
                    title, videopage, "Playvid", img, title, duration=duration, quality=quality
                )
        except Exception as e:
            utils.kodilog("pornditt List error: {}".format(e))
            continue
            
    # Pagination
    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a')
        if next_link:
            next_url = utils.safe_get_attr(next_link, "href")
            if next_url:
                if not next_url.startswith('http'):
                    next_url = urllib_parse.urljoin(site.url, next_url)
                
                # Try to find current and last page
                curr_pg = "1"
                curr_tag = pagination.select_one('li.page-current span')
                if curr_tag:
                    curr_pg = utils.safe_get_text(curr_tag).strip()
                
                last_pg = ""
                last_tag = pagination.select_one('li.last a')
                if last_tag:
                    last_url = utils.safe_get_attr(last_tag, "href")
                    match = re.search(r'/(\d+)/$', last_url)
                    if match:
                        last_pg = match.group(1)
                
                label = "Next Page..."
                if curr_pg and last_pg:
                    label = "Next Page... ({}/{})".format(curr_pg, last_pg)
                
                site.add_dir(label, next_url, "List", site.img_next)
                
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    html = utils.getHtml(url, site.url)
    
    # Extract license_code for KVS decoding
    license_code = ""
    match_lc = re.search(r"license_code: '([^']+)'", html)
    if match_lc:
        license_code = match_lc.group(1)

    # Try to find video_url in scripts
    sources = {}
    
    # Extract multiple qualities if available
    matches = re.findall(r"video(?:_alt_|_)url(?:[0-9]|): '([^']+)',.*?video(?:_alt_|_)url(?:[0-9]|)_text: '([^']+)'", html, re.DOTALL)
    if matches:
        for src, label in matches:
            if src.startswith('function/') and license_code:
                from resources.lib.decrypters.kvsplayer import kvs_decode
                src = kvs_decode(src, license_code)
            elif src.startswith('function/'):
                src = src.split('function/0/')[-1]
            sources[label] = src
    else:
        # Fallback to single video_url
        match = re.search(r"video_url: '([^']+)'", html)
        if match:
            src = match.group(1)
            if src.startswith('function/') and license_code:
                from resources.lib.decrypters.kvsplayer import kvs_decode
                src = kvs_decode(src, license_code)
            elif src.startswith('function/'):
                src = src.split('function/0/')[-1]
            sources["480p"] = src # Use default quality label
            
    if not sources:
        # Try direct video tag if available
        soup = utils.parse_html(html)
        video_tag = soup.select_one('video source')
        if video_tag:
            src = utils.safe_get_attr(video_tag, "src")
            if src:
                sources["720p"] = src

    if sources:
        videourl = utils.prefquality(
            sources,
            sort_by=lambda x: int("".join([y for y in x if y.isdigit()])) if any(y.isdigit() for y in x) else 0,
            reverse=True,
        )
        if videourl:
            vp.play_from_direct_link(videourl + "|Referer=" + url)
            return

    vp.progress.close()
    utils.notify("Pornditt", "Unable to extract video link")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # Pornditt search format: /search/keyword/
        search_url = "{0}search/{1}/".format(site.url, keyword.replace(" ", "-"))
        List(search_url)

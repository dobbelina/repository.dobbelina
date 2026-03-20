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

from resources.lib.adultsite import AdultSite
from resources.lib import utils
import re
from six.moves import urllib_parse

site = AdultSite(
    "hornyfap",
    "[COLOR hotpink]HornyFap[/COLOR]",
    "https://hornyfap.tv/",
    "hornyfap.png",
    "hornyfap",
)


@site.register(default_mode=True)
def Main(url):
    site.add_dir("Latest Videos", site.url + "latest-updates/", "List", "")
    site.add_dir("Most Viewed", site.url + "most-popular/", "List", "")
    site.add_dir("Categories", site.url + "categories/", "Categories", "")
    site.add_dir("Models", site.url + "models/", "Models", "")
    site.add_dir("Search", site.url + "search/", "Search", site.img_search)
    utils.eod()


@site.register()
def List(url, page=1):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    # Refine to video items in the main list, avoiding sidebar
    items = soup.select("div.list-videos div.item")
    if not items:
        # Fallback for models or other pages that might have different structure
        items = soup.select("div.item")

    for item in items:
        link_tag = item.select_one("a[href*='/video/']")
        if not link_tag:
            continue

        videopage = link_tag.get("href")
        videopage = urllib_parse.urljoin(site.url, videopage)

        title = item.select_one("strong.title")
        title = utils.safe_get_text(title)
        if not title:
            title = link_tag.get("title", "")
        
        title = utils.cleantext(title)

        img_tag = item.select_one("img.thumb, img.lazy-load")
        img = utils.safe_get_attr(img_tag, "src", ["data-src", "data-original", "data-webp"])
        if img:
            img = urllib_parse.urljoin(site.url, img)

        duration = item.select_one("div.duration, span.duration")
        duration = utils.safe_get_text(duration)

        site.add_download_link(
            title,
            videopage,
            "Playvid",
            img,
            title,
            duration=duration,
        )

    # Pagination
    next_page = soup.select_one("li.next a, a.next")
    if next_page:
        next_url = next_page.get("href")
        if next_url:
            next_url = urllib_parse.urljoin(site.url, next_url)
            page_match = re.search(r"/(\d+)/$", next_url)
            np = page_match.group(1) if page_match else str(int(page) + 1)
            site.add_dir(
                "Next Page ({})".format(np), next_url, "List", site.img_next, page=np
            )

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    html = utils.getHtml(url, site.url)
    if not html:
        vp.progress.close()
        return

    # Use the shared play_from_kt_player which handles kvs_decode and rnd parameter
    vp.play_from_kt_player(html, url)


@site.register()
def Categories(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    # The categories are usually in div.list-categories or similar
    items = soup.select("div.list-categories div.item, div.item a[href*='/categories/']")
    
    seen = set()
    for item in items:
        if item.name == "a":
            link_tag = item
        else:
            link_tag = item.select_one("a[href*='/categories/']")
        
        if not link_tag:
            continue
            
        cat_url = link_tag.get("href")
        if not cat_url or cat_url == site.url + "categories/" or cat_url in seen:
            continue
        
        seen.add(cat_url)
        cat_url = urllib_parse.urljoin(site.url, cat_url)
        
        name = utils.safe_get_text(link_tag)
        if not name:
            name = link_tag.get("title", "")
        
        if not name or name.lower() == "categories":
            continue

        site.add_dir(name, cat_url, "List", "")

    utils.eod()


@site.register()
def Models(url):
    html = utils.getHtml(url, site.url)
    if not html:
        utils.eod()
        return

    soup = utils.parse_html(html)
    # The models are usually in div.list-models or similar
    items = soup.select("div.list-models div.item, div.item a[href*='/models/']")
    
    seen = set()
    for item in items:
        if item.name == "a":
            link_tag = item
        else:
            link_tag = item.select_one("a[href*='/models/']")
            
        if not link_tag:
            continue
            
        model_url = link_tag.get("href")
        if not model_url or model_url == site.url + "models/" or model_url in seen:
            continue
            
        seen.add(model_url)
        model_url = urllib_parse.urljoin(site.url, model_url)
        
        name = utils.safe_get_text(link_tag)
        if not name:
            name = link_tag.get("title", "")
            
        if not name or name.lower() == "models":
            continue

        site.add_dir(name, model_url, "List", "")

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        search_url = site.url + "search/" + urllib_parse.quote(keyword) + "/"
        List(search_url)

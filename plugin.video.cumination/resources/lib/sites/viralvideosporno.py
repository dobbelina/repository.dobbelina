"""
Cumination
Copyright (C) 2018 holisticdioxide

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
    "viralvideosporno",
    "[COLOR hotpink]Viral Videos Porno[/COLOR]",
    "https://www.viralvideosporno.com/",
    "vvp.png",
    "viralvideosporno",
)


@site.register(default_mode=True)
def Main():
    """
    Content is the same as Elreyx, with almost the same layout and English descriptions.
    Used functions are defined in elreyx.py
    """
    site.add_dir(
        "[COLOR hotpink]Full Movies[/COLOR]", site.url + "peliculas/amateur", "MList"
    )
    site.add_dir(
        "[COLOR hotpink]Channels[/COLOR]", site.url, "Categories", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "buscar-", "Search", site.img_search
    )
    List(site.url)
    utils.eod()


def _normalize_url(url):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urllib_parse.urljoin(site.url, url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)
    if not soup:
        utils.eod()
        return

    for notice in soup.select(".notice"):
        link = notice.select_one("a[href]")
        if not link:
            continue

        videopage = _normalize_url(utils.safe_get_attr(link, "href", default=""))
        name = utils.cleantext(utils.safe_get_text(link, default=""))
        if not videopage or not name:
            continue

        img_tag = notice.select_one("img[src]")
        img = _normalize_url(utils.safe_get_attr(img_tag, "src", default=""))

        desc_elem = notice.select_one(".description") or notice
        desc = utils.cleantext(utils.safe_get_text(desc_elem, default=""))

        site.add_download_link(name, videopage, "Playvid", img, desc)

    pagination = soup.select_one('#pagination a[rel="next"]') or soup.select_one(
        '#pagination a[href*="raquo"]'
    )
    if not pagination:
        # Fallback to any link containing » in pagination container
        pagination_container = soup.select_one("#pagination")
        if pagination_container:
            for link in pagination_container.find_all("a", href=True):
                if "»" in utils.safe_get_text(link, default=""):
                    pagination = link
                    break
    if pagination:
        nextp = _normalize_url(utils.safe_get_attr(pagination, "href", default=""))
        if nextp:
            page_number_match = re.search(r"(\d+)(?!.*\d)", nextp)
            page_number = page_number_match.group(1) if page_number_match else ""
            label = f"Next Page ({page_number})" if page_number else "Next Page"
            site.add_dir(label, nextp, "List", site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r'source src=["\']([^"\']+)["\']')
    vp.progress.update(25, "[CR]Loading video page[CR]")

    phtml = utils.getHtml(url, site.url)
    
    # Try finding the video source directly in the page first
    source_match = re.search(r'<source\s+[^>]*src=["\']([^"\']+)["\']', phtml, re.IGNORECASE)
    if source_match:
        vp.play_from_direct_link(source_match.group(1))
        return

    soup = utils.parse_html(phtml)

    sources = []
    if soup:
        # Get primary video links
        sources.extend(
            [
                _normalize_url(utils.safe_get_attr(a, "href", default=""))
                for a in soup.select(".box[href], a[href*='embed'], a[href*='player']")
            ]
        )
        
        # Look for hidden/ocult links
        for ocult in soup.select(".ocult, #ocult, [class*='ocult']"):
            ocult_text = ocult.get_text(" ")
            sources.extend(re.findall(r'https?://[^\s"<>]+', ocult_text))
            
        # If universal resolvers are enabled, we might need to scan more
        if utils.addon.getSetting("universal_resolvers") == "true":
            # Search all script tags too
            for script in soup.find_all("script", string=True):
                sources.extend(re.findall(r'https?://[^\s"\'<>]+', script.string))

    # Clean and filter unique valid URLs
    links = {}
    for link in set(sources):
        if not link:
            continue
        try:
            if vp.resolveurl.HostedMediaFile(link).valid_url():
                domain = urllib_parse.urlparse(link).netloc.replace("www.", "")
                links[domain] = link
        except Exception:
            continue

    if links:
        videourl = utils.selector("Select link", links)
        if videourl:
            vp.play_from_link_to_resolve(videourl)
            return

    # Final fallback: let VideoPlayer scan the HTML
    vp.play_from_html(phtml, url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)
    if not soup:
        utils.eod()
        return

    seen = False
    for link in soup.select('a[title^="Ver"][href]'):
        catpage = _normalize_url(utils.safe_get_attr(link, "href", default=""))
        name = utils.cleantext(utils.safe_get_text(link, default=""))
        if not catpage or not name:
            continue
        if not seen:
            # Skip the first entry, which is usually the homepage
            seen = True
            continue
        site.add_dir(name, catpage, "List", "")

    utils.eod()


@site.register()
def MList(url):
    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)
    if not soup:
        utils.eod()
        return

    for card in soup.select(".portada"):
        link = card.select_one("a[href]")
        if not link:
            continue

        videopage = _normalize_url(utils.safe_get_attr(link, "href", default=""))
        img_tag = card.select_one("img[src]")
        img = _normalize_url(utils.safe_get_attr(img_tag, "src", default=""))
        name_elem = card.select_one(".titles") or link
        name = utils.cleantext(utils.safe_get_text(name_elem, default=""))

        if not videopage or not name:
            continue

        site.add_download_link(name, videopage, "Playvid", img, name)

    pagination = soup.select_one('#pagination a[rel="next"]') or soup.select_one(
        "#pagination a[href]"
    )
    if pagination:
        next_suffix = utils.safe_get_attr(pagination, "href", default="")
        nextp = urllib_parse.urljoin(url, next_suffix)
        page_number = next_suffix.split("_")[-1] if "_" in next_suffix else ""
        label = f"Next Page ({page_number})" if page_number else "Next Page"
        site.add_dir(label, nextp, "MList", site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl + title + ".html"
        List(searchUrl)

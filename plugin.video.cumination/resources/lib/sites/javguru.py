"""
Cumination
Copyright (C) 2021 Team Cumination

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
import json
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "javguru",
    "[COLOR hotpink]Jav Guru[/COLOR]",
    "https://jav.guru/",
    "javguru.png",
    "javguru",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "wp-json/wp/v2/categories/",
        "Catjson",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]",
        site.url + "jav-tags-list/",
        "Toplist",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Series[/COLOR]", site.url + "jav-series/", "Cat", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Actress[/COLOR]",
        site.url + "jav-actress-list/",
        "Actress",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Studios[/COLOR]",
        site.url + "jav-studio-list/",
        "Cat",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Uncensored[/COLOR]",
        site.url + "category/jav-uncensored/",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Find all inside-article items
    articles = soup.select(".inside-article")
    for article in articles:
        try:
            # Get link and image
            link = article.select_one("a[href]")
            if not link:
                continue
            video = utils.safe_get_attr(link, "href")
            if not video:
                continue

            img_tag = link.select_one("img[src]")
            if not img_tag:
                continue
            img = utils.safe_get_attr(img_tag, "src", ["data-src"])

            # Get title
            name = utils.safe_get_attr(link, "title", default="")
            if not name:
                name = utils.safe_get_attr(img_tag, "alt", default="")
            name = utils.cleantext(name)
            if not name:
                continue

            contextmenu = []
            contexturl = (
                utils.addon_sys
                + "?mode="
                + str("javguru.Lookupinfo")
                + "&url="
                + urllib_parse.quote_plus(video)
            )
            contextmenu.append(
                ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
            )

            site.add_download_link(name, video, "Play", img, name, contextm=contextmenu)
        except Exception as e:
            utils.kodilog("javguru List: Error processing video - {}".format(e))
            continue

    # Pagination - find current page and next link
    current = soup.select_one(".current")
    if current:
        # Find next link after current
        next_sibling = current.find_next_sibling("a")
        if next_sibling:
            npage = utils.safe_get_attr(next_sibling, "href")
            np = utils.safe_get_text(next_sibling, "").strip()

            # Find last page link
            last_link = soup.find(
                "a", string=lambda text: text and "Last" in text if text else False
            )
            lp = ""
            if last_link:
                last_href = utils.safe_get_attr(last_link, "href")
                lp_match = re.search(r"page/(\d+)/", last_href) if last_href else None
                lp = "/" + lp_match.group(1) if lp_match else ""

            if npage:
                full_url = site.url + npage if npage.startswith("/") else npage
                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR] ({0}{1})".format(np, lp),
                    full_url,
                    "List",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Catjson(url):
    listjson = utils.getHtml(url)
    jdata = json.loads(listjson)
    for cat in jdata:
        name = "{0} ({1})".format(cat["name"], cat["count"])
        site.add_dir(name, cat["link"], "List", "")
    utils.eod()


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # Try different selectors for category items
    # Pattern 1: cat-item with link and count in parentheses
    cat_items = soup.select(".cat-item")
    for item in cat_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            caturl = utils.safe_get_attr(link, "href")
            if not caturl:
                continue

            # Get text and extract name and count
            text = utils.safe_get_text(item, "").strip()
            # Count is in parentheses at end
            count_match = re.search(r"\((\d+)\)$", text)
            count = count_match.group(1) if count_match else ""
            name = re.sub(r"\s*\(\d+\)$", "", text).strip()
            name = utils.cleantext(name)

            if name:
                display_name = "{0} ({1})".format(name, count) if count else name
                site.add_dir(display_name, caturl, "List", "")
        except Exception as e:
            utils.kodilog("javguru Cat: Error processing cat-item - {}".format(e))
            continue

    # Pattern 2: tag links with span counts
    tag_links = soup.select('a[rel="tag"][href]')
    for link in tag_links:
        try:
            caturl = utils.safe_get_attr(link, "href")
            if not caturl:
                continue

            name = utils.safe_get_text(link, "").strip()
            # Look for count in sibling span
            span = link.find_next_sibling("span")
            count = ""
            if span:
                span_text = utils.safe_get_text(span, "").strip()
                count_match = re.search(r"\((\d+)\)", span_text)
                count = count_match.group(1) if count_match else ""

            name = utils.cleantext(name)
            if name:
                display_name = "{0} ({1})".format(name, count) if count else name
                site.add_dir(display_name, caturl, "List", "")
        except Exception as e:
            utils.kodilog("javguru Cat: Error processing tag link - {}".format(e))
            continue

    utils.eod()


@site.register()
def Toplist(url):
    site.add_dir(
        "[COLOR hotpink]Full list, by number of videos[/COLOR]",
        url,
        "Cat",
        site.img_cat,
    )
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # Find tag items with images
    tag_items = []
    links = soup.select("a[href]")
    for link in links:
        try:
            # Check if link contains an image and tagname
            img_tag = link.select_one("img[src]")
            if not img_tag:
                continue

            caturl = utils.safe_get_attr(link, "href")
            if not caturl:
                continue

            img = utils.safe_get_attr(img_tag, "src", ["data-src"])

            # Find tagname
            tagname_elem = link.select_one(".tagname")
            if not tagname_elem:
                continue

            name = utils.safe_get_text(tagname_elem, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            # Find plot (description text)
            # Usually after tagname, look for next text element
            plot = ""  # Optional, not critical

            # Find count (usually with an <i> tag)
            count_elem = link.select_one("i")
            if count_elem:
                # Get next text after <i>
                count_text = count_elem.find_next_sibling(string=True)
                count = count_text.strip() if count_text else ""
            else:
                count = ""

            tag_items.append((caturl, img, name, plot, count))
        except Exception as e:
            utils.kodilog("javguru Toplist: Error processing tag item - {}".format(e))
            continue

    # Sort by name
    for caturl, img, name, plot, count in sorted(tag_items, key=lambda x: x[2]):
        display_name = "{0} ({1})".format(name, count) if count else name
        site.add_dir(display_name, caturl, "List", img)

    utils.eod()


@site.register()
def Actress(url):
    actresshtml = utils.getHtml(url)
    soup = utils.parse_html(actresshtml)

    # Find actress links with /actress/ in href
    actress_links = soup.select('a[href*="/actress/"]')
    for link in actress_links:
        try:
            href = utils.safe_get_attr(link, "href")
            if not href or "/actress/" not in href:
                continue

            # Extract actress path from URL
            if href.startswith("http"):
                actressurl = (
                    "/" + "/".join(href.split("/")[3:])
                    if len(href.split("/")) > 3
                    else href
                )
            else:
                actressurl = href

            # Get image
            img_tag = link.select_one("img[src]")
            if not img_tag:
                continue
            img = utils.safe_get_attr(img_tag, "src", ["data-src"])

            # Get name from img alt
            name = utils.safe_get_attr(img_tag, "alt", default="")
            if not name:
                name = utils.safe_get_text(link, "").strip()
            name = utils.cleantext(name)
            if not name:
                continue

            # Find video count (usually after </i> tag)
            count_elem = link.select_one("i")
            videos = ""
            if count_elem:
                # Get next text after <i>
                count_text = count_elem.find_next_sibling(string=True)
                videos = count_text.strip() if count_text else ""

            if videos:
                name = "{0} ({1})".format(name, videos)

            full_url = (
                site.url + actressurl
                if actressurl.startswith("/")
                else site.url + "/" + actressurl
            )
            site.add_dir(name, full_url, "List", img)
        except Exception as e:
            utils.kodilog("javguru Actress: Error processing actress - {}".format(e))
            continue

    # Pagination - find current page and next link
    current = soup.select_one(".current")
    if current:
        # Find next link after current
        next_sibling = current.find_next_sibling("a")
        if next_sibling:
            npage = utils.safe_get_attr(next_sibling, "href")
            np = utils.safe_get_text(next_sibling, "").strip()

            if npage:
                full_url = site.url + npage if npage.startswith("/") else npage
                site.add_dir(
                    "[COLOR hotpink]Next Page...[/COLOR] ({0})".format(np),
                    full_url,
                    "Actress",
                    site.img_next,
                )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = "{0}{1}".format(url, keyword.replace(" ", "+"))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    sources = []
    videohtml = utils.getHtml(url)
    
    # Try current JSON-based approach with improved reversal logic from upstream
    match = re.compile('iframe_url":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(
        videohtml
    )
    if match:
        for i, stream in enumerate(match):
            link = utils._bdecode(stream)
            vp.progress.update(
                25 + (i * 5), "[CR]Loading streaming link {0} page[CR]".format(i + 1)
            )
            # Use the simpler logic from upstream which seems to handle current obfuscation better
            vlink = link.replace('d=', 'r=').split("=")
            if len(vlink) > 1:
                src = vlink[0] + '=' + vlink[1].split("&")[0][::-1]
                src = utils.getVideoLink(src, link)
                sources.append('"{}"'.format(src))

    # Try window.open patterns as fallback
    match_open = re.compile(r"window\.open\('([^']+)'", re.DOTALL | re.IGNORECASE).findall(
        videohtml
    )
    if match_open:
        for i, dllink in enumerate(match_open):
            vp.progress.update(
                60 + (i * 5), "[CR]Loading download link {0} page[CR]".format(i + 1)
            )
            try:
                dl_html = utils.getHtml(dllink)
                match_dl = re.compile('URL=([^"]+)"', re.DOTALL | re.IGNORECASE).findall(
                    dl_html
                )
                if match_dl:
                    sources.append('"{}"'.format(match_dl[0]))
            except Exception:
                continue

    if sources:
        vp.progress.update(75, "[CR]Loading video page[CR]")
        vp.play_from_html(", ".join(sources))
    else:
        vp.progress.close()
        utils.notify("Oh oh", "Couldn't find any playable sources")


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'/(category/[^"]+)"\s*?rel="category tag">([^<]+)<', ""),
        ("Tags", r'/(tag/[^"]+)"\s*?rel="tag">([^<]+)</a', ""),
        ("Studio", r'/(maker/[^"]+)"\s*?>([^<]+)</a></li><li><strong>L', ""),
        ("Label", r'/(studio/[^"]+)"\s*?>([^<]+)<', ""),
        ("Series", r'/(series/[^"]+)"\s*?>([^<]+)<', ""),
        ("Actor", r'/(actor/[^"]+)"\s*?>([^<]+)<', ""),
        ("Actress", r'/(actress/[^"]+)"\s*?>([^<]+)</a>(?:,|</li>[^<])', ""),
    ]

    lookupinfo = utils.LookupInfo(site.url, url, "javguru.List", lookup_list)
    lookupinfo.getinfo()

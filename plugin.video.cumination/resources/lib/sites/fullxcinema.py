"""
Cumination
Copyright (C) 2023 Team Cumination

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
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "fullxcinema",
    "[COLOR hotpink]fullxcinema[/COLOR]",
    "https://fullxcinema.com/",
    "fullxcinema.png",
    "fullxcinema",
)


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Categories[/COLOR]", site.url, "Cat", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "?s=", "Search", site.img_search
    )
    List(site.url + "?filter=latest")


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    # Split at "SHOULD WATCH" to avoid unwanted content
    if ">SHOULD WATCH<" in listhtml:
        html = listhtml.split(">SHOULD WATCH<")[0]
    else:
        html = listhtml

    soup = utils.parse_html(html)
    video_items = soup.select("article[data-video-id]")

    cm = []
    cm_lookupinfo = utils.addon_sys + "?mode=" + str("fullxcinema.Lookupinfo") + "&url="
    cm.append(
        ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + cm_lookupinfo + ")")
    )
    cm_related = utils.addon_sys + "?mode=" + str("fullxcinema.Related") + "&url="
    cm.append(
        ("[COLOR deeppink]Related videos[/COLOR]", "RunPlugin(" + cm_related + ")")
    )

    for item in video_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            videopage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title")

            img = utils.safe_get_attr(item, "data-main-thumb")

            # Look for duration
            duration_tag = item.select_one("i.fa-clock-o")
            duration = utils.safe_get_text(duration_tag) if duration_tag else ""

            if not videopage or not name:
                continue

            name = utils.cleantext(name)
            site.add_download_link(
                name, videopage, "Play", img, name, duration=duration, contextm=cm
            )

        except Exception as e:
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Handle pagination
    if ">Next" in html:
        next_link = soup.select_one('a[href*="Next"]')
    else:
        # Try to find next page after current
        current = soup.select_one(".current")
        if current:
            next_link = current.find_next("a")
        else:
            next_link = None

    if next_link and next_link.get("href"):
        next_url = next_link.get("href")

        # Extract page numbers
        page_match = re.search(r"/page/(\d+)", next_url)
        np = page_match.group(1) if page_match else ""

        # Try to find last page
        if ">Last" in html:
            last_link = soup.select_one('a[href*="Last"]')
            if last_link:
                last_match = re.search(r"/page/(\d+)", last_link.get("href", ""))
                lp = last_match.group(1) if last_match else ""
        else:
            # Try to find the highest page number
            page_links = soup.select('a[href*="/page/"]')
            page_numbers = []
            for link in page_links:
                match = re.search(r"/page/(\d+)", link.get("href", ""))
                if match:
                    page_numbers.append(int(match.group(1)))
            lp = str(max(page_numbers)) if page_numbers else ""

        page_label = "Next Page"
        if np:
            page_label += " ({})".format(np)
            if lp:
                page_label += "/{}".format(lp)

        cm_page = (
            utils.addon_sys
            + "?mode=fullxcinema.GotoPage&list_mode=fullxcinema.List&url="
            + urllib_parse.quote_plus(next_url)
            + "&np="
            + str(np)
            + "&lp="
            + str(lp)
        )
        cm = [("[COLOR violet]Goto Page #[/COLOR]", "RunPlugin(" + cm_page + ")")]

        site.add_dir(page_label, next_url, "List", site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        url = url.replace("/page/{}".format(np), "/page/{}".format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg="Out of range!")
            return
        contexturl = (
            utils.addon_sys
            + "?mode="
            + str(list_mode)
            + "&url="
            + urllib_parse.quote_plus(url)
        )
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    # Split to focus on tags section
    if 'title">Tags<' in cathtml:
        tags_section = cathtml.split('title">Tags<')[-1].split("/section>")[0]
    else:
        tags_section = cathtml

    soup = utils.parse_html(tags_section)
    category_links = soup.select("a[href][aria-label]")

    for link in category_links:
        try:
            caturl = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "aria-label")

            if not caturl or not name:
                continue

            name = utils.cleantext(name)
            site.add_dir(name, caturl, "List", "")

        except Exception as e:
            utils.kodilog("Error parsing category: " + str(e))
            continue

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        url = "{0}{1}".format(url, keyword.replace(" ", "%20"))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='<source src="([^"]+)"')
    videohtml = utils.getHtml(url)
    
    # Try finding the iframe URL via regex
    match = re.compile(
        r'(?:myiframe|player)">\s*<iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE
    ).findall(videohtml)
    
    if not match:
        # Fallback to meta tag
        match = re.compile(
            r'<meta itemprop="embedURL" content="([^"]+)"', re.DOTALL | re.IGNORECASE
        ).findall(videohtml)
        
    if match:
        link = match[0]
        if vp.resolveurl.HostedMediaFile(link):
            vp.play_from_link_to_resolve(link)
        else:
            html = utils.getHtml(link)
            vp.play_from_html(html)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        (
            "Actor",
            r'href="{}(/actor/[^"]+)" title="([^"]+)">'.format(site.url[:-1]),
            "",
        ),
        (
            "Category",
            r'href="{}(/category/[^"]+)" class="label" title="([^"]+)"'.format(
                site.url[:-1]
            ),
            "",
        ),
        (
            "Tag",
            r'href="{}(/tag/[^"]+)" class="label" title="([^"]+)"'.format(
                site.url[:-1]
            ),
            "",
        ),
    ]
    lookupinfo = utils.LookupInfo(site.url, url, "fullxcinema.List", lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("fullxcinema.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")

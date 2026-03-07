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

from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "freshporno",
    "[COLOR hotpink]FreshPorno[/COLOR]",
    "https://freshporno.org/",
    "freshporno.png",
    "freshporno",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Tags[/COLOR]", site.url + "tags/", "Tags", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Channels[/COLOR]",
        site.url + "channels/",
        "Channels",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Models[/COLOR]", site.url + "models/", "Models", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, "")
    soup = utils.parse_html(listhtml)

    def context_menu_builder(item_url, item_title):
        contexturl = (
            utils.addon_sys
            + "?mode="
            + str("freshporno.Lookupinfo")
            + "&url="
            + urllib_parse.quote_plus(item_url)
        )
        return [
            ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
        ]

    spec = {
        "items": ".thumbs-inner",
        "url": {"selector": "a[href]", "attr": "href"},
        "title": {"selector": "a[title]", "attr": "title"},
        "thumbnail": {"selector": "img", "attr": "data-original"},
        "pagination": {"selector": "a.next[href]", "attr": "href"},
    }

    utils.soup_videos_list(site, soup, spec, contextm=context_menu_builder)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    vpage = utils.getHtml(url, site.url)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "-")
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Tags(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    tag_links = soup.select('a[href*="/tags/"]')
    for link in tag_links:
        try:
            tagpage = utils.safe_get_attr(link, "href")
            icon = link.select_one("i.fa-tag")
            if not icon:
                continue

            name = utils.safe_get_text(link).replace("icon", "").strip()
            name = utils.cleantext(name)

            if name and tagpage:
                site.add_dir(name, site.url + tagpage, "List", "")
        except Exception as e:
            utils.kodilog("Error parsing tag: " + str(e))
            continue

    utils.eod()


@site.register()
def Channels(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    content_wrapper = soup.select_one(".content-wrapper")
    if not content_wrapper:
        utils.eod()
        return

    channel_links = content_wrapper.select("a[href]")
    for link in channel_links:
        try:
            channelpage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title")

            if not name or not channelpage:
                continue

            # Extract video count from the link content
            link_text = utils.safe_get_text(link)
            videos = ""
            if link_text:
                # Extract number from text like "123 videos"
                import re

                video_match = re.search(r"(\d+)", link_text)
                if video_match:
                    videos = video_match.group(1)

            name = "{} - {}".format(utils.cleantext(name.strip()), videos)

            # Handle image extraction
            img = ""
            parent_html = str(link.parent)
            if "no image" not in parent_html:
                img_match = re.search(r'data-original="([^"]+)"', parent_html)
                if img_match:
                    img = img_match.group(1)

            site.add_dir(name, channelpage, "List", img)

        except Exception as e:
            utils.kodilog("Error parsing channel: " + str(e))
            continue

    utils.eod()


@site.register()
def Models(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    content_wrapper = soup.select_one(".content-wrapper")
    if not content_wrapper:
        utils.eod()
        return

    model_links = content_wrapper.select("a[href]")
    for link in model_links:
        try:
            modelpage = utils.safe_get_attr(link, "href")
            name = utils.safe_get_attr(link, "title")

            if not name or not modelpage:
                continue

            # Extract video count from the link content
            link_text = utils.safe_get_text(link)
            videos = ""
            if link_text:
                # Extract number from text like "123 videos"
                import re

                video_match = re.search(r"(\d+)", link_text)
                if video_match:
                    videos = video_match.group(1)

            name = "{} - {}".format(utils.cleantext(name.strip()), videos)

            # Handle image extraction
            img = ""
            parent_html = str(link.parent)
            if "no image" not in parent_html:
                img_match = re.search(r'data-original="([^"]+)"', parent_html)
                if img_match:
                    img = img_match.group(1)

            site.add_dir(name, modelpage, "List", img)

        except Exception as e:
            utils.kodilog("Error parsing model: " + str(e))
            continue

    # Handle pagination for models
    next_link = soup.select_one("a.next[href]")
    if next_link:
        next_href = utils.safe_get_attr(next_link, "href")
        if next_href:
            page_number = next_href.split("/")[-2]
            site.add_dir(
                "Next Page (" + page_number + ")",
                site.url + next_href,
                "Models",
                site.img_next,
            )

    utils.eod()


@site.register()
def Lookupinfo(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    infodict = {}

    # Channels
    for link in soup.select('a[href*="/channels/"]'):
        title = utils.safe_get_attr(link, "title") or utils.safe_get_text(link)
        href = utils.safe_get_attr(link, "href")
        if title and href:
            name = "Channel - {}".format(utils.cleantext(title))
            infodict[name] = (urllib_parse.urljoin(site.url, href), "freshporno.List")

    # Tags
    for link in soup.select('a[href*="/tags/"]'):
        if link.select_one("i.fa-tag"):
            title = utils.safe_get_text(link).replace("icon", "").strip()
            href = utils.safe_get_attr(link, "href")
            if title and href:
                name = "Tag - {}".format(utils.cleantext(title))
                infodict[name] = (
                    urllib_parse.urljoin(site.url, href),
                    "freshporno.List",
                )

    # Models
    for link in soup.select('a[href*="/models/"]'):
        title = utils.safe_get_attr(link, "title") or utils.safe_get_text(link)
        href = utils.safe_get_attr(link, "href")
        if title and href:
            name = "Actor - {}".format(utils.cleantext(title))
            infodict[name] = (urllib_parse.urljoin(site.url, href), "freshporno.List")

    if infodict:
        selected_item = utils.selector("Choose item", infodict, show_on_one=True)
        if selected_item:
            contexturl = (
                utils.addon_sys
                + "?mode="
                + selected_item[1]
                + "&url="
                + urllib_parse.quote_plus(selected_item[0])
            )
            utils.xbmc.executebuiltin("Container.Update(" + contexturl + ")")
    else:
        utils.notify("Oh Oh", "No info found")

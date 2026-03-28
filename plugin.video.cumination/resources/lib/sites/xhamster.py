"""
Cumination
Copyright (C) 2022 Team Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import json
from six.moves import urllib_parse
from kodi_six import xbmc, xbmcgui, xbmcplugin
import datetime

site = AdultSite(
    "xhamster",
    "[COLOR hotpink]xHamster[/COLOR]",
    "https://xhamster.com/",
    "xhamster.png",
    "xhamster",
)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Channels[/COLOR]",
        site.url + "channels",
        "Channels",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]",
        site.url + "pornstars",
        "Pornstars",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Celebrities[/COLOR]",
        site.url + "celebrities",
        "Celebrities",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "search/", "Search", site.img_search
    )
    List(site.url + "newest")
    utils.eod()


@site.register()
def List(url):
    url = update_url(url)

    context_category = utils.addon_sys + "?mode=" + str("xhamster.ContextCategory")
    context_length = utils.addon_sys + "?mode=" + str("xhamster.ContextLength")
    context_quality = utils.addon_sys + "?mode=" + str("xhamster.ContextQuality")
    contextmenu = [
        (
            "[COLOR violet]Category[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("category")
            ),
            "RunPlugin(" + context_category + ")",
        ),
        (
            "[COLOR violet]Length[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("length")
            ),
            "RunPlugin(" + context_length + ")",
        ),
        (
            "[COLOR violet]Quality[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("quality")
            ),
            "RunPlugin(" + context_quality + ")",
        ),
    ]

    try:
        response = utils.getHtml(url, site.url)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in xhamster: " + str(e))
        site.add_dir(
            "No videos found. [COLOR hotpink]Clear all filters.[/COLOR]",
            "",
            "ResetFilters",
            Folder=False,
            contextm=contextmenu,
        )
        utils.eod()
        return

    pagetitle = ""
    match = re.compile(r"<title>([^>]+)</title>", re.DOTALL | re.IGNORECASE).search(
        response
    )
    if not match:
        match = re.compile(r">\s*([^>]+)\s*</h1>", re.DOTALL | re.IGNORECASE).search(
            response
        )
    if match:
        pagetitle = match.group(1)

    jdata = _load_initials_json(response)

    videos, pagination_props, discovered_title = _extract_videos_and_pagination(jdata)
    if discovered_title:
        pagetitle = discovered_title
    if not videos:
        utils.notify("Oh Oh", "No video found.")
        return

    thumbnails = utils.Thumbnails(site.name)
    for video in videos:
        if not video:
            continue
        if video.get("isBlockedByGeo", False):
            continue
        name = video["title"] if utils.PY3 else video["title"].encode("utf8")
        videolink = video["pageURL"]
        img = video.get("thumbURL", "")
        if img.endswith(".jpg") and "webp" in img:
            img = thumbnails.fix_img(img)
        if not img:
            continue
        length = str(datetime.timedelta(seconds=video["duration"]))
        if length.startswith("0:"):
            length = length[2:]
        hd = "4k" if video.get("isUHD", "") else "HD" if video.get("isHD", "") else ""
        name = "[COLOR blue][VR][/COLOR] " + name if video.get("isVR", "") else name
        name = (
            name + " [COLOR blue][Full Video][/COLOR]"
            if video.get("hasProducerBadge", "")
            else name
        )
        name = (
            name + " [COLOR orange][Amateur][/COLOR]"
            if video.get("hasAmateurBadge", "")
            else name
        )
        site.add_download_link(
            name,
            videolink,
            "Playvid",
            img,
            name,
            contextm=contextmenu,
            duration=length,
            quality=hd,
        )

    npurl = None
    if isinstance(pagination_props, dict):
        current_page = pagination_props.get("currentPageNumber")
        last_page = pagination_props.get("lastPageNumber")
        template = pagination_props.get("pageLinkTemplate")
        if current_page is not None and template:
            np = current_page + 1
            lp = last_page
            if not lp or lp >= np:
                npurl = template.replace(r"\/", "/").replace("{#}", "{}".format(np))
    elif "pagesNewestComponent" in jdata:
        if "paginationProps" in jdata["pagesNewestComponent"]:
            np = (
                jdata["pagesNewestComponent"]["paginationProps"]["currentPageNumber"]
                + 1
            )
            lp = jdata["pagesNewestComponent"]["paginationProps"]["lastPageNumber"] + 1
            if lp >= np:
                npurl = (
                    jdata["pagesNewestComponent"]["paginationProps"]["pageLinkTemplate"]
                    .replace(r"\/", "/")
                    .replace("{#}", "{}".format(np))
                )
    elif "pagesCategoryComponent" in jdata:
        if "paginationProps" in jdata["pagesCategoryComponent"]:
            np = (
                jdata["pagesCategoryComponent"]["paginationProps"]["currentPageNumber"]
                + 1
            )
            lp = (
                jdata["pagesCategoryComponent"]["paginationProps"]["lastPageNumber"] + 1
            )
            if lp >= np:
                npurl = (
                    jdata["pagesCategoryComponent"]["paginationProps"][
                        "pageLinkTemplate"
                    ]
                    .replace(r"\/", "/")
                    .replace("{#}", "{}".format(np))
                )
    elif jdata.get("paginationComponent"):
        np = jdata["paginationComponent"]["currentPageNumber"] + 1
        lp = jdata["paginationComponent"]["lastPageNumber"]
        if lp >= np:
            npurl = (
                jdata["paginationComponent"]["pageLinkTemplate"]
                .replace(r"\/", "/")
                .replace("{#}", "{}".format(np))
            )
    elif "pagination" in jdata:
        np = jdata["pagination"]["next"]
        lp = jdata["pagination"]["maxPages"]
        if lp >= np:
            npurl = (
                jdata["pagination"]["pageLinkTemplate"]
                .replace(r"\/", "/")
                .replace("{#}", "{}".format(np))
            )
    elif "page" in jdata:
        np = jdata["page"] + 1
        lp = None
        if "maxPages" in jdata:
            lp = jdata["maxPages"]
        if not lp or (np and lp >= np):
            match = re.compile(
                r'data-page="next"\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE
            ).search(response)
            if match:
                npurl = match.group(1)
    if npurl:
        npurl = npurl.replace("&#x3D;", "=").replace("&amp;", "&")
        cm_page = (
            utils.addon_sys
            + "?mode=xhamster.GotoPage&list_mode=xhamster.List&url="
            + urllib_parse.quote_plus(npurl)
            + "&np="
            + str(np)
            + "&lp="
            + str(lp)
        )
        cm = [("[COLOR violet]Goto Page #[/COLOR]", "RunPlugin(" + cm_page + ")")]
        npage = str(np) + "/" + str(lp) if lp else str(np)
        site.add_dir(
            "Next Page ({})   ... [COLOR blue]{}[/COLOR]".format(npage, pagetitle),
            npurl,
            "List",
            site.img_next,
            contextm=cm,
        )
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url, error=True)
    if "This video was deleted" in videopage:
        utils.notify("Oh Oh", "This video was deleted.")
        return
    hexurl = ""
    match = re.compile(r'<link rel="preload" href="([^"]+m3u8)"', re.DOTALL).search(
        videopage
    )
    if match:
        videourl = match.group(1)
        videourl = videourl.replace(".av1.", ".h264.")
    else:
        jsondata = videopage.split(">window.initials=")[-1].split(";</script>")[0]
        jdata = json.loads(jsondata)
        data = jdata.get("xplayerSettings", {})
        data2 = jdata.get("xplayerSettings2", {})
        sources = data.get("sources", {})
        sources2 = data2.get("sources", {})

        if "hls" in sources:
            h264src = sources["hls"].get("h264", "")
            h265src = sources["hls"].get("h265", "")
            av1src = sources["hls"].get("av1", "")
            if h264src:
                hexurl = h264src["url"]
            elif h265src:
                hexurl = h265src["url"]
            elif av1src:
                hexurl = av1src["url"]
            else:
                utils.notify("Oh Oh", "No playable video found.")
                return

        if hexurl:
            from resources.lib.decrypters import xhamster_decrypt

            try:
                videourl = xhamster_decrypt.deobfuscate_url(hexurl)
            except Exception as e:
                utils.notify("Oh Oh", "Failed to deobfuscate video URL - {}".format(e))
                return
        else:
            if "standard" in sources2:
                src = sources2["standard"].get("h264", "")
                srcs = {}
                for s in src:
                    srcs[s["quality"]] = s["url"]
                videourl = utils.prefquality(
                    srcs,
                    sort_by=lambda x: 2160 if x == "4k" else int(x[:-1]),
                    reverse=True,
                )
                if not videourl:
                    return

    if videourl.startswith("http"):
        vp.progress.update(75, "[CR]Playing video[CR]")
        vp.play_from_direct_link(videourl)


@site.register()
def Categories(url):
    cat = get_setting("category")
    if cat == "gay":
        url = url.replace("/categories", "/gay/categories")
    elif cat == "shemale":
        url = url.replace("/categories", "/shemale/categories")
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)
    seen = set()
    for anchor in soup.find_all("a", href=True):
        if not _has_class_prefix(anchor, "thumbItem-"):
            continue
        img_tag = anchor.find("img")
        thumb = utils.safe_get_attr(img_tag, "data-thumb-url", ["data-src", "src"])
        if not thumb:
            continue
        name_el = anchor.find("h3") or anchor
        name = utils.cleantext(utils.safe_get_text(name_el, default="").strip())
        if not name:
            continue
        href = urllib_parse.urljoin(site.url, anchor["href"])
        if href in seen:
            continue
        seen.add(href)
        site.add_dir(name, href, "List", thumb)
    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Channels(url):
    cat = get_setting("category")
    if cat == "gay":
        url = url.replace("/channels", "/gay/channels")
    elif cat == "shemale":
        url = url.replace("/channels", "/shemale/channels")
    cathtml = utils.getHtml(url, site.url)
    data = _load_initials_json(cathtml)
    layout = data.get("layoutPage", {})
    channels = (
        layout.get("channels")
        or layout.get("channelsListProps", {}).get("channels")
        or data.get("channels", [])
    )
    for channel in channels:
        if channel.get("isBlockedByGeo"):
            continue
        name = utils.cleantext(
            channel.get("channelName", "") or channel.get("name", "")
        )
        page_url = channel.get("channelURL")
        if not name or not page_url:
            continue
        thumb = channel.get("thumbURL") or channel.get("siteLogoURL") or ""
        videos = channel.get("videoCount")
        videos_label = (
            "{:,} videos".format(videos) if isinstance(videos, int) else videos or ""
        )
        title = "{0} [COLOR yellow]({1})[/COLOR]".format(name, videos_label.strip())
        list_url = page_url.rstrip("/")
        if not list_url.endswith("/newest"):
            list_url += "/newest"
        site.add_dir(title, list_url, "List", thumb)
    pagination = layout.get("paginationProps") or layout.get(
        "channelsListProps", {}
    ).get("paginationProps")
    _add_next_page_from_props(pagination, "Channels")
    utils.eod()


@site.register()
def Pornstars(url):
    cat = get_setting("category")
    if cat == "gay":
        url = url.replace("/pornstars", "/gay/pornstars")
    elif cat == "shemale":
        url = url.replace("/pornstars", "/shemale/pornstars")
    cathtml = utils.getHtml(url, site.url)
    data = _load_initials_json(cathtml)
    layout = data.get("layoutPage", {})
    pornstars = layout.get("pornstarListProps", {}).get("pornstars", [])
    _add_people_directory(pornstars)
    pagination = layout.get("pornstarListProps", {}).get("paginationProps")
    _add_next_page_from_props(pagination, "Pornstars")
    utils.eod()


@site.register()
def Celebrities(url):
    cat = get_setting("category")
    if cat == "gay":
        url = url.replace("/celebrities", "/gay/celebrities")
    elif cat == "shemale":
        url = url.replace("/celebrities", "/shemale/celebrities")
    cathtml = utils.getHtml(url, site.url)
    data = _load_initials_json(cathtml)
    layout = data.get("layoutPage", {})
    celebrities = layout.get("pornstarListProps", {}).get("pornstars", [])
    _add_people_directory(celebrities)
    pagination = layout.get("pornstarListProps", {}).get("paginationProps")
    _add_next_page_from_props(pagination, "Celebrities")
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "%20")
        searchUrl = url + title + "?orientations=" + get_setting("category")
        List(searchUrl)


@site.register()
def ContextCategory():
    categories = {"straight": 1, "gay": 2, "shemale": 3}
    cat = utils.selector(
        "Select category", categories.keys(), sort_by=lambda x: categories[x]
    )
    if cat:
        utils.addon.setSetting("xhamstercat", cat)
        if cat == "straight":
            utils._getHtml(site.url + "?straight=", site.url)
        else:
            utils._getHtml(site.url + cat, site.url)
        utils.refresh()


@site.register()
def ContextLength():
    categories = {"ALL": 1, "30+ min": 2}  # , '10-40 min': 3, '0-10 min': 4}
    cat = utils.selector(
        "Select category", categories.keys(), sort_by=lambda x: categories[x]
    )
    if cat:
        utils.addon.setSetting("xhamsterlen", cat)
        utils.refresh()


@site.register()
def ContextQuality():
    categories = {"ALL": 1, "2160p": 2, "1080p": 3, "720p": 4}
    cat = utils.selector(
        "Select category", categories.keys(), sort_by=lambda x: categories[x]
    )
    if cat:
        utils.addon.setSetting("xhamsterqual", cat)
        utils.refresh()


def get_setting(x):
    if x == "category":
        ret = utils.addon.getSetting("xhamstercat") or "straight"
    if x == "length":
        ret = utils.addon.getSetting("xhamsterlen") or "ALL"
    if x == "quality":
        ret = utils.addon.getSetting("xhamsterqual") or "ALL"
    return ret


def update_url(url):
    cat = get_setting("category")
    old_cat = "straight"
    if url.startswith(site.url + "gay") or "orientations=gay" in url:
        old_cat = "gay"
    elif url.startswith(site.url + "shemale") or "orientations=shemale" in url:
        old_cat = "shemale"

    if cat != old_cat:
        if "/search/" in url:
            url = re.sub(r"[\?&]page=[^\?&]+", "", url)
            url = re.sub(r"[\?&]orientations=[^\?&]+", "", url)
            if cat != "straight":
                url += "&orientations=" + cat if "?" in url else "?orientations=" + cat
        else:
            url = re.sub(r"newest/\d+", "newest", url)
            if old_cat == "straight":
                url = url.replace(site.url, site.url + cat + "/")
            else:
                url = (
                    url.replace(site.url + old_cat, site.url[:-1])
                    if cat == "straight"
                    else url.replace(site.url + old_cat, site.url + cat)
                )

    qual = get_setting("quality")
    if "quality=720p" in url or ("/hd/" in url and "quality=1080p" not in url):
        old_qual = "720p"
    elif "quality=1080p" in url:
        old_qual = "1080p"
    elif "quality=2160p" in url or "/4k/" in url:
        old_qual = "2160p"
    else:
        old_qual = "ALL"

    if qual != old_qual:
        url = re.sub(r"[\?&]page=[^\?&]+", "", url)
        if "search" in url:
            url = re.sub(r"[\?&]quality=[^\?&]+", "", url)
            if qual != "ALL":
                url += "&quality=" + qual if "?" in url else "?quality=" + qual
        else:
            url = re.sub(r"newest/\d+", "newest", url)
            url = (
                url.replace("/hd/newest", "newest")
                .replace("/4k/newest", "/newest")
                .replace("quality=1080p", "")
                .replace("?&", "&")
                .replace("&&", "&")
            )

            url = url.split("newest")
            if qual == "720p":
                url[0] += "hd/" if url[0].endswith("/") else "/hd/"
                url = "newest".join(url)
            elif qual == "2160p":
                url[0] += "4k/" if url[0].endswith("/") else "/4k/"
                url = "newest".join(url)
            else:
                url[0] += "hd/" if url[0].endswith("/") else "/hd/"
                url = "newest".join(url)
                url += "&quality=1080p" if "?" in url else "?quality=1080p"

    length = get_setting("length")

    if "min-duration=30" in url:
        old_length = "30+ min"
    else:
        old_length = "ALL"

    if length != old_length:
        url = re.sub(r"[\?&]page=[^\?&]+", "", url)
        url = re.sub(r"newest/\d+", "newest", url)
        url = re.sub(r"[\?&]min-duration=[^\?&]+", "", url)

        if length == "30+ min":
            url += "&min-duration=30" if "?" in url else "?min-duration=30"

    return url


@site.register()
def ResetFilters():
    utils.addon.setSetting("xhamstercat", "straight")
    utils.addon.setSetting("xhamsterlen", "ALL")
    utils.addon.setSetting("xhamsterqual", "ALL")
    utils.refresh()
    return


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        if lp and int(pg) > int(lp):
            utils.notify(msg="Out of range!")
            return
        url = url.replace("page={}".format(np), "page={}".format(pg))
        url = url.replace("newest/{}".format(np), "newest/{}".format(pg))
        url = url.replace("/{}?".format(np), "/{}?".format(pg))
        contexturl = (
            utils.addon_sys
            + "?mode="
            + str(list_mode)
            + "&url="
            + urllib_parse.quote_plus(url)
            + "&page="
            + str(pg)
        )
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")


def _has_class_prefix(element, prefix):
    classes = element.get("class") if element else None
    if not classes:
        return False
    return any(cls.startswith(prefix) for cls in classes)


def _find_nested_value(data, key):
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = _find_nested_value(value, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_nested_value(item, key)
            if found is not None:
                return found
    return None


def _extract_videos_and_pagination(jdata):
    layout_page = jdata.get("layoutPage", {})
    pagetitle = ""
    videos = None
    pagination = None

    if isinstance(layout_page, dict):
        category_info = layout_page.get("categoryInfoProps", {})
        if isinstance(category_info, dict):
            pagetitle = category_info.get("pageTitle", "")

        video_list_props = layout_page.get("videoListProps", {})
        if isinstance(video_list_props, dict):
            videos = video_list_props.get("videoThumbProps")
        if not videos:
            videos = layout_page.get("videoThumbProps")
        if isinstance(layout_page.get("paginationProps"), dict):
            pagination = layout_page.get("paginationProps")

    if not videos:
        component_video_paths = (
            ("trendingVideoListComponent", "videoThumbProps"),
            ("trendingVideoSectionComponent", "videoListProps", "videoThumbProps"),
            ("searchResult", "videoThumbProps"),
            ("pagesNewestComponent", "videoListProps", "videoThumbProps"),
            ("pagesCategoryComponent", "trendingVideoListProps", "videoThumbProps"),
        )
        for path in component_video_paths:
            node = jdata
            for part in path:
                if not isinstance(node, dict):
                    node = None
                    break
                node = node.get(part)
            if node:
                videos = node
                break

    if not videos:
        video_list_props = _find_nested_value(jdata, "videoListProps")
        if isinstance(video_list_props, dict):
            videos = video_list_props.get("videoThumbProps")

    if not videos:
        nested_videos = _find_nested_value(jdata, "videoThumbProps")
        if isinstance(nested_videos, list):
            videos = nested_videos

    if not pagination:
        nested_pagination = _find_nested_value(jdata, "paginationProps")
        if isinstance(nested_pagination, dict):
            pagination = nested_pagination

    if not pagination:
        pagination_component = jdata.get("paginationComponent")
        if isinstance(pagination_component, dict):
            pagination = pagination_component
        elif isinstance(jdata.get("pagination"), dict):
            pagination = jdata.get("pagination")

    return videos, pagination, pagetitle


def _load_initials_json(html, soup=None):
    if not html:
        return {}
    script_text = ""
    if not soup:
        try:
            soup = utils.parse_html(html)
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in xhamster: " + str(e))
            soup = None
    if soup:
        script = soup.find("script", id=lambda value: value and "initials" in value)
        if script:
            script_text = script.string or script.get_text() or ""
    if not script_text:
        match = re.search(r"window\.initials=({.*?})<\/script>", html, re.DOTALL)
        if match:
            script_text = match.group(1)
    if not script_text:
        parts = html.split("window.initials=")
        if len(parts) > 1:
            script_text = parts[-1].split(";</script>")[0]
    if not script_text:
        return {}
    script_text = script_text.strip()
    if script_text.startswith("window.initials="):
        script_text = script_text.split("window.initials=", 1)[1]
    script_text = script_text.rstrip(";")
    try:
        return json.loads(script_text)
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in xhamster: " + str(e))
        return {}


def _add_people_directory(items):
    if not items:
        return
    for person in items:
        if person.get("isBlockedByGeo"):
            continue
        name = utils.cleantext(person.get("name", ""))
        page_url = person.get("pageURL")
        if not name or not page_url:
            continue
        thumb = (
            person.get("imageThumbUrl")
            or person.get("logoThumbUrl")
            or person.get("imageUserAvatarUrl")
            or ""
        )
        videos = person.get("videoCount")
        videos_label = (
            "{:,} videos".format(videos)
            if isinstance(videos, int)
            else (videos or "").strip()
        )
        if not videos_label:
            videos_label = "videos"
        title = "{0} [COLOR yellow]({1})[/COLOR]".format(name, videos_label)
        list_url = page_url.rstrip("/")
        if not list_url.endswith("/newest"):
            list_url += "/newest"
        site.add_dir(title, list_url, "List", thumb)


def _add_next_page_from_props(pagination, mode):
    if not pagination:
        return
    current = pagination.get("currentPageNumber")
    template = pagination.get("pageLinkTemplate")
    if current is None or not template:
        return
    last_page = pagination.get("lastPageNumber")
    next_page = current + 1
    if last_page and next_page > last_page:
        return
    npurl = template.replace(r"\/", "/").replace("{#}", str(next_page))
    title = "[COLOR hotpink]Next Page...[/COLOR]"
    if last_page:
        title += " (Currently in Page {0} of {1})".format(current, last_page)
    else:
        title += " (Currently in Page {0})".format(current)
    site.add_dir(title, npurl, mode, site.img_next)

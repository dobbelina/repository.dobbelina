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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import json
from six.moves import urllib_parse

site = AdultSite(
    "noodlemagazine",
    "[COLOR hotpink]Noodlemagazine[/COLOR]",
    "https://noodlemagazine.com/",
    "noodlemagazine.png",
    "noodlemagazine",
)

data = {
    "sort": {
        "0": {"label": "Date Added", "default": True},
        "1": {"label": "Duration"},
        "2": {"label": "Relevance"},
    },
    "hd": {"0": {"label": "Everything", "default": True}, "1": {"label": "HD Only"}},
    "len": {
        "long": {"label": "Long"},
        "short": {"label": "Short"},
        "any": {"label": "Any", "default": True},
    },
}


@site.register(default_mode=True)
def Main(url):
    site.add_download_link(getFilterLabels(), site.url, "setFilters", "")
    site.add_dir(
        "[COLOR hotpink]Newest[/COLOR]", site.url + "video/" + getFilters(1), "List", ""
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", site.url + "video/", "Search", site.img_search
    )
    site.add_dir(
        "[COLOR hotpink]Babepedia Top 100 Pornstar to search for[/COLOR]",
        "https://www.babepedia.com/pornstartop100",
        "Babepedia",
        site.img_search,
    )
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, "")
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in noodlemagazine: " + str(e))
        return None

    if hasattr(listhtml, "select"):
        soup = listhtml
    else:
        if not isinstance(listhtml, (str, bytes)):
            listhtml = ""
        soup = utils.parse_html(listhtml)
    items = soup.select(".item")
    for item in items:
        link = item.select_one("a[href]")
        videopage = utils.safe_get_attr(link, "href", default="")
        if not videopage:
            continue
        videopage = urllib_parse.urljoin(site.url, videopage)

        img_tag = item.select_one("img")
        img = utils.safe_get_attr(img_tag, "data-src", ["src"])
        if img:
            if img.startswith("//"):
                img = "https:" + img
            elif not img.startswith("http"):
                img = urllib_parse.urljoin(site.url, img)
            if "getVideoPreview" in img:
                i1, i2 = img.split("/getVideoPreview")
                img = "https://" + i1.split("/")[-1] + "/getVideoPreview" + i2
            img = img.replace("&amp;", "&") + "|User-Agent=" + utils.USER_AGENT

        name = utils.cleantext(
            utils.safe_get_attr(img_tag, "alt", default=utils.safe_get_text(link))
        )
        hd_flag = item.select_one(".hd_mark, .hd-mark, [class*='hd_mark']")
        hd = " [COLOR orange]HD[/COLOR]" if hd_flag else ""
        duration = utils.safe_get_text(
            item.select_one(".duration, .time, .video-duration"), default=""
        )

        site.add_download_link(
            name, videopage, "Playvid", img, name, duration=duration, quality=hd
        )

    np = ""
    next_el = soup.select_one(".more[data-page]")
    if next_el:
        np = utils.safe_get_attr(next_el, "data-page", default="")
    if np:
        if "p=" in url:
            nextp = re.sub(r"p=\d+", "p={}".format(np), url)
        elif "?" in url:
            nextp = url + "&p=" + np
        else:
            nextp = url + "?p=" + np
        site.add_dir("Next Page ({})".format(np), nextp, "List", site.img_next, page=np)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    html = utils.getHtml(url, site.url)
    
    sources = {}
    
    # Try finding the playlist JS variable
    p = re.compile(r"(?:window\.playlist|playlist)\s*=\s*(\{.*?\});", re.DOTALL | re.IGNORECASE).search(
        html
    )
    if p:
        try:
            js = json.loads(p.group(1))
            src = js.get("sources", [])
            for x in src:
                label = str(x.get("label", "Unknown"))
                file_url = x.get("file")
                if file_url:
                    sources[label] = file_url
        except Exception as e:
            utils.kodilog("noodlemagazine: Error parsing playlist JSON: {}".format(e))

    # Try finding direct source tags with regex as well
    if not sources:
        matches = re.findall(r'<source\s+[^>]*src=["\']([^"\']+)["\'](?:[^>]*label=["\']([^"\']+)["\'])?', html, re.IGNORECASE)
        for src_url, label in matches:
            sources[label or "HD"] = src_url

    # Fallback to general HTML source searching if playlist JS not found or failed
    if not sources:
        soup = utils.parse_html(html)
        if soup:
            # Look for common video sources
            video_tags = soup.find_all("video")
            for video in video_tags:
                src_tags = video.find_all("source")
                for src in src_tags:
                    label = utils.safe_get_attr(src, "label") or utils.safe_get_attr(src, "title") or "HD"
                    file_url = utils.safe_get_attr(src, "src")
                    if file_url:
                        sources[label] = file_url
            
            # If still nothing, try the VideoPlayer's built-in html scanner
            if not sources:
                vp.play_from_html(html, url)
                return

    if sources:
        videourl = utils.prefquality(
            sources,
            sort_by=lambda x: int("".join([y for y in x if y.isdigit()])) if any(y.isdigit() for y in x) else 0,
            reverse=True,
        )
        if videourl:
            videourl = videourl + "|Referer=" + site.url
            vp.play_from_direct_link(videourl)
            return

    vp.progress.close()
    utils.notify("Oh oh", "No playable video source found")


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "%20")
        searchUrl = url + title + getFilters(0)
        List(searchUrl, 0)


@site.register()
def Babepedia(url):
    try:
        listhtml = utils.getHtml(url, "")
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in noodlemagazine: " + str(e))
        return None

    match = re.compile(
        'class="(?:thumbimg|thumbimg lazy)" border="0" (?:data-)*src="([^"]+)" alt="([^"]+)',
        re.DOTALL | re.IGNORECASE,
    ).findall(listhtml)
    for img, name in match:
        name = utils.cleantext(name)
        img = "https://www.babepedia.com" + img
        videopage = site.url + "video/" + name.replace(" ", "%20") + getFilters(0)
        site.add_dir(name, videopage, "List", img, page=0)
    utils.eod()


@site.register()
def setFilters():
    filters = {"Sort": "sort", "Quality": "hd", "Length": "len"}
    chosenfilter = utils.selector("Select filter", filters)
    if chosenfilter:
        options = {v["label"]: k for k, v in data[chosenfilter].items()}
        chosenoption = utils.selector("Choose option", options)
        if chosenoption:
            utils.addon.setSetting("noodle" + chosenfilter, chosenoption)
            utils.refresh()


def getFilters(page):
    defaults = getDefaults()
    sortvalue = utils.addon.getSetting("noodlesort") or next(
        iter(defaults["sort"].keys())
    )
    hdvalue = utils.addon.getSetting("noodlehd") or next(iter(defaults["hd"].keys()))
    lenvalue = utils.addon.getSetting("noodlelen") or next(iter(defaults["len"].keys()))
    return "?sort={}&hd={}&len={}&p={}".format(sortvalue, hdvalue, lenvalue, page)


def getFilterLabels():
    defaults = getDefaults()
    sortvalue = utils.addon.getSetting("noodlesort") or next(
        iter(defaults["sort"].keys())
    )
    hdvalue = utils.addon.getSetting("noodlehd") or next(iter(defaults["hd"].keys()))
    lenvalue = utils.addon.getSetting("noodlelen") or next(iter(defaults["len"].keys()))

    sortlabel = data["sort"][sortvalue]["label"]
    hdlabel = data["hd"][hdvalue]["label"]
    lenlabel = data["len"][lenvalue]["label"]
    return "Sort: {} - Quality: {} - Length: {}".format(sortlabel, hdlabel, lenlabel)


def getDefaults():
    default_items = {}

    for category, options in data.items():
        for key, details in options.items():
            if details.get("default"):
                default_items[category] = {key: {"label": details["label"]}}
    return default_items

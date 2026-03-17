"""
Cumination site scraper
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

import json
import re
from six.moves import urllib_parse
import xbmc
import xbmcgui

from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite(
    "pmvhaven",
    "[COLOR hotpink]PMVHaven[/COLOR]",
    "https://pmvhaven.com/",
    "pmvhaven.png",
    "pmvhaven",
)


def _format_duration(video):
    duration = video.get("duration")
    if duration:
        return duration

    duration_seconds = video.get("durationSeconds")
    if duration_seconds in (None, ""):
        return ""

    try:
        duration_seconds = int(duration_seconds)
    except (TypeError, ValueError):
        return ""

    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return "{}:{:02d}:{:02d}".format(hours, minutes, seconds)
    return "{}:{:02d}".format(minutes, seconds)


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "api/videos/search?limit=32&page=1&q=",
        "Search",
        site.img_search,
    )
    List(
        site.url
        + "api/videos?limit=32&sort=-releaseDate&page=1&skipCount=true&tagMode=OR&expandTags=false"
    )
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    jdata = json.loads(listhtml)
    if not isinstance(jdata, dict):
        jdata = {}

    for video in jdata.get("videos", []):
        name = video.get("title", "")
        img = video.get("thumbnailUrl", "")
        video_url = video.get("videoUrl", video.get("hlsMasterPlaylistUrl", ""))
        duration = _format_duration(video)
        height = video.get("height")
        quality = "{}p".format(height) if height else ""
        if not name or not video_url:
            continue
        if video.get("hasExtremeContent", False):
            name += "[COLOR red] EXTREME[/COLOR]"
        tags = ",".join(video.get("tags", []))
        models = ",".join(video.get("starsTags", []))

        cm_lookupinfo = (
            utils.addon_sys
            + "?mode=pmvhaven.Lookupinfo&url={}".format(
                urllib_parse.quote_plus(tags + "|" + models)
            )
        )
        cm = [
            (
                "[COLOR deeppink]Lookup info[/COLOR]",
                "RunPlugin({})".format(cm_lookupinfo),
            )
        ]

        site.add_download_link(
            name,
            video_url,
            "Playvid",
            img,
            name,
            duration=duration,
            quality=quality,
            contextm=cm,
        )

    pagination = jdata.get("pagination")
    if not isinstance(pagination, dict):
        pagination = {}

    if pagination.get("hasNext"):
        next_page = pagination.get("page", 1) + 1
        next_url = re.sub(r"page=\d+", "page={}".format(next_page), url)
        cm_page = (
            utils.addon_sys
            + "?mode=pmvhaven.GotoPage&url="
            + urllib_parse.quote_plus(next_url)
        )
        cm = [("[COLOR violet]Goto Page #[/COLOR]", "RunPlugin(" + cm_page + ")")]
        site.add_dir(
            "Next Page ({})".format(next_page),
            next_url,
            "List",
            site.img_next,
            contextm=cm,
        )

    utils.eod()


@site.register()
def GotoPage(url):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        url = re.sub(r"page=\d+", "page={}".format(pg), url)
        contexturl = utils.addon_sys + "?mode=pmvhaven.List&url=" + urllib_parse.quote_plus(url)
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_direct_link(url)


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        List(url + keyword.replace(" ", "+"))


@site.register()
def Related(url):
    contexturl = utils.addon_sys + "?mode=pmvhaven.List&url=" + urllib_parse.quote_plus(url)
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Lookupinfo(url):
    tags, models = url.split("|")
    tags = tags.split(",") if tags else []
    models = models.split(",") if models else []

    lookup_list = {}
    for tag in tags:
        lookup_list["Tag - " + tag] = (
            site.url
            + "api/videos?limit=32&sort=-releaseDate&page=1&tagMode=OR&expandTags=false&tags={}".format(
                tag
            )
        )

    for model in models:
        lookup_list["Model - " + model] = (
            site.url + "api/videos/search?limit=32&page=1&q={}".format(model)
        )

    selected_item = utils.selector("Choose item", lookup_list, show_on_one=True)
    if not selected_item:
        return
    contexturl = (
        utils.addon_sys + "?mode=pmvhaven.List&url=" + urllib_parse.quote_plus(selected_item)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")

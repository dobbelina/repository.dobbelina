"""
Cumination
Copyright (C) 2016 Whitecream

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
import re
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "porndig",
    "[COLOR hotpink]Porndig[/COLOR] [COLOR white]Professional[/COLOR]",
    "https://www.porndig.com/",
    "porndig.png",
    "porndig",
)
site2 = AdultSite(
    "porndig2",
    "[COLOR hotpink]Porndig[/COLOR] [COLOR white]Amateurs[/COLOR]",
    "http://www.porndig.com/",
    "porndig.png",
    "porndig",
)

addon = utils.addon
headers = {"User-Agent": utils.USER_AGENT, "X-Requested-With": "XMLHttpRequest"}


def _normalize_section(section):
    try:
        return int(section)
    except (TypeError, ValueError):
        utils.kodilog(
            "porndig List: Invalid section {!r}, defaulting to videos".format(section)
        )
        return 0


@site.register(default_mode=True)
@site2.register(default_mode=True)
def Main(name):
    if "Amateurs" in name:
        addon.setSetting("pdsection", "1")
    else:
        addon.setSetting("pdsection", "0")
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "videos/",
        "Categories",
        site.img_cat,
    )
    if addon.getSetting("pdsection") == "0":
        site.add_dir(
            "[COLOR hotpink]Studios[/COLOR]",
            site.url + "studios/load_more_studios",
            "Studios",
            "",
            0,
        )
        site.add_dir(
            "[COLOR hotpink]Pornstars[/COLOR]",
            site.url + "pornstars/load_more_pornstars",
            "Pornstars",
            "",
            0,
        )
    List(1, 0, 0)


@site.register()
def Categories(url):
    if addon.getSetting("pdsection") == "1":
        url = site.url + "amateur/videos/"
    urldata = utils.getHtml(url, site.url)
    soup = utils.parse_html(urldata)

    # Find category options with category_slug
    category_options = soup.select("option[value]")
    for option in category_options:
        try:
            # Check if this is a category_slug option (parent select should have category_slug in name/id)
            parent_select = option.find_parent("select")
            if not parent_select or "category_slug" not in str(
                parent_select.get("name", "")
            ) + str(parent_select.get("id", "")):
                continue

            catchannel = utils.safe_get_attr(option, "value")
            if not catchannel:
                continue

            catname = utils.safe_get_text(option, "").strip()
            if not catname:
                continue

            site.add_dir(utils.cleantext(catname), "", "List", "", 0, catchannel, 3)
        except Exception as e:
            utils.kodilog("porndig Categories: Error processing category - {}".format(e))
            continue

    utils.eod()


def VideoListData(page, channel):
    sort = "date"
    offset = page * 36
    if addon.getSetting("pdsection") == "1":
        catid = 4
    else:
        catid = 1
    values = {
        "main_category_id": catid,
        "type": "post",
        "name": "category_videos",
        "filters[filter_type]": sort,
        "filters[filter_period]": "",
        "offset": offset,
    }
    return urllib_parse.urlencode(values)


def CatListData(page, channel):
    sort = "date"
    offset = page * 100
    if addon.getSetting("pdsection") == "1":
        catid = 4
    else:
        catid = 1
    values = {
        "main_category_id": catid,
        "type": "post",
        "name": "category_videos",
        "filters[filter_type]": sort,
        "filters[filter_period]": "",
        "offset": offset,
        "quantity": 100,
        "category_id[]": channel,
    }
    return urllib_parse.urlencode(values)


def VideoListStudio(page, channel):
    sort = "date"
    offset = page * 30
    values = {
        "main_category_id": "1",
        "type": "post",
        "name": "studio_related_videos",
        "filters[filter_type]": sort,
        "filters[filter_period]": "",
        "offset": offset,
        "content_id": channel,
    }
    return urllib_parse.urlencode(values)


def VideoListPornstar(page, channel):
    sort = "date"
    offset = page * 30
    values = {
        "main_category_id": "1",
        "type": "post",
        "name": "pornstar_related_videos",
        "filters[filter_type]": sort,
        "filters[filter_period]": "",
        "offset": offset,
        "content_id": channel,
    }
    return urllib_parse.urlencode(values)


def StudioListData(page):
    offset = page * 30
    values = {
        "main_category_id": "1",
        "type": "studio",
        "name": "top_studios",
        "filters[filter_type]": "likes",
        "starting_letter": "",
        "offset": offset,
    }
    return urllib_parse.urlencode(values)


def PornstarListData(page):
    offset = page * 30
    values = {
        "main_category_id": "1",
        "type": "pornstar",
        "name": "top_pornstars",
        "filters[filter_type]": "likes",
        "country_code": "",
        "starting_letter": "",
        "offset": offset,
    }
    return urllib_parse.urlencode(values)


@site.register()
def Pornstars(url, page=1):
    data = PornstarListData(page)
    urldata = utils.getHtml(url, site.url, headers, data=data)
    urldata = ParseJson(urldata)
    soup = utils.parse_html(urldata)

    i = 0
    # Find items with IDs starting with underscore and digit
    items = soup.select('[id^="_"]')
    for item in items:
        try:
            # Extract ID from element id (format: _12345)
            item_id = utils.safe_get_attr(item, "id")
            if not item_id or not item_id[1:].isdigit():
                continue
            ID = item_id[1:]  # Remove leading underscore

            img_tag = item.select_one("img")
            if not img_tag:
                continue
            img = utils.get_thumbnail(img_tag)
            # Remove query parameters from image URL
            if "?" in img:
                img = img.split("?")[0]

            studio = utils.safe_get_attr(img_tag, "alt", default="").strip()

            # Find videos count (look for "videos" text followed by count)
            videos_tag = item.select_one('p:-soup-contains("videos")')
            if not videos_tag:
                videos_tag = item.find(
                    "p",
                    string=lambda text: text and "videos" in text.lower()
                    if text
                    else False,
                )
            videos = utils.safe_get_text(videos_tag, "").strip()

            if not studio:
                continue

            title = "{0} [COLOR deeppink][I]{1} videos[/I][/COLOR]".format(
                studio, videos
            )
            site.add_dir(title, "", "List", img, 0, ID, 2)
            i += 1
        except Exception as e:
            utils.kodilog("porndig Pornstars: Error processing pornstar - {}".format(e))
            continue

    if i >= 30:
        page += 1
        name = "Next Page... ({0})".format(page + 1)
        site.add_dir(name, url, "Pornstars", site.img_next, page)
    utils.eod()


@site.register()
def Studios(url, page=1):
    data = StudioListData(page)
    urldata = utils.getHtml(url, site.url, headers, data=data)
    urldata = ParseJson(urldata)
    soup = utils.parse_html(urldata)

    i = 0
    # Find items with IDs starting with underscore and digit
    items = soup.select('[id^="_"]')
    for item in items:
        try:
            # Extract ID from element id (format: _12345)
            item_id = utils.safe_get_attr(item, "id")
            if not item_id or not item_id[1:].isdigit():
                continue
            ID = item_id[1:]  # Remove leading underscore

            img_tag = item.select_one("img")
            if not img_tag:
                continue
            img = utils.get_thumbnail(img_tag)
            # Remove query parameters from image URL
            if "?" in img:
                img = img.split("?")[0]

            studio = utils.safe_get_attr(img_tag, "alt", default="").strip()

            # Find videos count (look for "videos" text followed by count)
            videos_tag = item.select_one('p:-soup-contains("videos")')
            if not videos_tag:
                videos_tag = item.find(
                    "p",
                    string=lambda text: text and "videos" in text.lower()
                    if text
                    else False,
                )
            videos = utils.safe_get_text(videos_tag, "").strip()

            if not studio:
                continue

            title = "{0} [COLOR deeppink][I]{1} videos[/I][/COLOR]".format(
                studio, videos
            )
            site.add_dir(title, "", "List", img, 0, ID, 1)
            i += 1
        except Exception as e:
            utils.kodilog("porndig Studios: Error processing studio - {}".format(e))
            continue

    if i >= 30:
        page += 1
        name = "Next Page... ({0})".format(page + 1)
        site.add_dir(name, url, "Studios", site.img_next, page)
    utils.eod()


@site.register()
def List(channel, section, page=0):
    section = _normalize_section(section)

    if section == 0:
        data = VideoListData(page, channel)
        maxresult = 36
    elif section == 1:
        data = VideoListStudio(page, channel)
        maxresult = 30
    elif section == 2:
        data = VideoListPornstar(page, channel)
        maxresult = 30
    elif section == 3:
        data = CatListData(page, channel)
        maxresult = 100
    else:
        data = VideoListData(page, channel)
        maxresult = 36

    urldata = utils.getHtml(
        site.url + "posts/load_more_posts", site.url, headers, data=data
    )
    urldata = ParseJson(urldata)
    soup = utils.parse_html(urldata)

    i = 0
    # Find all section elements (video items)
    sections = soup.select("section")
    for section_item in sections:
        try:
            # Get video URL and name from link
            link = section_item.select_one("a[href]")
            if not link:
                continue

            url = utils.safe_get_attr(link, "href")
            if not url:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                continue
            name = name.replace("\u2019", "'")

            # Get quality badge class
            quality_badge = section_item.select_one(
                '[class*="quality"], [class*="hd"], [class*="4k"], [class*="full"]'
            )
            hd = ""
            if quality_badge:
                badge_class = utils.safe_get_attr(quality_badge, "class")
                if isinstance(badge_class, list):
                    badge_class = " ".join(badge_class).lower()
                else:
                    badge_class = str(badge_class).lower()

                if "full" in badge_class:
                    hd = "[COLOR yellow]FULLHD[/COLOR]"
                elif "4k" in badge_class:
                    hd = "[COLOR red]4K[/COLOR]"
                elif "hd" in badge_class:
                    hd = "[COLOR orange]HD[/COLOR]"

            # Get image
            img_tag = section_item.select_one("img")
            img = utils.get_thumbnail(img_tag)

            # Get duration
            duration_tag = section_item.select_one('[class*="tion"], .duration')
            if duration_tag:
                # Check for span inside duration tag
                span = duration_tag.select_one("span")
                duration = utils.safe_get_text(
                    span if span else duration_tag, ""
                ).strip()
            else:
                duration = ""

            if url.startswith("/"):
                url = site.url[:-1] + url

            site.add_download_link(
                name, url, "Playvid", img, name, duration=duration, quality=hd
            )
            i += 1
        except Exception as e:
            utils.kodilog("porndig List: Error processing video - {}".format(e))
            continue

    if i >= maxresult and channel:
        page += 1
        name = "Next Page... ({0})".format(page + 1)
        site.add_dir(
            name, "", "List", site.img_next, page=page, channel=channel, section=section
        )
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    soup = utils.parse_html(videopage)

    # Find iframe with data-url and class attributes
    iframe = soup.select_one("iframe[data-url][src]")
    if not iframe:
        # Try alternative selector
        iframe = soup.select_one("iframe[src]")

    if iframe:
        player_url = utils.safe_get_attr(iframe, "src")
        if player_url:
            playerpage = utils.getHtml(player_url, url)
        else:
            vp.progress.close()
            return
    else:
        vp.progress.close()
        return

    # Extract JSON from player page
    match = re.compile(
        r"window.player_args.push\((.+?)\);", re.DOTALL | re.IGNORECASE
    ).findall(playerpage)
    if not match:
        vp.progress.close()
        return

    videopagejson = json.loads(match[0])
    videourl = None

    for data in videopagejson["src"]:
        if data["codec"] == "h264":
            if "srcSet" in data.keys():
                srcset = data["srcSet"]
                links = {
                    x["label"].replace("4K", "2160p").replace("UHD", "2160p"): x["src"]
                    for x in srcset
                }
                videourl = utils.selector(
                    "Choose your video",
                    links,
                    setting_valid="qualityask",
                    sort_by=lambda x: int(x[:-1]),
                    reverse=True,
                )
            else:
                videourl = data["src"]

    if not videourl:
        vp.progress.close()
        return
    vp.play_from_direct_link(videourl)


def ParseJson(urldata):
    if not urldata:
        return ""

    if isinstance(urldata, bytes):
        urldata = urldata.decode("utf-8", "ignore")

    if isinstance(urldata, str):
        stripped = urldata.strip()
        if stripped.startswith("<"):
            return urldata
    else:
        utils.kodilog("porndig ParseJson: Unsupported response type")
        return ""

    try:
        parsed = json.loads(urldata)
    except (TypeError, ValueError) as exc:
        utils.kodilog("porndig ParseJson: Invalid JSON - {}".format(exc))
        return ""

    if not isinstance(parsed, dict):
        utils.kodilog("porndig ParseJson: Expected dict response")
        return ""

    content = (
        parsed.get("data", {}).get("content")
        or parsed.get("content")
        or parsed.get("html")
        or ""
    )
    if not isinstance(content, str):
        utils.kodilog("porndig ParseJson: Missing content payload")
        return ""
    return content

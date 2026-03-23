"""
Cumination
Copyright (C) 2015 Whitecream
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

import json
import xbmc
import xbmcgui
import random
import base64
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

addon = utils.addon
site = AdultSite(
    "beeg", "[COLOR hotpink]Beeg[/COLOR]", "https://store.externulls.com/", "beeg.png", "beeg"
)


def _load_json_payload(raw_payload, default):
    if not raw_payload:
        return default
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8", "ignore")
    if not isinstance(raw_payload, str):
        return default
    try:
        payload = json.loads(raw_payload)
    except (TypeError, ValueError) as exc:
        utils.kodilog("beeg: invalid JSON payload - {}".format(exc))
        return default
    return payload


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'tag/recommends?type=other&slug=index', 'Category', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'tag/recommends?type=brand&slug=index', 'Category', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'tag/recommends?type=person&slug=index', 'Category', site.img_cat)
    List('https://store.externulls.com/facts/tag?id=27173&limit=48&offset=0', 1)
    utils.eod()


@site.register()
def List(url, page=1):
    listjson = utils.getHtml(url, site.url)
    jdata = _load_json_payload(listjson, [])
    if not isinstance(jdata, list):
        jdata = []

    for video in jdata:
        tag = ""
        slug = ""
        fc_facts = video["fc_facts"]
        for t in video["tags"]:
            if t["is_owner"]:
                tag = t["tg_name"]
                slug = t["tg_slug"]
        tag = tag if utils.PY3 else tag.encode("utf8")

        story = ""
        for data in video["file"]["data"]:
            if data["cd_column"] == "sf_name":
                name = data["cd_value"]
            if data["cd_column"] == "sf_story":
                story = data["cd_value"]

        name = name if utils.PY3 else name.encode("utf8")
        name = "{} - {}".format(tag, name)
        story = story if utils.PY3 else story.encode("utf8")

        if "fl_duration" in video["file"]:
            m, s = divmod(video["file"]["fl_duration"], 60)
            duration = "{:d}:{:02d}".format(m, s)
        else:
            duration = ""

        h = video["file"].get("fl_height")
        quality = str(h) + "p" if h else ""
        plot = tag + " - " + name + "[CR]" + story

        thumb = str(random.choice(fc_facts[0]["fc_thumbs"]))
        videodump = json.dumps(video)
        videopage = base64.b64encode(videodump.encode())
        img = "https://thumbs.externulls.com/videos/{0}/{1}.webp?size=480x270".format(
            video["file"]["id"], thumb
        )
        parts = ""
        if len(fc_facts) > 1:
            parts = "[COLOR blue] ({} parts)[/COLOR]".format(len(fc_facts))
            for fc_fact in fc_facts:
                if "fc_start" not in fc_fact:
                    parts = ""

        if len(fc_facts) == 1 and "fc_start" in fc_facts[0] and "fc_end" in fc_facts[0]:
            if (
                fc_facts[0]["fc_start"] is not None
                and fc_facts[0]["fc_end"] is not None
            ):
                min_start, sec_start = divmod(fc_facts[0]["fc_start"], 60)
                min_end, sec_end = divmod(fc_facts[0]["fc_end"], 60)
                parts = "[COLOR blue] ({:d}:{:02d} - {:d}:{:02d})[/COLOR]".format(
                    min_start, sec_start, min_end, sec_end
                )

        name += parts

        # Get tag ID for fresh fetching in Playvid
        tag_id = ""
        for t in video["tags"]:
            if t["is_owner"]:
                tag_id = t["id"]
        if not tag_id and video["tags"]:
            tag_id = video["tags"][0]["id"]

        cm_related = (
            utils.addon_sys
            + "?mode="
            + str("beeg.ContextRelated")
            + "&slug="
            + urllib_parse.quote_plus(slug)
        )
        if tag:
            cm = [
                (
                    "[COLOR violet]Tag [COLOR orange][{}][/COLOR]".format(tag),
                    "RunPlugin(" + cm_related + ")",
                )
            ]
        else:
            cm = ""

        # Pass ID and tag_id in the URL for fresh fetching
        video_id = video["file"]["id"]
        videopage = "id={}&tag_id={}".format(video_id, tag_id)
        # Store full video data in cache as fallback
        utils.cache.set("beeg_video_{}".format(video_id), json.dumps(video))

        site.add_download_link(
            name,
            videopage,
            "Playvid",
            img,
            plot,
            contextm=cm,
            duration=duration,
            quality=quality,
        )
    if len(jdata) >= 48:
        if not page:
            page = 1
        page = min(page, 100)
        npage = url.split("offset=")[0] + "offset=" + str(page * 48)
        cm_page = (
            utils.addon_sys
            + "?mode=beeg.GotoPage"
            + "&url="
            + urllib_parse.quote_plus(npage)
            + "&np="
            + str(page)
        )
        cm = [("[COLOR violet]Goto Page #[/COLOR]", "RunPlugin(" + cm_page + ")")]
        site.add_dir(
            "Next Page ({})".format(str(page + 1)),
            npage,
            "List",
            site.img_next,
            page=page + 1,
            contextm=cm,
        )
    utils.eod()


@site.register()
def GotoPage(url, np):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        pg = min(int(pg), 101)
        url = url.replace(
            "offset={}".format(int(np) * 48), "offset={}".format(int(pg) * 48)
        )
        contexturl = (
            utils.addon_sys
            + "?mode="
            + "beeg.List&url="
            + urllib_parse.quote_plus(url)
            + "&page="
            + str(pg)
        )
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def ContextRelated(slug):
    url = "https://store.externulls.com/facts/tag?slug={}&get_original=true&limit=48&offset=0".format(
        slug
    )
    contexturl = (
        utils.addon_sys
        + "?mode="
        + str("beeg.List")
        + "&url="
        + urllib_parse.quote_plus(url)
    )
    xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Playvid(url, name, download=None):
    playall = utils.addon.getSetting("paradisehill") == "true"
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    jdata = None
    video_id = None
    
    # New format: id=123&tag_id=456
    if "id=" in url and "tag_id=" in url:
        try:
            params = dict(urllib_parse.parse_qsl(url))
            video_id = params.get("id")
            tag_id = params.get("tag_id")
            
            # Fetch fresh data
            api_url = "https://store.externulls.com/facts/file/{}?tag={}".format(video_id, tag_id)
            utils.kodilog("beeg Playvid: Fetching fresh URL from {}".format(api_url), xbmc.LOGDEBUG)
            fresh_json = utils.getHtml(api_url, site.url)
            jdata = json.loads(fresh_json)
        except Exception as e:
            utils.kodilog("beeg Playvid: Fresh fetch failed - {}".format(e))
            
    # Fallback to cache if fresh fetch failed
    if not jdata and video_id:
        cached = utils.cache.get("beeg_video_{}".format(video_id))
        if cached:
            utils.kodilog("beeg Playvid: Using cached data for {}".format(video_id), xbmc.LOGDEBUG)
            jdata = json.loads(cached)

    # Legacy fallback: base64 encoded data
    if not jdata:
        try:
            listjson = base64.b64decode(url)
            try:
                decoded_json = listjson.decode('utf-8')
            except UnicodeDecodeError:
                decoded_json = listjson.decode('latin-1', 'ignore')
            jdata = json.loads(decoded_json)
        except Exception as e:
            utils.kodilog("beeg Playvid: JSON decode error - {}".format(e))
            vp.progress.close()
            utils.notify("Error", "Unable to parse video data")
            return

    # Check if we have file data (fresh API returns file directly, List JSON has it under 'file')
    file_data = jdata.get("file", jdata)
    fc_facts = jdata.get("fc_facts", [])
    
    if not fc_facts and "fc_facts" in file_data:
        fc_facts = file_data["fc_facts"]

    if len(fc_facts) <= 1:
        if "hls_resources" in file_data:
            videos = file_data["hls_resources"]
        elif fc_facts and "hls_resources" in fc_facts[0]:
            videos = fc_facts[0]["hls_resources"]
        else:
            vp.progress.close()
            utils.notify("Error", "No stream resources found")
            return
        playall = False
    else:
        links = {}
        # Filter out facts without start/end times if multiple parts exist
        valid_facts = [f for f in fc_facts if f.get("fc_start") is not None]
        if not valid_facts:
            valid_facts = fc_facts
            
        for i, fc_fact in enumerate(sorted(valid_facts, key=lambda x: x.get("fc_start") if x.get("fc_start") is not None else 0)):
            start = fc_fact.get("fc_start") if fc_fact.get("fc_start") is not None else 0
            end = fc_fact.get("fc_end") if fc_fact.get("fc_end") is not None else 0
            m, s = divmod(int(start), 60)
            stxt = "{:d}:{:02d}".format(m, s)
            m, s = divmod(int(end), 60)
            etxt = "{:d}:{:02d}".format(m, s)
            part = " part {} ({} - {})".format(str(i + 1), stxt, etxt)
            links[part] = fc_fact.get("hls_resources", {})
            
        if len(links) < 2:
            playall = False
            videos = list(links.values())[0] if links else {}
        elif not playall:
            videos = utils.selector("Select part:", links)
            
    if not playall:
        if videos:
            videos = {key.replace("fl_cdn_", ""): videos[key] for key in videos.keys()}
            # Remove AV1 and H265 if they cause issues, but for now just handle multi
            if "multi" in videos.keys():
                maxres = videos["multi"].split("x")[-1].split(":")[0]
                if maxres in videos.keys():
                    del videos["multi"]
                elif maxres.isdigit():
                    videos[maxres] = videos.pop("multi")
            
            key = utils.prefquality(videos, sort_by=lambda x: int(x) if x.isdigit() else -1, reverse=True)
            if key:
                vp.progress.update(75, "[CR]Loading video page[CR]")
                path = key
                if not path.startswith("http"):
                    videourl = "https://video.beeg.com/" + path + "|Referer={}".format(site.url)
                else:
                    videourl = path + "|Referer={}".format(site.url)
                vp.play_from_direct_link(videourl)
            else:
                vp.progress.close()
                utils.notify("Error", "No preferred quality found")
        else:
            vp.progress.close()
            utils.notify("Error", "No video sources found")

    if playall:
        if links:
            iconimage = xbmc.getInfoImage("ListItem.Thumb")
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            for part_name in sorted(links.keys()):
                vp.progress.update(75, "[CR]Adding part to playlist[CR]")
                videos = links[part_name]
                videos = {
                    key.replace("fl_cdn_", ""): videos[key] for key in videos.keys()
                }
                if "multi" in videos.keys():
                    maxres = videos["multi"].split("x")[-1].split(":")[0]
                    if maxres in videos.keys():
                        del videos["multi"]
                    elif maxres.isdigit():
                        videos[maxres] = videos.pop("multi")
                
                key = utils.prefquality(videos, sort_by=lambda x: int(x) if x.isdigit() else -1, reverse=True)
                if key:
                    newname = name + part_name
                    listitem = xbmcgui.ListItem(newname)
                    listitem.setArt(
                        {
                            "thumb": iconimage,
                            "icon": "DefaultVideo.png",
                            "poster": iconimage,
                        }
                    )
                    if utils.KODIVER > 19.8:
                        vtag = listitem.getVideoInfoTag()
                        vtag.setTitle(newname)
                        vtag.setGenres(["Porn"])
                    else:
                        listitem.setInfo("video", {"Title": newname, "Genre": "Porn"})
                    listitem.setProperty("IsPlayable", "true")
                    
                    path = key
                    if not path.startswith("http"):
                        videourl = "https://video.beeg.com/" + path + "|Referer={}".format(site.url)
                    else:
                        videourl = path + "|Referer={}".format(site.url)
                    pl.add(videourl, listitem)
            xbmc.Player().play(pl)


@site.register()
def Category(url):
    listjson = utils.getHtml(url, site.url)
    jdata = _load_json_payload(listjson, [])
    if not isinstance(jdata, list):
        jdata = []
    # Filter out items that are not categories (missing tg_name)
    categories = [cat for cat in jdata if "tg_name" in cat]
    for cat in sorted(categories, key=lambda x: x["tg_name"]):
        name = cat["tg_name"]
        slug = cat["tg_slug"]
        thumbs = cat.get("thumbs", [])
        img = 'https://thumbs.externulls.com/photos/{}/to.webp'.format(random.choice(thumbs).get('id', 0)) if thumbs else site.img_cat
        caturl = 'https://store.externulls.com/facts/tag?slug={}&limit=48&offset=0'.format(slug)
        site.add_dir(name, caturl, 'List', img)
    utils.eod()

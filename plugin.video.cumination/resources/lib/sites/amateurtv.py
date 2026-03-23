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

import os
import sqlite3
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "amateurtv",
    "[COLOR hotpink]Amatuer TV[/COLOR]",
    "https://www.amateur.tv/",
    "amateurtv.png",
    "amateurtv",
    True,
)


def _load_json_payload(raw_payload):
    if not raw_payload:
        return {}
    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8", "ignore")
    if not isinstance(raw_payload, str):
        return {}
    try:
        payload = json.loads(raw_payload)
    except (TypeError, ValueError) as exc:
        utils.kodilog("amateurtv: invalid JSON payload - {}".format(exc))
        return {}
    return payload if isinstance(payload, dict) else {}


@site.register(default_mode=True)
def Main():
    female = utils.addon.getSetting("chatfemale") == "true"
    male = utils.addon.getSetting("chatmale") == "true"
    couple = utils.addon.getSetting("chatcouple") == "true"
    trans = utils.addon.getSetting("chattrans") == "true"
    site.add_dir(
        "[COLOR red]Refresh Amatuer TV images[/COLOR]",
        "",
        "clean_database",
        "",
        Folder=False,
    )
    if female:
        site.add_dir("[COLOR hotpink]Females[/COLOR]", "w", "List", "", 1)
    if couple:
        site.add_dir("[COLOR hotpink]Couples[/COLOR]", "c", "List", "", 1)
    if male:
        site.add_dir("[COLOR hotpink]Males[/COLOR]", "m", "List", "", 1)
    if trans:
        site.add_dir("[COLOR hotpink]Transsexual[/COLOR]", "t", "List", "", 1)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute(
                "SELECT id, cachedurl FROM texture WHERE url LIKE ?;",
                ("%" + ".amateur.tv" + "%",),
            )
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture = ?;", (row[0],))
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except Exception as e:
                    utils.kodilog(
                        "@@@@Cumination: Silent failure in amateurtv: " + str(e)
                    )
            conn.execute(
                "DELETE FROM texture WHERE url LIKE ?;", ("%" + ".amateur.tv" + "%",)
            )
            if showdialog:
                utils.notify("Finished", "Cam4 images cleared")
    except Exception as e:
        utils.kodilog("@@@@Cumination: Silent failure in amateurtv: " + str(e))


@site.register()
def List(url, page=1):
    if utils.addon.getSetting("chaturbate") == "true":
        clean_database(False)
    cam_url = "{0}v3/readmodel/cache/filteredcams?genre=[%22{1}%22]&page={2}".format(
        site.url, url, page
    )
    listhtml = utils._getHtml(cam_url, site.url)
    cams = _load_json_payload(listhtml).get("cams", {})
    nodes = cams.get("nodes") or []
    for cam in nodes:
        if cam.get("online"):
            model = cam.get("user")
            name = model.get("username")
            age = model.get("age")
            if age:
                name = "{0} [COLOR deeppink][{1}][/COLOR]".format(name, age[0])
            hd = ""
            if cam.get("hd"):
                hd = "HD"
            img = cam.get("imageURL").split("?")[0].replace("/en.", "/www.")

            subject = ""

            if cam.get("viewers", {}).get("totalNumber"):
                subject += "[COLOR deeppink]Viewers:[/COLOR] {0}[CR]".format(
                    cam.get("viewers", {}).get("totalNumber")
                )
            if cam.get("country"):
                subject += "[CR][COLOR deeppink]Country:[/COLOR] {0}[CR]".format(
                    cam.get("country")
                )
                name += " [COLOR blue][{0}][/COLOR]".format(cam.get("country"))
            if cam.get("quality"):
                subject += "[COLOR deeppink]Resolution:[/COLOR] {0}[CR]".format(
                    cam.get("quality")
                )
            if cam.get("topic", {}).get("text"):
                subject += "[CR]{0}[CR][CR]".format(
                    cam.get("topic", {}).get("text").encode("utf8")
                    if utils.PY2
                    else cam.get("topic", {}).get("text")
                )
            if cam.get("isInPrivateExclusive"):
                name += " [COLOR yellow][I]In Private[/I][/COLOR]"

            site.add_download_link(
                name,
                model.get("username"),
                "Playvid",
                img,
                subject,
                noDownload=True,
                quality=hd,
            )

    if (cams.get("totalCount") or 0) > (page * 150):
        page += 1
        site.add_dir("Next Page...", url, "List", site.img_next, page=page)

    utils.eod()


@site.register()
def Playvid(url, name):
    vp = utils.VideoPlayer(name)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    url = "{0}v3/readmodel/show/{1}/en".format(site.url, url)
    listhtml = utils._getHtml(url, site.url)
    vurls = _load_json_payload(listhtml).get("videoTechnologies")
    if vurls:
        # Try multiple possible keys for HLS streams
        vurl = vurls.get("fmp4-hls") or vurls.get("hls") or vurls.get("hls-fmp4")
        if vurl:
            vp.play_from_direct_link(vurl + "|User-Agent=iPad")
            return

    utils.notify("Oh Oh", "No Video found")
    vp.progress.close()
    return

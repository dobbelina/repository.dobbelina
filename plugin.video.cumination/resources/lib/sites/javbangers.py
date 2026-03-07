"""
Cumination site scraper
Copyright (C) 2020 Team Cumination

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
import xbmcplugin
import xbmc
import xbmcgui
from random import randint
from resources.lib import utils
from resources.lib.adultsite import AdultSite


site = AdultSite(
    "javbangers",
    "[COLOR hotpink]JAV Bangers[/COLOR]",
    "https://www.javbangers.com/",
    "javbangers.png",
    "javbangers",
)

getinput = utils._get_keyboard
jblogged = "true" in utils.addon.getSetting("jblogged")


@site.register(default_mode=True)
def Main():
    sort_orders = {
        "Recently updated": "last_content_date",
        "Most viewed": "playlist_viewed",
        "Top rated": "rating",
        "Most commented": "most_commented",
        "Most videos": "total_videos",
    }
    jbsortorder = (
        utils.addon.getSetting("jbsortorder")
        if utils.addon.getSetting("jbsortorder")
        else "last_content_date"
    )
    sortname = list(sort_orders.keys())[list(sort_orders.values()).index(jbsortorder)]

    context = utils.addon_sys + "?mode=" + str("javbangers.PLContextMenu")
    contextmenu = [("[COLOR orange]Sort order[/COLOR]", "RunPlugin(" + context + ")")]

    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "categories/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Playlists[/COLOR] [COLOR orange]{}[/COLOR]".format(sortname),
        site.url
        + "playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by={}&from=01".format(
            jbsortorder
        ),
        "Playlists",
        site.img_cat,
        contextm=contextmenu,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "search/{0}/",
        "Search",
        site.img_search,
    )
    if not jblogged:
        site.add_dir("[COLOR hotpink]Login[/COLOR]", "", "JBLogin", "", Folder=False)
    elif jblogged:
        jbuser = utils.addon.getSetting("jbuser")
        site.add_dir(
            "[COLOR violet]JB Favorites[/COLOR]",
            site.url
            + "my/favourites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_my_fav_videos=01",
            "List",
            site.img_cat,
        )
        site.add_dir(
            "[COLOR hotpink]Logout {0}[/COLOR]".format(jbuser),
            "",
            "JBLogin",
            "",
            Folder=False,
        )
    List(site.url + "latest-updates/")
    utils.eod()


@site.register()
def List(url):
    hdr = dict(utils.base_hdrs)
    hdr["Cookie"] = get_cookies()
    listhtml = utils.getHtml(url, site.url, headers=hdr)
    if jblogged and (">Log in<" in listhtml):
        if JBLogin(False):
            hdr["Cookie"] = get_cookies()
            listhtml = utils.getHtml(url, site.url, headers=hdr)
        else:
            return None

    soup = utils.parse_html(listhtml)

    # Find all video items
    video_items = soup.select('[class*="video-item"]')
    for item in video_items:
        try:
            # Get class to check for private
            item_class = utils.safe_get_attr(item, "class")
            if isinstance(item_class, list):
                item_class = " ".join(item_class)
            else:
                item_class = str(item_class) if item_class else ""

            # Check for private video
            if "private" in item_class.lower():
                if not jblogged:
                    continue
                private = "[COLOR blue] [PV][/COLOR] "
            else:
                private = ""

            # Get video link
            link = item.select_one("a[href][title]")
            if not link:
                continue
            videopage = utils.safe_get_attr(link, "href")
            if not videopage:
                continue

            name = utils.safe_get_attr(link, "title", default="")
            name = utils.cleantext(name)
            name = private + name

            # Get image - try both original and cover src
            img = ""
            img_tag = item.select_one("img[original]")
            if img_tag:
                img = utils.safe_get_attr(img_tag, "original")
            if not img:
                img_tag = item.select_one("img.cover[src]")
                if img_tag:
                    img = utils.safe_get_attr(img_tag, "src")

            # Check for HD badge
            hd = (
                "HD"
                if item.find(
                    string=lambda text: text and ">HD<" in text if text else False
                )
                or item.select_one('.hd, [class*="hd"]')
                else ""
            )

            # Get duration from clock icon/text
            duration_elem = item.select_one('[class*="clock"]')
            name2 = ""
            if duration_elem:
                duration_text = utils.safe_get_text(duration_elem, "").strip()
                # Extract time pattern (digits and colons)
                time_match = re.search(r"[\d:]+", duration_text)
                name2 = time_match.group(0) if time_match else ""

            contextmenu = []
            contexturl = (
                utils.addon_sys
                + "?mode="
                + str("javbangers.Lookupinfo")
                + "&url="
                + urllib_parse.quote_plus(videopage)
            )
            contextmenu.append(
                ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
            )
            if jblogged:
                contextadd = (
                    utils.addon_sys
                    + "?mode="
                    + str("javbangers.ContextMenu")
                    + "&url="
                    + urllib_parse.quote_plus(videopage)
                    + "&fav=add"
                )
                contextdel = (
                    utils.addon_sys
                    + "?mode="
                    + str("javbangers.ContextMenu")
                    + "&url="
                    + urllib_parse.quote_plus(videopage)
                    + "&fav=del"
                )
                contextmenu.append(
                    (
                        "[COLOR violet]Add to JB favorites[/COLOR]",
                        "RunPlugin(" + contextadd + ")",
                    )
                )
                contextmenu.append(
                    (
                        "[COLOR violet]Delete from JB favorites[/COLOR]",
                        "RunPlugin(" + contextdel + ")",
                    )
                )

            site.add_download_link(
                name,
                videopage,
                "Playvid",
                img,
                name,
                contextm=contextmenu,
                duration=name2,
                quality=hd,
            )
        except Exception as e:
            utils.kodilog("javbangers List: Error processing video - {}".format(e))
            continue

    next_link = soup.select_one("a.next")
    if next_link:
        block_id = utils.safe_get_attr(next_link, "data-block-id")
        params = utils.safe_get_attr(next_link, "data-parameters", default="")
        href = utils.safe_get_attr(next_link, "href", default="")
        params = params.replace(";", "&").replace(":", "=") if params else ""

        # Derive next page number from href or parameters
        npage = ""
        href_match = re.search(r"/(\d+)/", href)
        if href_match:
            npage = href_match.group(1)
        elif params:
            from_match = re.search(r"from=(\d+)", params)
            if from_match:
                npage = from_match.group(1)

        # Derive last page if available
        lastp = ""
        last_link = soup.find("a", string=re.compile("Last", re.IGNORECASE))
        if last_link:
            last_href = utils.safe_get_attr(last_link, "href", default="")
            last_match = re.search(r"/(\d+)/", last_href)
            if last_match:
                lastp = "/{}".format(last_match.group(1))

        if block_id and params:
            rnd = 1000000000000 + randint(0, 999999999999)
            nurl = url.split("?")[
                0
            ] + "?mode=async&function=get_block&block_id={0}&{1}&_={2}".format(
                block_id, params, str(rnd)
            )
            nurl = nurl.replace("+from_albums", "")
            if npage:
                nurl = re.sub(r"&from([^=]*)=\d+", r"&from\1={}".format(npage), nurl)
        else:
            nurl = urllib_parse.urljoin(site.url, href) if href else url

        cm_page = None
        if npage:
            cm_url = (
                utils.addon_sys
                + "?mode=javbangers.GotoPage"
                + "&url="
                + urllib_parse.quote_plus(nurl)
                + "&np="
                + str(npage)
                + "&lp="
                + str(lastp[1:] if lastp else "")
            )
            cm_page = [
                ("[COLOR violet]Goto Page #[/COLOR]", "RunPlugin(" + cm_url + ")")
            ]

        site.add_dir(
            "[COLOR hotpink]Next Page...[/COLOR] ("
            + str(npage or "?")
            + str(lastp)
            + ")",
            nurl,
            "List",
            site.img_next,
            contextm=cm_page,
        )
    utils.eod()


@site.register()
def GotoPage(url, np, lp=None):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, "Enter Page number")
    if pg:
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg="Out of range!")
            return
        url = re.sub(r"&from([^=]*)=\d+", r"&from\1={}".format(pg), url, re.IGNORECASE)
        contexturl = (
            utils.addon_sys
            + "?mode="
            + "javbangers.List&url="
            + urllib_parse.quote_plus(url)
        )
        xbmc.executebuiltin("Container.Update(" + contexturl + ")")


@site.register()
def Playvid(url, name, download=None):
    utils.kodilog('Playing video: ' + url)
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    hdr = dict(utils.base_hdrs)
    hdr['Cookie'] = get_cookies()
    vpage = utils.getHtml(url, site.url, headers=hdr)
    if "kt_player('kt_player'" in vpage:
        vp.progress.update(60, "[CR]{0}[CR]".format("kt_player detected"))
        vp.play_from_kt_player(vpage, url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, "")
    soup = utils.parse_html(cathtml)

    # Find all item links with title attribute
    items = soup.select(".item[href][title]")
    for link in items:
        try:
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue

            name = utils.safe_get_attr(link, "title", default="")
            name = utils.cleantext(name)
            if not name:
                continue

            # Get image
            img_tag = link.select_one("img[src]")
            img = utils.safe_get_attr(img_tag, "src", ["data-src"]) if img_tag else ""

            # Get video count
            videos_elem = link.select_one('[class*="videos"]')
            name2 = utils.safe_get_text(videos_elem, "").strip() if videos_elem else ""

            if name2:
                name = name + " [COLOR cyan][{}][/COLOR]".format(name2)

            site.add_dir(name, catpage, "List", img, 1)
        except Exception as e:
            utils.kodilog("javbangers Categories: Error processing category - {}".format(e))
            continue

    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playlists(url, page=1):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    # Find all playlist items
    items = soup.select(".item[href][title]")
    for link in items:
        try:
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue

            name = utils.safe_get_attr(link, "title", default="")
            name = utils.cleantext(name)
            if not name:
                continue

            # Get image from thumb video class with data-original
            img = ""
            for i in range(1, 5):
                img_tag = link.select_one(".thumb.video{0}[data-original]".format(i))
                if img_tag:
                    img = utils.safe_get_attr(img_tag, "data-original")
                    break
            if not img:
                img_tag = link.select_one("img[data-original]")
                if img_tag:
                    img = utils.safe_get_attr(img_tag, "data-original")

            # Get total playlist count
            total_elem = link.select_one(".totalplaylist")
            name2 = utils.safe_get_text(total_elem, "").strip() if total_elem else ""

            if name2:
                name = name + " [COLOR cyan][{}][/COLOR]".format(name2)

            site.add_dir(name, catpage, "List", img)
        except Exception as e:
            utils.kodilog("javbangers Playlists: Error processing playlist - {}".format(e))
            continue

    # Pagination
    next_li = soup.select_one("li.next")
    if next_li and next_li.select_one("a"):
        # Find last page number
        last_link = soup.find(
            "a", string=lambda text: text and ":" in text if text else False
        )
        lastp = ""
        if last_link:
            link_text = utils.safe_get_text(last_link, "").strip()
            last_match = re.search(r":(\d+)", link_text)
            lastp = "/{}".format(last_match.group(1)) if last_match else ""

        if not page:
            page = 1
        npage = page + 1
        if "from={0:02d}".format(page) in url:
            nurl = url.replace(
                "from={0:02d}".format(page), "from={0:02d}".format(npage)
            )
        else:
            utils.kodilog(" Playlists pagination error")
            nurl = url
        site.add_dir(
            "[COLOR hotpink]Next Page...[/COLOR] (" + str(npage) + lastp + ")",
            nurl,
            "Playlists",
            site.img_next,
            npage,
        )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "+")
        searchUrl = searchUrl.format(title)
        List(searchUrl)


@site.register()
def JBLogin(logged=True):
    jblogged = utils.addon.getSetting("jblogged")
    if not logged:
        jblogged = False
        utils.addon.setSetting("jblogged", "false")

    if not jblogged or "false" in jblogged:
        jbuser = (
            utils.addon.getSetting("jbuser") if utils.addon.getSetting("jbuser") else ""
        )
        jbpass = (
            utils.addon.getSetting("jbpass") if utils.addon.getSetting("jbpass") else ""
        )
        if jbuser == "":
            jbuser = getinput(default=jbuser, heading="Input your Javbangers username")
            jbpass = getinput(
                default=jbpass, heading="Input your Javbangers password", hidden=True
            )

        loginurl = "{0}ajax-login/".format(site.url)
        postRequest = {
            "action": "login",
            "email_link": "{0}email/".format(site.url),
            "format": "json",
            "mode": "async",
            "pass": jbpass,
            "remember_me": "1",
            "username": jbuser,
        }
        response = utils._postHtml(loginurl, form_data=postRequest)
        if "success" in response.lower():
            utils.addon.setSetting("jblogged", "true")
            utils.addon.setSetting("jbuser", jbuser)
            utils.addon.setSetting("jbpass", jbpass)
            success = True
        else:
            utils.notify(
                "Failure logging in", "Failure, please check your username or password"
            )
            utils.addon.setSetting("jbuser", "")
            utils.addon.setSetting("jbpass", "")
            success = False
    elif jblogged:
        clear = utils.selector(
            "Clear stored user & password?", ["Yes", "No"], reverse=True
        )
        if clear:
            if clear == "Yes":
                utils.addon.setSetting("jbuser", "")
                utils.addon.setSetting("jbpass", "")
            utils.addon.setSetting("jblogged", "false")
            utils._getHtml(site.url + "logout/")
    if logged:
        xbmc.executebuiltin("Container.Refresh")
    else:
        return success


@site.register()
def ContextMenu(url, fav):
    id = url.split("/")[4]
    fav_addurl = (
        url
        + "?mode=async&format=json&action=add_to_favourites&video_id="
        + id
        + "&album_id=&fav_type=0&playlist_id=0"
    )
    fav_delurl = (
        url
        + "?mode=async&format=json&action=delete_from_favourites&video_id="
        + id
        + "&album_id=&fav_type=0&playlist_id=0"
    )
    fav_url = fav_addurl if fav == "add" else fav_delurl

    hdr = dict(utils.base_hdrs)
    hdr["Cookie"] = get_cookies()
    resp = utils.getHtml(fav_url, site.url, headers=hdr)

    if fav == "add":
        if ("success") in resp:
            utils.notify("Favorites", "Added to JB Favorites")
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify("Favorites", msg)
        return
    if fav == "del":
        if ("success") in resp:
            utils.notify("Deleted from JB Favorites")
            xbmc.executebuiltin("Container.Refresh")
        else:
            msg = re.findall('message":"([^"]+)"', resp)[0]
            utils.notify(msg)
        return


@site.register()
def PLContextMenu():
    sort_orders = {
        "Recently updated": "last_content_date",
        "Most viewed": "playlist_viewed",
        "Top rated": "rating",
        "Most commented": "most_commented",
        "Most videos": "total_videos",
    }
    order = utils.selector("Select order", sort_orders)
    if order:
        utils.addon.setSetting("jbsortorder", order)
        xbmc.executebuiltin("Container.Refresh")


def get_cookies():
    domain = site.url.split("www")[-1][:-1]
    cookiestr = "kt_tcookie=1"
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == "PHPSESSID":
            cookiestr += "; PHPSESSID=" + cookie.value
        if cookie.domain == domain and cookie.name == "kt_ips":
            cookiestr += "; kt_ips=" + cookie.value
        if cookie.domain == domain and cookie.name == "kt_member":
            cookiestr += "; kt_member=" + cookie.value
    if jblogged and "kt_member" not in cookiestr:
        JBLogin(False)
    return cookiestr


@site.register()
def Lookupinfo(url):
    class SiteLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if "members/" in url:
                return site.url + url + "/videos/"
            if any(x in url for x in ["models/", "tags/", "categories/"]):
                return site.url + url

    lookup_list = [
        ("Cat", '/(categories/[^"]+)">([^<]+)<', ""),
        ("Tag", '/(tags[^"]+)">[^<]+<[^<]+</i>([^<]+)<', ""),
        ("Actor", '/(models/[^"]+)">([^<]+)<', ""),
        ("Uploader", '/(members/[^"]+)">([^<]+)<', ""),
    ]

    lookupinfo = SiteLookup(site.url, url, "javbangers.List", lookup_list)
    lookupinfo.getinfo()

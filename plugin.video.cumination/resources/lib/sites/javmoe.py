"""
Cumination Site Plugin
Copyright (C) 2018 Team Cumination

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
import string
import codecs
import time
from six.moves import urllib_parse
from resources.lib import utils, jsunpack
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "javmoe",
    "[COLOR hotpink]JAV Moe[/COLOR]",
    "https://javmama.me/",
    "javmoe.png",
    "javmoe",
)

enames = {
    "FS": "FileStar",
    "r": "RapidVideo",
    "ST": "Motonews",
    "sw": "StreamWish",
    "tb": "TurboVid",
    "vg": "VidGuard",
}


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Genres[/COLOR]",
        site.url + "genres/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]", site.url + "pornstars/", "Letters", "", ""
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "?s={}&post_type=post",
        "Search",
        site.img_search,
    )
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    items = 0
    visited = set()
    while items < 36 and url:
        if url in visited:
            break
        visited.add(url)
        try:
            listhtml = utils.getHtml(url, site.url)
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in javmoe: " + str(e))
            return None

        soup = utils.parse_html(listhtml)

        # Find all divs with class "epshen"
        divs = soup.select('.epshen, div[class*="epshen"]')
        for div in divs:
            try:
                # Get link
                link = div.select_one("a[href]")
                if not link:
                    continue
                videopage = utils.safe_get_attr(link, "href")
                if not videopage:
                    continue

                # Get image
                img_tag = div.select_one("img")
                img = utils.get_thumbnail(img_tag)
                if not img:
                    continue

                # Get name from title element
                title_elem = div.select_one('.title, [class*="title"]')
                if not title_elem:
                    continue
                name = utils.safe_get_text(title_elem, "").strip()
                name = utils.cleantext(name)
                if not name:
                    continue

                img = urllib_parse.quote(img, safe=":/")
                videopage = urllib_parse.quote(videopage, safe=":/")
                site.add_download_link(name, videopage, "Playvid", img, name)
                items += 1
            except Exception as e:
                utils.kodilog("javmoe List: Error processing video - {}".format(e))
                continue

        # Find next page link
        next_link = soup.select_one(".next.page-numbers[href], a.next[href]")
        if next_link:
            url = utils.safe_get_attr(next_link, "href")
        else:
            url = None

    if url:
        site.add_dir("Next Page", url, "List", site.img_next)
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
def Categories(url):
    cathtml = utils.getHtml(url, "")
    soup = utils.parse_html(cathtml)

    # Find all list items with links
    list_items = soup.select("li")
    for item in list_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                continue

            site.add_dir(name, catpage, "List", site.img_cat)
        except Exception as e:
            utils.kodilog("javmoe Categories: Error processing category - {}".format(e))
            continue

    utils.eod()


@site.register()
def Letters(url):
    site.add_dir("#", r"\d", "Pornstars", site.img_cat)
    for name in string.ascii_uppercase:
        site.add_dir(name, name, "Pornstars", site.img_cat)
    utils.eod()


@site.register()
def Pornstars(url):
    caturl = site.url + "pornstars/"
    cathtml = utils.getHtml(caturl, "")
    soup = utils.parse_html(cathtml)

    # Find all list items with links matching the letter pattern
    list_items = soup.select("li")
    for item in list_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue

            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue

            name = utils.safe_get_text(link, "").strip()
            if not name:
                continue

            # Check if name matches the letter pattern
            # url is either a letter or '\d' for numbers
            if url == r"\d":
                # Check if name starts with a digit
                if not name[0].isdigit():
                    continue
            else:
                # Check if name starts with the specified letter (case insensitive)
                if not name.upper().startswith(url.upper()):
                    continue

            site.add_dir(name, catpage.strip(), "List")
        except Exception as e:
            utils.kodilog("javmoe Pornstars: Error processing pornstar - {}".format(e))
            continue

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)

    # Parse embed URLs from list items
    soup = utils.parse_html(videopage)
    eurls = []
    list_items = soup.select("li")
    for item in list_items:
        try:
            link = item.select_one("a[href]")
            if not link:
                continue
            eurl = utils.safe_get_attr(link, "href")
            ename = utils.safe_get_text(link, "").strip()
            if eurl and ename:
                eurls.append((eurl, ename))
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in javmoe: " + str(e))
            continue

    sources = {
        enames.get(ename): eurl for eurl, ename in eurls if ename in list(enames)
    }
    eurl = utils.selector("Select Hoster", sources)
    if not eurl:
        vp.progress.close()
        return

    vp.progress.update(50, "[CR]Loading embed page[CR]")
    if eurl != "?server=1":
        videopage = utils.getHtml(url + eurl, site.url)
    videourl = ""
    v = re.compile('<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).search(
        videopage
    )
    if v:
        videourl = v.group(1)
    else:
        v = re.compile(
            r"""vg\s*id='<div\s*id="(?P<embed>[^"]+)"\s*domain="(?P<domain>[^"]+)"""
        ).search(videopage)
        if v:
            videourl = "https://{0}/e/{1}$${2}".format(
                v.group("domain"), vg_id(v.group("embed")), site.url
            )

    if "filestar.club" in videourl:
        videourl = utils.getVideoLink(videourl, url)

    if "gdriveplayer.to" in videourl:
        videourl = videourl.split("data=")[-1]
        while "%" in videourl:
            videourl = urllib_parse.unquote(videourl)
        videohtml = utils.getHtml("https:" + videourl, site.url)
        ptext = jsunpack.unpack(videohtml).replace("\\", "")
        ct = re.findall(r'"ct":"([^"]+)', ptext)[0]
        salt = codecs.decode(re.findall(r'"s":"([^"]+)', ptext)[0], "hex")
        pf = re.findall(r"""null,\s*['"]([^'"]+)""", ptext, re.S)[0]
        pf = re.compile(r"[a-zA-Z]{1,}").split(pf)
        passphrase = "".join([chr(int(c)) for c in pf])
        passphrase = re.findall(r'var\s+pass\s*=\s*"([^"]+)', passphrase)[0]
        from resources.lib.jscrypto import jscrypto

        etext = jscrypto.decode(ct, passphrase, salt)
        ctext = jsunpack.unpack(etext).replace("\\", "")
        frames = re.findall(r"sources:\s*(\[[^]]+\])", ctext)[0]
        frames = re.findall(r'file":"([^"]+)[^}]+label":"(\d+p)"', frames)
        t = int(time.time() * 1000)
        sources = {
            qual: "{0}{1}&ref={2}&res={3}".format(
                source, t, site.url, qual[:-1] if qual.endswith("p") else qual
            )
            for source, qual in frames
        }
        surl = utils.prefquality(sources)
        source = surl.split("&t=")[0]
        qual = surl.split("=")[-1]
        vp.progress.update(75, "[CR]Processed embed page[CR]")
        if surl:
            if surl.startswith("//"):
                surl = "https:" + surl
            if not surl.startswith("http"):
                surl = "https://gdriveplayer.to/" + surl
            attempt = 1
            while "redirect" in surl:
                surl = utils.getVideoLink(surl, headers={"Range": "bytes=0-"})
                if "server" not in surl:
                    attempt += 1
                    t = int(time.time() * 1000)
                    surl = "{0}&t={1}&ref={2}%26play_error_file%3Dyes&try={3}&res={4}".format(
                        source, t, site.url, attempt, qual
                    )
                elif "redirector." in surl:
                    surl = ""
            if surl:
                vp.play_from_direct_link(surl)
                return
        vp.progress.close()
        utils.notify("Oh oh", "No video found")
        return
    elif "motonews" in videourl:
        if videourl.startswith("//"):
            videourl = "https:" + videourl
        epage = utils.getHtml(videourl, url)
        s = re.findall(r'file":"(?P<url>[^"]+)","label":"(?P<label>[^"]+)', epage)
        vp.progress.update(75, "[CR]Processed embed page[CR]")
        if s:
            sources = {qual: source.replace("\\/", "/") for source, qual in s}
            surl = utils.prefquality(sources)
            if surl.startswith("//"):
                surl = "https:" + surl
            vp.play_from_direct_link(
                surl
                + "|Referer={0}&verifypeer=false".format(
                    urllib_parse.urljoin(videourl, "/")
                )
            )
        else:
            vp.progress.close()
            utils.notify("Oh oh", "No video found")
            return
    elif videourl:
        vp.progress.update(75, "[CR]Processed embed page[CR]")
        vp.play_from_link_to_resolve(videourl)


def vg_id(sid):
    fid = ""
    for g in range(0, len(sid), 2):
        fid += hex(int(sid[g : g + 2], 16) ^ 6)[2:]
    return fid

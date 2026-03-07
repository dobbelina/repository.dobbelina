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
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite(
    "porno1hu", "[COLOR hotpink]Porno1.hu[/COLOR]", "https://porno1.hu/", "porno1hu.png"
)


@site.register(default_mode=True)
def Main(url):
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]",
        site.url + "kategoriak/",
        "Categories",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "kereses/",
        "Search",
        site.img_search,
    )
    List(
        site.url
        + "friss-porno/?mode=async&function=get_block&block_id=list_videos_latest_videos_list&sort_by=post_date&from=1",
        1,
    )
    utils.eod()


@site.register()
def List(url, page=1):
    try:
        listhtml = utils.getHtml(url, "")
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in porno1hu: " + str(e))
        return None

    soup = utils.parse_html(listhtml)

    for item in soup.select(".item"):
        link = item.select_one("a[href]")
        if not link:
            continue
        videopage = urljoin(site.url, utils.safe_get_attr(link, "href"))
        name = utils.cleantext(
            utils.safe_get_attr(link, "title") or utils.safe_get_text(link, default="")
        )
        img_tag = item.select_one("img")
        img = utils.safe_get_attr(img_tag, "data-original", ["data-src", "src"])
        duration = utils.safe_get_text(item.select_one(".duration"), default="").strip()

        contextmenu = []
        contexturl = (
            utils.addon_sys
            + "?mode=porno1hu.Lookupinfo"
            + "&url="
            + urllib_parse.quote_plus(videopage)
        )
        contextmenu.append(
            ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
        )

        site.add_download_link(
            name,
            videopage,
            "Playvid",
            img,
            name,
            contextm=contextmenu,
            duration=duration,
        )

    next_link = soup.select_one("a.next, li.next a")
    if next_link:
        next_href = utils.safe_get_attr(next_link, "href")
        if not next_href:
            params = next_link.get("data-parameters")
            if params:
                parsed = dict(p.split("=") for p in params.split(";") if "=" in p)
                base = urlparse(url)
                query = urllib_parse.parse_qs(base.query)
                for key in ("from", "from_videos"):
                    if key in parsed:
                        query[key] = [parsed[key]]
                query_str = urlencode(query, doseq=True)
                next_href = urlunparse(
                    (
                        base.scheme,
                        base.netloc,
                        base.path,
                        base.params,
                        query_str,
                        base.fragment,
                    )
                )
        if next_href:
            site.add_dir(
                "Next Page",
                urljoin(site.url, next_href),
                "List",
                site.img_next,
                page=page + 1,
            )

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    
    # Try direct API first if it's a standard video URL
    video_id_match = re.search(r"/szexvideo/(\d+)/", url)
    if video_id_match:
        video_id = video_id_match.group(1)
        api_url = "https://porno1.hu/api/videofile.php?video_id={}&lifetime=8640000".format(video_id)
        try:
            jsondata = utils.getHtml(api_url, url)
            r = re.search('video_url":"([^"]+)', jsondata)
            if r:
                from resources.lib.decrypters import txxx
                videourl = txxx.Tdecode(r.group(1))
                if not videourl.startswith("http"):
                    videourl = "https://porno1.hu" + videourl
                vp.play_from_direct_link(videourl + "|referer=https://porno1.hu/")
                return
        except Exception:
            pass

    html = utils.getHtml(url, site.url)
    soup = utils.parse_html(html)
    
    meta = soup.find("meta", attrs={"property": "embedURL"}) or soup.find(
        "meta", attrs={"name": "embedURL"}
    )
    embedurl = utils.safe_get_attr(meta, "content") if meta else None
    if not embedurl:
        iframe = soup.find("iframe", src=True)
        embedurl = utils.safe_get_attr(iframe, "src") if iframe else None
    
    if not embedurl:
        # Fallback: scan main page html
        vp.play_from_html(html)
        return

    embedhtml = utils.getHtml(embedurl, url)
    license_match = re.search(r"license_code:\s*['\"]([^\"']+)['\"]", embedhtml, re.IGNORECASE)
    if not license_match:
        vp.play_from_html(embedhtml)
        return

    vp.play_from_kt_player(embedhtml, url)
    return


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, "")
    except Exception as e:
        utils.kodilog("@@@@Cumination: failure in porno1hu: " + str(e))
        return None
    soup = utils.parse_html(cathtml)
    for item in soup.select("a.item[href][title]"):
        catpage = utils.safe_get_attr(item, "href")
        name = utils.cleantext(utils.safe_get_attr(item, "title"))
        videos = utils.safe_get_text(
            item.select_one(".videos, .count"), default=""
        ).strip()
        if videos:
            name = name + " [COLOR hotpink](" + videos + ")[/COLOR]"
        catpage = (
            urljoin(site.url, catpage)
            + "?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1"
        )
        site.add_dir(name, catpage, "List", "", page=1)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(searchUrl, "Search")
    else:
        title = keyword.replace(" ", "-")
        searchUrl = (
            searchUrl
            + title
            + "?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&category_ids=&sort_by=&from_videos=1"
        )
        List(searchUrl, 1)


@site.register()
def Lookupinfo(url):
    class porno1huLookup(utils.LookupInfo):
        def url_constructor(self, url):
            if "kategoriak/" in url or "cimke/" in url:
                return (
                    url
                    + "?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=1"
                )

    lookup_list = [
        ("Cat", r'<a href="(https://porno1.hu/kategoriak/[^"]+)">([^<]+)<', ""),
        ("Tag", r'<a href="(https://porno1.hu/cimke/[^"]+)">([^<]+)<', ""),
    ]

    lookupinfo = porno1huLookup("", url, "porno1hu.List", lookup_list)
    lookupinfo.getinfo()

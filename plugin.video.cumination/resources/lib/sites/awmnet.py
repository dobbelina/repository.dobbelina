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
import xbmcplugin
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.decrypters import txxx


site = AdultSite(
    "awmnet",
    "[COLOR hotpink]AWM Network[/COLOR] - [COLOR deeppink]49 sites[/COLOR]",
    "https://www.4tube.com/",
    "awmnet.png",
    "awmnet",
)

sitelist = [
    [
        "4tube",
        "https://www.4tube.com/templates/4tube/images/logo.png",
        "https://www.4tube.com/",
    ],
    [
        "AI PornVideos",
        "https://www.aipornvideos.com/images/aipornvideos/logo.png",
        "https://www.aipornvideos.com/",
    ],
    [
        "Anal Galore",
        "https://www.analgalore.com/templates/analgalore/images/logo.png",
        "https://www.analgalore.com/",
    ],
    [
        "Asian Galore",
        "https://www.asiangalore.com/templates/asiangalore/images/logo.png",
        "https://www.asiangalore.com/",
    ],
    [
        "Ass O Ass",
        "https://www.assoass.com/templates/assoass/images/logo.png",
        "https://www.assoass.com/",
    ],
    [
        "BBW PornVideos",
        "https://www.bbwpornvideos.com/images/bbwpornvideos/logo.png",
        "https://www.bbwpornvideos.com/",
    ],
    [
        "BigCockXXX",
        "https://www.bigcockxxx.com/images/bigcockxxx/logo.png",
        "https://www.bigcockxxx.com/",
    ],
    [
        "Biporn",
        "https://www.biporn.com/templates/biporn/images/logo.png",
        "https://www.biporn.com/",
    ],
    [
        "Cartoon Porn Videos",
        "https://www.cartoonpornvideos.com/templates/cartoonpornvideos/images/logo.png",
        "https://www.cartoonpornvideos.com/",
    ],
    [
        "CoqNu",
        "https://www.coqnu.com/templates/coqnu/images/logo.png",
        "https://www.coqnu.com/",
    ],
    [
        "Dino Tube",
        "https://www.dinotube.com/templates/dinotube/images/logo.png",
        "https://www.dinotube.com/",
    ],
    [
        "Ebony Galore",
        "https://www.ebonygalore.com/templates/ebonygalore/images/logo.png",
        "https://www.ebonygalore.com/",
    ],
    [
        "EL Ladies",
        "https://www.el-ladies.com/templates/el-ladies/images/logo.png",
        "https://www.el-ladies.com/",
    ],
    [
        "For Her Tube",
        "https://www.forhertube.com/templates/forhertube/images/logo.png",
        "https://www.forhertube.com/",
    ],
    [
        "Fucd",
        "https://www.fucd.com/templates/fucd/images/logo.png",
        "https://www.fucd.com/",
    ],
    [
        "Full Porn Videos",
        "https://www.fullpornvideos.com/templates/fullpornvideos/images/logo.png",
        "https://www.fullpornvideos.com/",
    ],
    [
        "Fuq",
        "https://www.fuq.com/templates/fuq/images/logo.png",
        "https://www.fuq.com/",
    ],
    [
        "Fux",
        "https://www.fux.com/templates/fux/images/logo.png",
        "https://www.fux.com/",
    ],
    [
        "GayMale Tube",
        "https://www.gaymaletube.com/templates/gaymaletube/images/logo.png",
        "https://www.gaymaletube.com/",
    ],
    [
        "Got Porn",
        "https://www.gotporn.com/templates/gotporn/images/logo.png",
        "https://www.gotporn.com/",
    ],
    [
        "Hentai Galore",
        "https://www.hentaigalore.com/images/hentaigalore/logo.png",
        "https://www.hentaigalore.com/",
    ],
    [
        "Homemade Galore",
        "https://www.homemadegalore.com/templates/homemadegalore/images/logo.png",
        "https://www.homemadegalore.com/",
    ],
    [
        "iXXX",
        "https://www.ixxx.com/templates/ixxx/images/logo.png",
        "https://www.ixxx.com/",
    ],
    [
        "Latin Galore",
        "https://www.latingalore.com/templates/latingalore/images/logo.png",
        "https://www.latingalore.com/",
    ],
    [
        "Lesbian Porn Videos",
        "https://www.lesbianpornvideos.com/templates/lesbianpornvideos/images/logo.png",
        "https://www.lesbianpornvideos.com/",
    ],
    [
        "Lobster Tube",
        "https://www.lobstertube.com/templates/lobstertube/images/logo.png",
        "https://www.lobstertube.com/",
    ],
    [
        "Lupo Porno",
        "https://www.lupoporno.com/templates/lupoporno/images/logo.png",
        "https://www.lupoporno.com/",
    ],
    [
        "Mature Tube",
        "https://www.maturetube.com/templates/maturetube/images/logo.png",
        "https://www.maturetube.com/",
    ],
    [
        "Melons Tube",
        "https://www.melonstube.com/templates/melonstube/images/logo.png",
        "https://www.melonstube.com/",
    ],
    [
        "Meta Porn",
        "https://www.metaporn.com/templates/metaporn/images/logo.png",
        "https://www.metaporn.com/",
    ],
    [
        "Model Galore",
        "https://www.modelgalore.com/templates/modelgalore/images/logo.png",
        "https://www.modelgalore.com/",
    ],
    [
        "New Porno",
        "https://www.newporno.com/templates/newporno/images/logo.png",
        "https://www.newporno.com/",
    ],
    [
        "Porn HD",
        "https://www.pornhd.com/templates/pornhd/images/logo.png",
        "https://www.pornhd.com/",
    ],
    [
        "Porn MD",
        "https://www.pornmd.com/templates/pornmd/images/logo.png",
        "https://www.pornmd.com/",
    ],
    [
        "Porn TV",
        "https://www.porntv.com/templates/porntv/images/logo.png",
        "https://www.porntv.com/",
    ],
    [
        "Porzo",
        "https://www.porzo.com/templates/porzo/images/logo.png",
        "https://www.porzo.com/",
    ],
    [
        "Qorno",
        "https://www.qorno.com/templates/qorno/images/logo.png",
        "https://www.qorno.com/",
    ],
    [
        "Samba Porno",
        "https://www.sambaporno.com/templates/sambaporno/images/logo.png",
        "https://www.sambaporno.com/",
    ],
    [
        "Short Porn",
        "https://www.shortporn.com/templates/shortporn/images/logo.png",
        "https://www.shortporn.com/",
    ],
    [
        "Stocking Tease",
        "https://www.stocking-tease.com/templates/stocking-tease/images/logo.png",
        "https://www.stocking-tease.com/",
    ],
    [
        "TG Tube",
        "https://www.tgtube.com/templates/tgtube/images/logo.png",
        "https://www.tgtube.com/",
    ],
    [
        "Tiava",
        "https://www.tiava.com/templates/tiava/images/logo.png",
        "https://www.tiava.com/",
    ],
    [
        "Toro Porno",
        "https://www.toroporno.com/templates/toroporno/images/logo.png",
        "https://www.toroporno.com/",
    ],
    [
        "Tube BDSM",
        "https://www.tubebdsm.com/templates/tubebdsm/images/logo.png",
        "https://www.tubebdsm.com/",
    ],
    [
        "Tube Galore",
        "https://www.tubegalore.com/templates/tubegalore/images/logo.png",
        "https://www.tubegalore.com/",
    ],
    [
        "Tube Porn",
        "https://www.tubeporn.com/templates/tubeporn/images/logo.png",
        "https://www.tubeporn.com/",
    ],
    [
        "Tube Pornstars",
        "https://www.tubepornstars.com/templates/tubepornstars/images/logo.png",
        "https://www.tubepornstars.com/",
    ],
    [
        "VR XXX",
        "https://www.vrxxx.com/templates/vrxxx/images/logo.png",
        "https://www.vrxxx.com/",
    ],
    [
        "XXXmilfs",
        "https://www.xxxmilfs.com/images/xxxmilfs/logo.png?69f905d4",
        "https://www.xxxmilfs.com/",
    ],
]


def getBaselink(url):
    if not url:
        return sitelist[0][2]
    for pornsite in sitelist:
        domain = urllib_parse.urlparse(pornsite[2]).netloc
        if domain in url:
            return pornsite[2]
    parsed = urllib_parse.urlparse(url)
    if parsed.scheme and parsed.netloc:
        return "{0}://{1}/".format(parsed.scheme, parsed.netloc)
    return sitelist[0][2]


@site.register(default_mode=True)
def Main():
    for pornsite in sorted(sitelist):
        site.add_dir(
            "[COLOR hotpink]{0}[/COLOR]".format(pornsite[0]),
            pornsite[2],
            "SiteMain",
            pornsite[1],
        )
    utils.eod()


@site.register()
def SiteMain(url):
    siteurl = getBaselink(url)
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]", siteurl, "Categories", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Pornstars[/COLOR]", siteurl + "pornstar", "Tags", site.img_cat
    )
    site.add_dir("[COLOR hotpink]Tags[/COLOR]", siteurl + "a-z", "Tags", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]", siteurl + "search/", "Search", site.img_search
    )
    List(siteurl + "new?pricing=free")


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, siteurl)
    soup = utils.parse_html(listhtml)

    # Find all video items with item-link class
    items = soup.select('a.item-link, a[class*="item-link"]')

    seen = set()
    for item in items:
        videourl = utils.safe_get_attr(item, "href")
        name = utils.safe_get_attr(item, "title")

        if not videourl or not name:
            continue

        # Skip duplicates
        if videourl in seen:
            continue
        seen.add(videourl)

        img_tag = item.select_one("img")
        thumb = utils.safe_get_attr(
            img_tag, "src", ["data-src", "data-original", "data-lazy-src", "data-lazy"]
        )

        is_paid_video = False
        for node in item.find_all(True, class_=True):
            class_names = node.get("class", [])
            if any("font-[100]" in class_name for class_name in class_names):
                is_paid_video = True
                break

        # Get provider info (span/div with text-xsm after the link)
        provider = ""
        provider_tag = item.find_next(class_=re.compile(r"text-xsm"))
        if provider_tag:
            provider = utils.safe_get_text(provider_tag, "").strip()

        # Build name with provider
        if provider:
            name = "[COLOR yellow][{}][/COLOR] {}".format(
                provider, utils.cleantext(name)
            )
        else:
            name = utils.cleantext(name)
        if is_paid_video:
            name = "[COLOR red](Paid Video)[/COLOR] " + name

        # Get duration and HD info from float-right section
        info_div = item.find_next(class_="float-right")
        hd = ""
        duration = ""
        if info_div:
            info_text = utils.safe_get_text(info_div)
            hd = "HD" if "HD" in info_text.upper() else ""
            duration_match = re.findall(r"([\d:]+)", info_text)
            duration = duration_match[0] if duration_match else ""

        # Build final URL
        final_url = siteurl[:-1] + videourl.replace("&amp;", "&")
        site.add_download_link(
            name, final_url, "Playvid", thumb, name, duration=duration, quality=hd
        )

    # Pagination
    next_link = soup.select_one('a[aria-label*="Next"], a[label*="Next"]')
    if next_link:
        purl = utils.safe_get_attr(next_link, "href")
        if purl:
            purl = siteurl[:-1] + purl.replace("&amp;", "&")
            current_page = soup.select_one(
                'a[aria-label*="Current"], a[label*="Current"]'
            )
            if current_page:
                curr_pg_text = utils.safe_get_attr(
                    current_page, "aria-label", ["label"]
                )
                curr_pg_match = re.findall(r"(\d+)", curr_pg_text)
                curr_pg = curr_pg_match[0] if curr_pg_match else "?"
            else:
                curr_pg = "?"
            site.add_dir(
                "Next Page... [COLOR hotpink](Currently in Page {})[/COLOR]".format(
                    curr_pg
                ),
                purl,
                "List",
                site.img_next,
            )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        # Ensure url ends with slash if it doesn't have query params
        base_search = url
        if "?" not in base_search and not base_search.endswith("/"):
            base_search += "/"
            
        title = keyword.replace(" ", "%20")
        if "?" in base_search:
            searchUrl = base_search + title
        else:
            searchUrl = base_search + title + "?pricing=free"
        List(searchUrl)


@site.register()
def Tags(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    soup = utils.parse_html(cathtml)

    # Find all category items
    items = soup.select('li.category, li[class*="category"]')

    for item in items:
        link = item.select_one("a")
        if not link:
            continue

        catpage = utils.safe_get_attr(link, "href")
        if not catpage:
            continue

        # Get category title
        title_tag = link.select_one('span.category-title, span[class*="title"]')
        name = utils.safe_get_text(title_tag, "")
        if not name:
            name = utils.safe_get_text(link)

        if not name:
            continue

        # Get video count
        count_tag = item.select_one("span, div")
        if count_tag and count_tag != title_tag:
            count_text = utils.safe_get_text(count_tag, "")
            # Extract number (could be like "123", "1.2k", "1.2m")
            videos_match = re.search(r"([\d\.km]+)", count_text, re.IGNORECASE)
            videos = videos_match.group(1) if videos_match else ""
        else:
            videos = ""

        if videos:
            name = (
                utils.cleantext(name)
                + " [COLOR deeppink]("
                + videos
                + " videos)[/COLOR]"
            )
        else:
            name = utils.cleantext(name)

        site.add_dir(
            name, siteurl[:-1] + catpage + "?pricing=free", "List", site.img_cat
        )

    utils.eod()


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, siteurl)
    soup = utils.parse_html(cathtml)

    # Find all card group items
    items = soup.select('div.card.group, div[class*="card"][class*="group"]')

    for item in items:
        link = item.select_one("a")
        if not link:
            continue

        catpage = utils.safe_get_attr(link, "href")
        name = utils.safe_get_attr(link, "title")

        if not catpage or not name:
            continue

        img_tag = item.select_one("img")
        image = utils.safe_get_attr(
            img_tag, "src", ["data-src", "data-original", "data-lazy-src", "data-lazy"]
        )

        # Get video count
        count_tag = item.select_one("span, div")
        if count_tag:
            count_text = utils.safe_get_text(count_tag, "")
            videos_match = re.search(r"([\d\.km]+)", count_text, re.IGNORECASE)
            videos = videos_match.group(1) if videos_match else ""
        else:
            videos = ""

        if videos:
            name = (
                utils.cleantext(name)
                + " [COLOR deeppink]("
                + videos
                + " videos)[/COLOR]"
            )
        else:
            name = utils.cleantext(name)

        site.add_dir(name, siteurl[:-1] + catpage + "?pricing=free", "List", image)

    xbmcplugin.addSortMethod(utils.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    def add_video_headers(videourl, referer):
        if not videourl:
            return videourl
        if "|" in videourl:
            return videourl
        if videourl.startswith("//"):
            videourl = "https:" + videourl
        if not videourl.startswith("http"):
            return videourl
        return "{}|Referer={}&User-Agent={}".format(videourl, referer, utils.USER_AGENT)

    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    found = False
    while not found:
        vlink = utils.getVideoLink(url, site.url)
        if vlink != url:
            if vlink.startswith("/"):
                vlink = urllib_parse.urljoin(url, vlink)
            url = vlink
        else:
            found = True
    vp.progress.update(50, "[CR]Scraping video page[CR]")
    if not vp.resolveurl.HostedMediaFile(vlink) or "zbporn" in vlink:
        if "&lander=" in vlink:
            vlink = vlink.split("&lander=")[-1]
        vlink = urllib_parse.unquote(vlink)
        referer = "/".join(vlink.split("/")[:3]) + "/"

        vpage = utils.getHtml(url, site.url)

        patterns = [
            r"""<source\s+[^>]*src=['"]([^'"]+\.mp4[^'"]*)['"]\s+[^>]*title=['"]([^'"]+)""",
            r'\{"src":"([^"]+)","desc":"([^"]+)"',
            r'\\"url\\",\\"([^"]+)\\",\\"width\\",\d+,\\"height\\",(\d+)',
        ]
        sources = {}
        for pattern in patterns:
            match = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
            if match:
                sources.update({title: src for src, title in match if title != "Auto"})
        try:
            videourl = utils.prefquality(
                sources,
                sort_by=lambda x: 2160 if x == "4k" else int(x[:-1]),
                reverse=True,
            )
        except Exception as e:
            utils.kodilog("@@@@Cumination: failure in awmnet: " + str(e))
            videourl = utils.selector("Select source", sources, reverse=True)
        if videourl:
            videourl = videourl.replace(r"\/", "/")
            videourl = add_video_headers(videourl, referer)
            vp.play_from_direct_link(videourl)
            return

        patterns = [
            r'embed_url":\s*"([^"]+)"',
            r"video_url:\s*'([^']+(?:\.m3u8|\.mp4))'",
            r'rel="video_src" href="([^"]+)"',
            r'<source src="([^"]+(?:\.m3u8|\.mp4))"',
        ]
        sources = []
        for pattern in patterns:
            match = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
            if match:
                sources = sources + match
        videourl = utils.selector("Select source", sources)
        if videourl:
            videourl = "https:" + videourl if videourl.startswith("//") else videourl
            videourl = add_video_headers(videourl, referer)
            vp.play_from_direct_link(videourl)
            return

        if "function/0/http" not in vpage and (
            '<div class="embed-wrap"' in vpage or '"embedUrl": "' in vpage
        ):
            match = re.compile(
                r'<div class="embed-wrap".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE
            ).findall(vpage)
            if match:
                vpage = utils.getHtml(match[0], url)
            else:
                match = re.compile(
                    r'"embedUrl":\s*"([^"]+)"', re.DOTALL | re.IGNORECASE
                ).findall(vpage)
                if match:
                    vpage = utils.getHtml(match[0], url)

        if "license_code: '" in vpage:
            sources = {}
            license = re.compile(
                r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE
            ).findall(vpage)[0]
            patterns = [
                r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                r"video_url:\s*'([^']+)',[^/]+(postfix):\s*'\.mp4'",
                r"video_url:\s*'([^']+)',[^/]+(preview)",
            ]
            for pattern in patterns:
                items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
                for surl, qual in items:
                    qual = "0p" if qual in ("preview", "postfix") else qual
                    qual = "720p" if qual == "HD" else qual
                    if "function/0/http" in surl:
                        surl = kvs_decode(surl, license)
                    # Use the video page URL base as referer, not the API URL base
                    referer = "/".join(vlink.split("/")[:3]) + "/"
                    surl = utils.getVideoLink(surl, referer)
                    surl = surl + "|Referer={}&User-Agent={}".format(
                        referer, utils.USER_AGENT
                    )
                    if ".mp4" in surl:
                        sources.update({qual: surl})

            if sources:

                def quality_sort_key2(x):
                    if x == "4k":
                        return 2160
                    try:
                        return int(x.replace("p", "").replace("P", ""))
                    except (ValueError, AttributeError):
                        return 0

                videourl = utils.selector(
                    "Select quality",
                    sources,
                    setting_valid="qualityask",
                    sort_by=quality_sort_key2,
                    reverse=True,
                )

                if videourl:
                    vp.play_from_direct_link(videourl)
                    return

        match = re.search(r"^(http[s]?://[^/]+/)videos*/(\d+)/", vlink, re.IGNORECASE)
        if match:
            host = match.group(1)
            id = match.group(2)
            apiurl = "{0}api/videofile.php?video_id={1}&lifetime=8640000".format(
                host, id
            )
            try:
                jsondata = utils.getHtml(apiurl, url)
                r = re.search('video_url":"([^"]+)', jsondata)
                if r:
                    videourl = host + txxx.Tdecode(r.group(1))
                    videourl = add_video_headers(videourl, referer)
                    vp.play_from_direct_link(videourl)
                    return
                else:
                    utils.kodilog(
                        "AWM: API returned no video_url, trying resolveurl fallback"
                    )
            except Exception as e:
                utils.kodilog("Error getting video from API: " + str(e))
                utils.kodilog("AWM: Trying resolveurl fallback for: " + vlink)
                # Continue to try resolveurl fallback

    if "xhamster" in vlink:
        from resources.lib.sites.xhamster import Playvid as xhamsterPlayvid

        xhamsterPlayvid(vlink, name, download)
        return

    vp.play_from_link_to_resolve(vlink)

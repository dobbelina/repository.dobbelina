"""
Cumination
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
import re
import base64
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

addon = utils.addon
site = AdultSite(
    "sxyprn", "[COLOR hotpink]Sxy Prn[/COLOR]", "https://sxyprn.com/", "", "sxyprn"
)


@site.register(default_mode=True)
def Main():
    site.add_dir("[COLOR hotpink]Categories[/COLOR]", site.url, "Cat", site.img_cat)
    site.add_dir(
        "[COLOR hotpink]Top Pornstars[/COLOR]", site.url, "Stars", site.img_cat
    )
    site.add_dir(
        "[COLOR hotpink]Top rated last week[/COLOR]",
        site.url + "popular/top-rated.html",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Top POP last week[/COLOR]",
        site.url + "popular/top-pop.html",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Top viewed last week[/COLOR]",
        site.url + "popular/top-viewed.html",
        "List",
        site.img_cat,
    )
    site.add_dir(
        "[COLOR hotpink]Orgasmic[/COLOR]", site.url + "orgasm/", "List", site.img_cat
    )
    site.add_dir("[COLOR hotpink]Search[/COLOR]", site.url, "Search", site.img_search)
    List(site.url + "blog/all/0.html?fl=all&sm=latest")
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    if ">Nothing Found. See More...<" in listhtml:
        utils.notify("SEARCH", "Nothing Found.")
        return

    soup = utils.parse_html(listhtml)
    video_items = soup.select("div.post_el_small")

    for item in video_items:
        # Prefer real post links over author/category links.
        link = (
            item.select_one('a[href*="/post/"]')
            or item.select_one("a[aria-label][href]")
            or item.select_one("a[href]")
        )
        if not link:
            continue

        href = utils.safe_get_attr(link, "href")
        title = utils.safe_get_attr(link, "title")
        if not href:
            continue
        if not title:
            title = utils.safe_get_text(item.select_one(".post_text"))
        if not title:
            title = utils.safe_get_attr(item.select_one("img"), "alt", default="")
        if not title:
            continue

        videopage = urllib_parse.urljoin(site.url, href)
        name = title

        external_links = []
        for ext_link in item.select(".post_text a.extlink[href], a.extlink_icon[href]"):
            ext_url = utils.safe_get_attr(ext_link, "href")
            if ext_url and ext_url.startswith("http"):
                external_links.append(ext_url)

        if not external_links and "http" in name:
            external_links = re.findall(r"(http[^\s]+)", name)

        if external_links:
            name = re.sub(r"(http[^\s]+)", "", name)
            iurl = "|".join(dict.fromkeys(external_links)) + "@"
        else:
            iurl = videopage

        info = utils.cleantext(name)
        if info.startswith("#"):
            name = info[1:].split("#")[0]
        else:
            name = info.split("#")[0]
        if "Cast:" in name:
            name = name.split("Cast:")[0]
        if "cast:" in name:
            name = name.split("cast:")[0]
        name = name.strip().replace("\n", " ")
        if name.startswith("{") and name.endswith("}"):
            name = name.strip("{}")

        img_tag = item.select_one("img")
        thumb = utils.safe_get_attr(
            img_tag, "data-src", ["data-original", "data-lazy", "src"]
        )
        if thumb and thumb.startswith("//"):
            thumb = "https:" + thumb

        duration_tag = item.select_one('.duration_small, [class*="duration"]')
        duration = utils.safe_get_text(duration_tag)
        if duration and ":" not in duration:
            duration = ""

        quality_tag = item.select_one(".bitrate")
        quality = utils.safe_get_text(quality_tag)

        aria_link = item.select_one("a[aria-label]")
        if aria_link:
            aria_href = utils.safe_get_attr(aria_link, "href")
            if aria_href:
                videopage = urllib_parse.urljoin(site.url, aria_href)

        contexturl = (
            utils.addon_sys
            + "?mode={}.Lookupinfo".format(site.module_name)
            + "&url="
            + urllib_parse.quote_plus(videopage)
        )
        contextmenu = [
            ("[COLOR deeppink]Lookup info[/COLOR]", "RunPlugin(" + contexturl + ")")
        ]

        site.add_download_link(
            name,
            iurl,
            "Playvid",
            thumb,
            info,
            duration=duration,
            quality=quality,
            contextm=contextmenu,
        )

    curr_el = soup.select_one(".ctrl_el.ctrl_sel")
    ctrl_items = soup.select(".ctrl_el")
    currpage = utils.safe_get_text(curr_el).strip() if curr_el else ""
    lastpage = utils.safe_get_text(ctrl_items[-1]).strip() if ctrl_items else ""

    next_href = ""
    if curr_el:
        next_link = curr_el.find_next("a", class_="ctrl_el")
        if next_link:
            next_href = utils.safe_get_attr(next_link, "href")

    if not next_href:
        next_wrapper = soup.select_one("div.next_page")
        if next_wrapper:
            parent = next_wrapper.find_parent("a")
            if parent:
                next_href = utils.safe_get_attr(parent, "href")

    if next_href:
        next_url = urllib_parse.urljoin(site.url, next_href)
        label = "Next Page..."
        if currpage and lastpage:
            label = "Next Page... (Currently in Page {0} of {1})".format(
                currpage, lastpage
            )
        site.add_dir(label, next_url, "List", site.img_next)

    utils.eod()


def ssut51(arg):
    digits = re.sub(r"[\D]", "", str(arg))
    return sum(int(c) for c in digits)


def boo(ss, es):
    host = site.url.lower().split("/")[-2]
    b = base64.b64encode("{}-{}-{}".format(ss, host, es).encode()).decode()
    return b.replace("+", "-").replace("/", "_").replace("=", ".")


def preda(arg):
    arg[5] = str(int(arg[5]) - ssut51(arg[6]) - ssut51(arg[7]))
    return arg


def getvsrc(src):
    tmp = src.split("/")
    tmp[1] += "8/" + boo(ssut51(tmp[6]), ssut51(tmp[7]))
    tmp = preda(tmp)
    return "/".join(tmp)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    for anchor in soup.select("a[href]"):
        wrapper = anchor.select_one("div.htag_el")
        if not wrapper:
            continue

        caturl = utils.safe_get_attr(anchor, "href")
        if not caturl:
            continue
        caturl = urllib_parse.urljoin(site.url, caturl)

        img_tag = wrapper.select_one("img")
        img = utils.safe_get_attr(
            img_tag, "data-src", ["data-original", "data-lazy", "src"]
        )
        if img and img.startswith("//"):
            img = "https:" + img

        tag_name = ""
        for text in wrapper.stripped_strings:
            if text.startswith("#"):
                tag_name = text.lstrip("#")
                break
        count = utils.safe_get_text(wrapper.select_one(".count"))

        if not tag_name:
            tag_name = utils.safe_get_text(wrapper)

        name = utils.cleantext(tag_name)
        if count:
            name += " [COLOR deeppink]({0})[/COLOR]".format(count)

        site.add_dir(name, caturl, "List", img)
    utils.eod()


@site.register()
def Stars(url):
    cathtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(cathtml)

    for anchor in soup.select('a[target="_blank"][href]'):
        block = anchor.select_one(".top_sub_el.top_sub_el_ps")
        if not block:
            continue

        caturl = urllib_parse.urljoin(site.url, utils.safe_get_attr(anchor, "href"))
        name = utils.safe_get_text(block.select_one(".top_sub_el_key_ps"))
        if not name:
            name = utils.safe_get_text(block)

        name = utils.cleantext(name)
        site.add_dir(name, caturl, "List", "")
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, "Search")
    else:
        title = keyword.replace(" ", "-")
        searchUrl = url + title + ".html"
        List(searchUrl)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videourl = ""

    if url.endswith("@"):
        links = url[:-1].split("|")
        links = {
            utils.get_vidhost(link): link
            for link in links
            if vp.resolveurl.HostedMediaFile(link)
        }
        videourl = utils.selector("Select link", links)
    else:
        videopage = utils.getHtml(url, site.url)
        soup = utils.parse_html(videopage)

        external_links = []
        for ext_link in soup.select(".post_text a.extlink[href], a.extlink_icon[href]"):
            ext_url = utils.safe_get_attr(ext_link, "href")
            if ext_url and vp.resolveurl.HostedMediaFile(ext_url):
                external_links.append(ext_url)
        if external_links:
            links = {utils.get_vidhost(link): link for link in external_links}
            videourl = utils.selector("Select link", links)

        if not videourl:
            # New pages expose encoded mappings in a hidden data-vnfo JSON map.
            vnfo = soup.select_one(".vidsnfo[data-vnfo]")
            data_vnfo = utils.safe_get_attr(vnfo, "data-vnfo", default="") if vnfo else ""
            path = ""
            if data_vnfo:
                try:
                    mapping = json.loads(data_vnfo)
                    post_match = re.search(r"/post/([^/.]+)", url)
                    post_id = post_match.group(1) if post_match else ""
                    if post_id and post_id in mapping:
                        path = mapping.get(post_id, "")
                    elif mapping:
                        path = list(mapping.values())[0]
                except Exception:
                    path = ""

            if not path:
                legacy = re.compile(
                    r'data-vnfo=[\'"]\{".+?":"(.+?)"',
                    re.DOTALL | re.IGNORECASE,
                ).findall(videopage)
                path = legacy[0] if legacy else ""

            if path:
                path = path.replace(r"\/", "/")
                if "/cdn/" in path:
                    videourl = getvsrc(path)
                elif path.startswith("/"):
                    videourl = site.url[:-1] + path
                else:
                    videourl = path

                if videourl.startswith("/"):
                    videourl = site.url[:-1] + videourl

    if not videourl:
        utils.notify("Oh Oh", "No Videos found")
        vp.progress.close()
        return

    if "/cdn8/" in videourl:
        videourl = utils.getVideoLink(videourl)
        if videourl.startswith("//"):
            videourl = "https:" + videourl
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Actor", ["el_wrap'>(.*?)comments_area", "href='([^']+)'>([^<]+)<"], ""),
        ("Tag", ["el_wrap'>(.*?)comments_area", """href="([^"']+)">([^<]+)<"""], ""),
    ]

    lookupinfo = utils.LookupInfo(
        site.url, url, "{}.List".format(site.module_name), lookup_list
    )
    lookupinfo.getinfo()

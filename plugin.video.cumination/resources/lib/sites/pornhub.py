"""
Cumination
Copyright (C) 2015 Whitecream
Copyright (C) 2015 anton40
Copyright (C) 2015 Team Cumination

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

site = AdultSite(
    "pornhub",
    "[COLOR hotpink]PornHub[/COLOR]",
    "https://www.pornhub.com/",
    "pornhub.png",
    "pornhub",
)
cookiehdr = {"Cookie": "accessAgeDisclaimerPH=1; accessAgeDisclaimerUK=1"}


@site.register(default_mode=True)
def Main():
    site.add_dir(
        "[COLOR hotpink]Search[/COLOR]",
        site.url + "video/search?search=",
        "Search",
        site.img_search,
    )
    categories_url = site.url.rstrip("/") + "/categories"
    site.add_dir(
        "[COLOR hotpink]Categories[/COLOR]", categories_url, "Categories", site.img_cat
    )
    List(site.url + "video?o=cm")
    utils.eod()


@site.register()
def List(url):
    url = update_url(url)

    def collect_video_items(scope_obj):
        selectors = (
            "li.pcVideoListItem, div.pcVideoListItem, li.js-pop.videoBox, div.js-pop.videoBox"
        )
        nodes = list(scope_obj.select(selectors))
        filtered = []
        for node in nodes:
            link = node.select_one('a[href*="/view_video.php?viewkey="]')
            if link:
                filtered.append(node)
        if filtered:
            return filtered

        # Fallback: locate anchors directly when container classes change.
        anchors = scope_obj.select('a[href*="/view_video.php?viewkey="]')
        wrapped = []
        for anchor in anchors:
            parent = anchor.find_parent(["li", "div", "article"])
            wrapped.append(parent if parent is not None else anchor)
        return wrapped

    def dedupe_video_items(items):
        deduped = []
        seen_urls = set()
        for item in items:
            link = item.select_one('a[href*="/view_video.php?viewkey="]')
            href = utils.safe_get_attr(link, "href") if link else ""
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            deduped.append(item)
        return deduped

    def collect_search_video_items(soup_obj):
        search_scopes = soup_obj.select(
            "#searchPageVideoList, #videoSearchResult, #videoSearchWrapper, "
            "#videoBoxesSearch, .videoBoxesSearch, .search-video-thumbs, "
            "[class*='search-video-thumbs']"
        )
        scoped_items = []
        for scope in search_scopes:
            scoped_items.extend(collect_video_items(scope))
        scoped_items = dedupe_video_items(scoped_items)
        if scoped_items:
            return scoped_items
        return dedupe_video_items(collect_video_items(soup_obj))

    def add_img_headers(img_url):
        if not img_url:
            return img_url
        if "|" in img_url:
            return img_url
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        if not img_url.startswith("http"):
            return img_url
        if "phncdn.com" in img_url or "ttcache.com" in img_url:
            return "{}|Referer={}&User-Agent={}".format(
                img_url, site.url, utils.USER_AGENT
            )
        return img_url

    cm_production = utils.addon_sys + "?mode=" + str("pornhub.ContextProduction")
    cm_min_length = utils.addon_sys + "?mode=" + str("pornhub.ContextMinLength")
    cm_max_length = utils.addon_sys + "?mode=" + str("pornhub.ContextMaxLength")
    cm_quality = utils.addon_sys + "?mode=" + str("pornhub.ContextQuality")
    cm_country = utils.addon_sys + "?mode=" + str("pornhub.ContextCountry")
    cm_sortby = utils.addon_sys + "?mode=" + str("pornhub.ContextSortby")
    cm_time = utils.addon_sys + "?mode=" + str("pornhub.ContextTime")
    cm_filter = [
        (
            "[COLOR violet]Production[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("production")
            ),
            "RunPlugin(" + cm_production + ")",
        ),
        (
            "[COLOR violet]Min Length[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("minlength")
            ),
            "RunPlugin(" + cm_min_length + ")",
        ),
        (
            "[COLOR violet]Max Length[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("maxlength")
            ),
            "RunPlugin(" + cm_max_length + ")",
        ),
        (
            "[COLOR violet]Quality[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("quality")
            ),
            "RunPlugin(" + cm_quality + ")",
        ),
        (
            "[COLOR violet]Country[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("country")
            ),
            "RunPlugin(" + cm_country + ")",
        ),
        (
            "[COLOR violet]Sort By[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("sortby")
            ),
            "RunPlugin(" + cm_sortby + ")",
        ),
        (
            "[COLOR violet]Time[/COLOR] [COLOR orange]{}[/COLOR]".format(
                get_setting("time")
            ),
            "RunPlugin(" + cm_time + ")",
        ),
    ]

    listhtml = utils.getHtml(url, site.url, cookiehdr)
    if "Error Page Not Found" in listhtml or not listhtml:
        site.add_dir(
            "No videos found. [COLOR hotpink]Clear all filters.[/COLOR]",
            "",
            "ResetFilters",
            Folder=False,
            contextm=cm_filter,
        )
        utils.eod()
        return

    # Parse HTML with BeautifulSoup
    soup = utils.parse_html(listhtml)

    # Extract page title (if present)
    title_tag = soup.select_one("h1.searchPageTitle, h1")
    if title_tag:
        title = utils.cleantext(utils.safe_get_text(title_tag))
        site.add_dir(
            "[COLOR orange]" + title + " [COLOR hotpink]*** Clear all filters.[/COLOR]",
            "",
            "ResetFilters",
            Folder=False,
            contextm=cm_filter,
        )

    # Extract video items
    # PornHub uses class="pcVideoListItem" for video cards
    if "search?" in url:
        video_items = collect_search_video_items(soup)
    else:
        video_items = dedupe_video_items(collect_video_items(soup))

    for item in video_items:
        try:
            # Get the link element
            link = item.select_one('a[href*="/view_video.php?viewkey="]')
            if not link:
                continue

            # Extract video URL and title
            video_url = utils.safe_get_attr(link, "href")
            if not video_url:
                continue

            # Make absolute URL if needed
            if video_url.startswith("/"):
                video_url = site.url[:-1] + video_url

            title = utils.safe_get_attr(link, "title")
            if not title:
                title_tag = item.select_one(".title")
                title = utils.safe_get_text(title_tag)
            if not title:
                img_tag = item.select_one("img")
                title = utils.safe_get_attr(img_tag, "alt")

            # Extract thumbnail image
            img_tag = item.select_one("img")
            img = utils.safe_get_attr(
                img_tag,
                "data-thumb-url",
                ["data-mediumthumb", "data-src", "data-lazy-src", "data-img", "src"],
            )
            if not img:
                img = utils.safe_get_attr(
                    item,
                    "data-thumb-url",
                    ["data-mediumthumb", "data-img", "data-src", "data-lazy-src"],
                )
            if not img and link:
                img = utils.safe_get_attr(
                    link,
                    "data-thumb-url",
                    ["data-mediumthumb", "data-img", "data-src", "data-lazy-src"],
                )
            img = add_img_headers(img)

            # Extract duration
            duration_tag = item.select_one('.duration, [data-title="Video Duration"]')
            duration = utils.safe_get_text(duration_tag)

            # Skip very short videos (likely previews/ads)
            if duration:
                # Convert duration to seconds for comparison
                # Format is usually MM:SS or H:MM:SS
                parts = duration.split(':')
                try:
                    seconds = 0
                    if len(parts) == 1:
                        seconds = int(parts[0])
                    elif len(parts) == 2:
                        seconds = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 3:
                        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    
                    if seconds > 0 and seconds < 15:
                        utils.kodilog("pornhub: Skipping short video '{}' ({}s)".format(title, seconds))
                        continue
                except (ValueError, TypeError):
                    pass

            # Add video to list
            site.add_download_link(
                title,
                video_url,
                "Playvid",
                img,
                "",
                duration=duration,
                contextm=cm_filter,
            )

        except Exception as e:
            # Log error but continue processing other videos
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Extract pagination (Next Page link)
    next_page = soup.select_one("li.page_next a, .page_next a")
    if next_page:
        next_url = utils.safe_get_attr(next_page, "href")
        if next_url:
            # Extract page number for display
            page_match = re.search(r"page=(\d+)", next_url)
            page_num = page_match.group(1) if page_match else ""

            # Extract "Showing X-Y of Z" text for display
            showing_text = soup.select_one(".showingCounter")
            showing_info = (
                " [COLOR hotpink]... " + utils.safe_get_text(showing_text) + "[/COLOR]"
                if showing_text
                else ""
            )

            # Build next page URL
            if next_url.startswith("/"):
                next_url = site.url[:-1] + next_url
            next_url = next_url.replace("&amp;", "&")

            site.add_dir(
                "Next Page ({}){}".format(page_num, showing_info),
                next_url,
                "List",
                site.img_next,
            )

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, "Search")
    else:
        from six.moves import urllib_parse

        title = urllib_parse.quote_plus(keyword)
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    utils.kodilog("PornHub Categories URL: " + url)
    cathtml = utils.getHtml(url, site.url, cookiehdr)

    soup = utils.parse_html(cathtml)
    categories = soup.select('.category-wrapper, div[class*="category"]')

    entries = []
    for category in categories:
        try:
            link = category.select_one("a")
            if not link:
                continue
            catpage = utils.safe_get_attr(link, "href")
            if not catpage:
                continue
            if catpage.startswith("/"):
                catpage = site.url[:-1] + catpage
            name = utils.safe_get_attr(link, "alt")
            if not name:
                name = utils.safe_get_attr(link, "title")
            if not name:
                name_tag = category.select_one(".title, .categoryName")
                name = utils.safe_get_text(name_tag) if name_tag else "Category"
            img_tag = category.select_one("img")
            img = utils.safe_get_attr(img_tag, "src", ["data-src", "data-lazy-src"])
            count_tag = category.select_one("var, .videoCount")
            video_count = utils.safe_get_text(count_tag)
            if video_count:
                display_name = name + " [COLOR orange]({} videos)[/COLOR]".format(
                    video_count
                )
            else:
                display_name = name
            entries.append((display_name, catpage, img, name.lower()))
        except Exception as e:
            utils.kodilog("Error parsing category: " + str(e))
            continue

    entries.sort(key=lambda item: item[3])
    for display_name, catpage, img, _ in entries:
        site.add_dir(display_name, catpage, "List", img, "")

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vp.play_from_link_to_resolve(url)


def get_setting(x):
    dict = {
        "production": "All",
        "minlength": "0",
        "maxlength": "40+ Min",
        "quality": "All",
        "country": "World",
        "sortby": "Newest",
        "time": "All Time",
    }
    if x in dict:
        ret = (
            utils.addon.getSetting("pornhub" + x)
            if utils.addon.getSetting("pornhub" + x)
            else dict[x]
        )
    else:
        ret = ""
    return ret


@site.register()
def ContextProduction():
    filters = {"All": 1, "Professional": 2, "Homemade": 3}
    cat = utils.selector(
        "Select production", filters.keys(), sort_by=lambda x: filters[x]
    )
    if cat:
        utils.addon.setSetting("pornhubproduction", cat)
        utils.refresh()


@site.register()
def ContextMinLength():
    filters = {"0": 1, "10 min": 2, "20 min": 3, "30 min": 4}
    cat = utils.selector(
        "Select Min Legth", filters.keys(), sort_by=lambda x: filters[x]
    )
    if cat:
        utils.addon.setSetting("pornhubminlength", cat)
        utils.refresh()


@site.register()
def ContextMaxLength():
    filters = {"10 Min": 1, "20 Min": 2, "30 Min": 3, "40+ Min": 4}
    cat = utils.selector(
        "Select Max Legth", filters.keys(), sort_by=lambda x: filters[x]
    )
    if cat:
        utils.addon.setSetting("pornhubmaxlength", cat)
        utils.refresh()


@site.register()
def ContextQuality():
    filters = {"All": 1, "HD": 2}
    cat = utils.selector("Select Quality", filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting("pornhubquality", cat)
        utils.refresh()


@site.register()
def ContextCountry():
    cc = {
        "World": "",
        "Argentina": "cc=ar",
        "Australia": "cc=au",
        "Austria": "cc=at",
        "Belgium": "cc=be",
        "Brazil": "cc=br",
        "Bulgaria": "cc=bg",
        "Canada": "cc=ca",
        "Chile": "cc=cl",
        "Croatia": "cc=hr",
        "Czech Republic": "cc=cz",
        "Denmark": "cc=dk",
        "Egypt": "cc=eg",
        "Finland": "cc=fi",
        "France": "cc=fr",
        "Germany": "cc=de",
        "Greece": "cc=gr",
        "Hungary": "cc=hu",
        "India": "cc=in",
        "Ireland": "cc=ie",
        "Israel": "cc=il",
        "Italy": "cc=it",
        "Japan": "cc=jp",
        "Mexico": "cc=mx",
        "Morocco": "cc=ma",
        "Netherlands": "cc=nl",
        "New Zealand": "cc=nz",
        "Norway": "cc=no",
        "Pakistan": "cc=pk",
        "Poland": "cc=pl",
        "Portugal": "cc=pt",
        "Romania": "cc=ro",
        "Russian Federation": "cc=ru",
        "Serbia": "cc=rs",
        "Slovakia": "cc=sk",
        "Korea => Republic of": "cc=kr",
        "Spain": "cc=es",
        "Sweden": "cc=se",
        "Switzerland": "cc=ch",
        "United Kingdom": "cc=gb",
        "Ukraine": "cc=ua",
        "United States": "cc=us",
    }
    cat = utils.selector("Select Country", cc.keys())
    if cat:
        utils.addon.setSetting("pornhubcountry", cat)
        utils.refresh()


@site.register()
def ContextSortby():
    filters = {
        "Newest": 1,
        "Hottest": 2,
        "Longest": 3,
        "Top Rated": 4,
        "Most Viewed": 5,
        "Featured Recently/Most Relevant": 6,
    }
    cat = utils.selector(
        "Select Sort Order", filters.keys(), sort_by=lambda x: filters[x]
    )
    if cat:
        utils.addon.setSetting("pornhubsortby", cat)
        utils.refresh()


@site.register()
def ContextTime():
    filters = {"All Time": 1, "Daily": 2, "Weekly": 3, "Monthly": 4, "Yearly": 5}
    cat = utils.selector("Select time", filters.keys(), sort_by=lambda x: filters[x])
    if cat:
        utils.addon.setSetting("pornhubtime", cat)
        utils.refresh()


def param(x):
    cc = {
        "World": "",
        "Argentina": "cc=ar",
        "Australia": "cc=au",
        "Austria": "cc=at",
        "Belgium": "cc=be",
        "Brazil": "cc=br",
        "Bulgaria": "cc=bg",
        "Canada": "cc=ca",
        "Chile": "cc=cl",
        "Croatia": "cc=hr",
        "Czech Republic": "cc=cz",
        "Denmark": "cc=dk",
        "Egypt": "cc=eg",
        "Finland": "cc=fi",
        "France": "cc=fr",
        "Germany": "cc=de",
        "Greece": "cc=gr",
        "Hungary": "cc=hu",
        "India": "cc=in",
        "Ireland": "cc=ie",
        "Israel": "cc=il",
        "Italy": "cc=it",
        "Japan": "cc=jp",
        "Mexico": "cc=mx",
        "Morocco": "cc=ma",
        "Netherlands": "cc=nl",
        "New Zealand": "cc=nz",
        "Norway": "cc=no",
        "Pakistan": "cc=pk",
        "Poland": "cc=pl",
        "Portugal": "cc=pt",
        "Romania": "cc=ro",
        "Russian Federation": "cc=ru",
        "Serbia": "cc=rs",
        "Slovakia": "cc=sk",
        "Korea => Republic of": "cc=kr",
        "Spain": "cc=es",
        "Sweden": "cc=se",
        "Switzerland": "cc=ch",
        "United Kingdom": "cc=gb",
        "Ukraine": "cc=ua",
        "United States": "cc=us",
    }
    dict = {
        "All": "",
        "Professional": "p=professional",
        "Homemade": "p=homemade",
        "0": "",
        "10 min": "min_duration=10",
        "20 min": "min_duration=20",
        "30 min": "min_duration=30",
        "10 Min": "max_duration=10",
        "20 Min": "max_duration=20",
        "30 Min": "max_duration=30",
        "40+ Min": "",
        "HD": "hd=1",
        "Newest": "o=cm",
        "Hottest": "o=ht",
        "Longest": "o=lg",
        "Top Rated": "o=tr",
        "Most Viewed": "o=mv",
        "Featured Recently/Most Relevant": "",
        "All Time": "t=a",
        "Daily": "t=t",
        "Weekly": "t=w",
        "Monthly": "",
        "Yearly": "t=y",
    }
    dict.update(cc)
    if x in dict:
        ret = dict[x]
    else:
        utils.kodilog("Key error: " + str(x))
        ret = ""
    return ret


def update_url(url):
    if "/video/search" in url:
        # Keep search queries simple and stable; aggressive filters often return empty results.
        query_match = re.search(r"[?&]search=([^&]*)", url)
        search_value = query_match.group(1) if query_match else ""
        page_match = re.search(r"[?&]page=(\d+)", url)
        page_value = page_match.group(1) if page_match else ""

        clean_url = site.url + "video/search?search=" + search_value
        if page_value:
            clean_url += "&page=" + page_value
        clean_url += "&o=mr"
        return clean_url

    old_params = url.split("?")[-1].split("&")
    old_params.sort()
    url = re.sub(r"[\?&]p=[^\?&]+", "", url)
    url = re.sub(r"[\?&]min_duration=[^\?&]+", "", url)
    url = re.sub(r"[\?&]max_duration=[^\?&]+", "", url)
    url = re.sub(r"[\?&]hd=[^\?&]+", "", url)
    url = re.sub(r"[\?&]o=[^\?&]+", "", url)
    url = re.sub(r"[\?&]t=[^\?&]+", "", url)
    url = re.sub(r"[\?&]cc=[^\?&]+", "", url)

    params = {
        param(get_setting("production")),
        param(get_setting("minlength")),
        param(get_setting("maxlength")),
        param(get_setting("quality")),
        param(get_setting("country")),
        param(get_setting("sortby")),
        param(get_setting("time")),
    }

    for x in params:
        if x != "":
            url += "&" + x

    if "search?" in url:
        url = url.replace("o=cm", "o=mr")
        url = re.sub(r"[\?&]o=ht[^\?&]+", "", url)

    if "o=" not in url or "o=lg" in url or "o=cm" in url or "o=mr" in url:
        url = re.sub(r"[\?&]t=[^\?&]+", "", url)
        url = re.sub(r"[\?&]cc=[^\?&]+", "", url)
    if "o=tr" in url:
        url = re.sub(r"[\?&]cc=[^\?&]+", "", url)
    if "o=ht" in url:
        url = re.sub(r"[\?&]t=[^\?&]+", "", url)
    if "?" not in url:
        url = url.replace("&", "?", 1)

    new_params = url.split("?")[-1].split("&")
    new_params.sort()

    if new_params != old_params:
        url = re.sub(r"[\?&]page=[^\?&]+", "", url)
    if "?" not in url:
        url = url.replace("&", "?", 1)
    return url


@site.register()
def ResetFilters():
    dict = {
        "production": "All",
        "minlength": "0",
        "maxlength": "40+ Min",
        "quality": "All",
        "country": "World",
        "sortby": "Newest",
        "time": "All Time",
    }
    for x in dict:
        utils.addon.setSetting("pornhub" + x, dict[x])
    utils.refresh()
    return

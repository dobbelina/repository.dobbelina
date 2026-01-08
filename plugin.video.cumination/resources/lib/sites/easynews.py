# -*- coding: utf-8 -*-
from base64 import b64encode
import re
import requests
import time
import unicodedata
from urllib.parse import quote
import xbmcgui

from resources.lib import utils
from resources.lib.adultsite import AdultSite


# from resources.lib.common.source_utils import (
#     clean_title,
#     get_info,
#     get_quality,
#     de_string_size,
#     remove_from_title,
#     remove_country,
# )
# from resources.lib.modules.exceptions import PreemptiveCancellation

# from providerModules.a4kNewsgroups import common


site = AdultSite('easynew', '[COLOR hotpink]EasyNews[/COLOR]', 'https://members.easynews.com/', 'easynews.png', 'easynews')


def _get_auth():
    auth = None
    try:
        username = utils.addon.getSetting("easynews.username") or ""
        password = utils.addon.getSetting("easynews.password") or ""
        if username == "" or password == "":
            username = utils._get_keyboard(default='', heading='Input your Chaturbate username')
            password = utils._get_keyboard(default='', heading='Input your Chaturbate password', hidden=True)
            if username != "" and password != "":
                utils.addon.setSetting("easynews.username", username)
                utils.addon.setSetting("easynews.password", password)
            else:
                return auth
        user_info = f"{username}:{password}"
        user_info = user_info.encode("utf-8")
        auth = f"Basic {b64encode(user_info).decode('utf-8')}"
    except Exception as e:
        utils.kodilog(f"Easynews: could not authorize - {e}", "error")
    return {"Authorization": auth}


auth = _get_auth()


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Configuration[/COLOR]', '', 'Config', '')
    site.add_dir('[COLOR hotpink]Search[/COLOR]', f'{site.url}2.0/search/solr-search/advanced', 'Search', site.img_search)
    utils.eod()


@site.register()
def Config():
    site.add_dir('[COLOR hotpink]Username[/COLOR]', '{0}my/subscriptions/?mode=async&function=get_block&block_id=list_videos_videos_from_my_subscriptions&sort_by=&from_my_subscriptions_videos=1'.format(site.url), 'PTList', page=1)
    site.add_dir('[COLOR hotpink]Password[/COLOR]', '{0}my/subscriptions/?mode=async&function=get_block&block_id=list_members_subscriptions_my_subscriptions&sort_by=added_date&from_my_subscriptions=1'.format(site.url), 'PTSubscriptions')
    site.add_dir('[COLOR hotpink]PT Favorites[/COLOR]', site.url + 'my/favourites/videos/?mode=async&function=get_block&block_id=list_videos_my_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_my_fav_videos=1', 'PTList', site.img_cat)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        search_params = {
            "st": "adv",
            "fex": "m4v,3gp,mov,divx,xvid,wmv,avi,mpg,mpeg,mp4,mkv,avc,flv,webm",
            "fty[]": "VIDEO",
            "u": "1",
            "pby": 350,
            "safeO": 0,
        }
        search_params["gps"] = keyword
        utils.kodilog(f"Easynews: searching for {keyword}")
        utils.kodilog(auth)
        utils.kodilog(url)
        results = requests.get(url, params=search_params, headers=auth, timeout=20).json()
        List(keyword, results)


@site.register()
def List(title, results):
    down_url = results.get("downURL")
    dl_farm = results.get("dlFarm")
    dl_port = results.get("dlPort")
    items = results.get("data", [])

    utils.kodilog(f"Easynews: found {len(items)} items")
    utils.notify(f"Easynews: found {len(items)} items")

    def _process_item(item, down_url, dl_farm, dl_port, title):
        post_hash, size, post_title, ext = (
            item["0"],
            item["4"],
            item["10"],
            item["11"],
        )

        cleaned = utils.cleantext(post_title)

        if item.get("virus"):
            return
        if item.get("type", "").upper() != "VIDEO":
            return
        # if not title_check(post_title, title):
        #     return
        # if _check_exclusions(cleaned):
        #     return

        stream_url = down_url + quote(f"/{dl_farm}/{dl_port}/{post_hash}{ext}/{post_title}{ext}")
        file_dl = f"{stream_url}|Authorization={quote(auth['Authorization'])}"
        return file_dl

    for item in items:
        post_title = item["10"]
        post_hash = item["0"]
        ext = item["11"]
        size = item["4"]

        img = f'https://th.easynews.com/thumbnails-{post_hash[:3]}/th-{post_hash}.jpg'
        videourl = _process_item(item, down_url, dl_farm, dl_port, title)
        if not videourl:
            continue

        utils.kodilog(f"Easynews: adding {post_title} ({size})")
        utils.kodilog(videourl)
        site.add_download_link(post_title, videourl, 'Playvid', img)  # , 'info', duration=None, quality=None)

    utils.kodilog(items[0])

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(url)


# _exclusions = ["soundtrack", "gesproken", "sample", "trailer", "extras only", " ost"]
# _resolutions = [
#     "2160p",
#     "216op",
#     "4k",
#     "1080p",
#     "1o8op",
#     "108op",
#     "1o80p",
#     "720p",
#     "72op",
#     "480p",
#     "48op",
# ]


# class sources:
#     def __init__(self):
#         self.language = ["en"]
#         self.base_link = "https://members.easynews.com"
#         self.search_link = "/2.0/search/solr-search/advanced"
#         self.query_link = f"{self.base_link}{self.search_link}"
#         self.auth = self._get_auth()
#         self.start_time = 0
#         self.sort_params = {
#             "s1": "relevance",
#             "s1d": "-",
#             "s2": "dsize",
#             "s2d": "-",
#             "s3": "dtime",
#             "s3d": "-",
#         }
#         self.search_params = {
#             "st": "adv",
#             "fex": "m4v,3gp,mov,divx,xvid,wmv,avi,mpg,mpeg,mp4,mkv,avc,flv,webm",
#             "fty[]": "VIDEO",
#             "u": "1",
#             "pby": 350,
#             "safeO": 0,
#         }
#         self.search_params.update(self.sort_params)

#     def _get_auth(self):
#         auth = None
#         try:
#             username = utils.addon.getSetting("easynews.username") or ""
#             password = utils.addon.getSetting("easynews.password")
#             if username == "" or password == "":
#                 return auth
#             user_info = f"{username}:{password}"
#             user_info = user_info.encode("utf-8")
#             auth = f"Basic {b64encode(user_info).decode('utf-8')}"
#         except Exception as e:
#             utils.kodilog(f"a4kNewsgroups.easynews: could not authorize - {e}", "error")
#         return {"Authorization": auth}

#     def _return_results(self, source_type, sources, preemptive=False):
#         if preemptive:
#             utils.kodilog("a4kNewsgroupssource_typeeasynews: cancellation requested", "info")
#         elif preemptive is None:
#             utils.kodilog(f"a4kNewsgroups.{source_type}.easynews: not authorized", "info")

#         utils.kodilog(f"a4kNewsgroups.{source_type}.easynews: {len(sources)}", "info")
#         utils.kodilog(
#             f"a4kNewsgroups.{source_type}.easynews: took {int((time.time() - self.start_time) * 1000)} ms",
#             "info",
#         )
#         return sources

#     def _make_query(self, query):
#         query = "".join([c for c in unicodedata.normalize("NFKD", query) if unicodedata.category(c) != "Mn"])
#         query = query.replace('"', "")
#         utils.kodilog(query, "info")

#         self.search_params["gps"] = query
#         results = requests.get(
#             self.query_link,
#             params=self.search_params,
#             headers=self.auth,
#             timeout=20,
#         ).json()

#         down_url = results.get("downURL")
#         dl_farm = results.get("dlFarm")
#         dl_port = results.get("dlPort")
#         files = results.get("data", [])

#         return down_url, dl_farm, dl_port, files

#     def _process_item(self, item, down_url, dl_farm, dl_port, simple_info):
#         post_hash, size, post_title, ext = (
#             item["0"],
#             item["4"],
#             item["10"],
#             item["11"],
#         )

#         cleaned = clean_title(post_title)

#         if item.get("virus"):
#             return
#         if item.get("type", "").upper() != "VIDEO":
#             return
#         if not self.title_check(post_title, simple_info):
#             return
#         if self._check_exclusions(cleaned):
#             return
#         if not self._check_languages(item.get("alangs", []), item.get("slangs", [])):
#             return

#         stream_url = down_url + quote(f"/{dl_farm}/{dl_port}/{post_hash}{ext}/{post_title}{ext}")
#         file_dl = f"{stream_url}|Authorization={quote(self.auth['Authorization'])}"
#         utils.kodilog(file_dl, "info")

#         source = {
#             "scraper": "easynews",
#             "release_title": post_title,
#             "info": get_info(post_title),
#             "size": de_string_size(size),
#             "quality": get_quality(post_title),
#             "url": file_dl + '&seekable=0',
#             "url": file_dl,
#             "debrid_provider": "Usenet",
#             "headers": self.auth,
#             "filetype": ext,
#         }
#         return source

#     def episode(self, simple_info, info):
#         self.start_time = time.time()
#         sources = []
#         if not self.auth:
#             return self._return_results("episode", sources, preemptive=None)

#         show_title = clean_title(simple_info["show_title"])
#         season_xx = simple_info["season_number"].zfill(2)
#         episode_xx = simple_info["episode_number"].zfill(2)
#         absolute_number = simple_info["absolute_number"]
#         is_anime = simple_info["isanime"]

#         queries = [
#             f'"{show_title}" S{season_xx}E{episode_xx}',
#         ]
#         if is_anime and absolute_number:
#             queries.append(f'"{show_title}" {absolute_number}')

#         for query in queries:
#             try:
#                 down_url, dl_farm, dl_port, files = self._make_query(query)

#                 for item in files:
#                     source = self._process_item(item, down_url, dl_farm, dl_port, simple_info)

#                     if source is not None:
#                         sources.append(source)
#                 return self._return_results("episode", sources)
#             except PreemptiveCancellation:
#                 return self._return_results("episode", sources, preemptive=True)

#     def movie(self, title, year, imdb, simple_info, info):
#         self.start_time = time.time()
#         sources = []
#         if not self.auth:
#             return self._return_results("movie", sources, preemptive=None)

#         title = clean_title(simple_info["title"])
#         year = simple_info["year"]

#         query = f'"{title}" {year}'
#         try:
#             down_url, dl_farm, dl_port, files = self._make_query(query)
#             if not files:
#                 query = title
#                 down_url, dl_farm, dl_port, files = self._make_query(query)

#             for item in files:
#                 source = self._process_item(item, down_url, dl_farm, dl_port, simple_info)

#                 if source is not None:
#                     sources.append(source)

#             return self._return_results("movie", sources)
#         except PreemptiveCancellation:
#             return self._return_results("movie", sources, preemptive=True)

#     @staticmethod


def clean_title(title, broken=None):
    """
    Returns a cleaned version of the provided title
    :param title: title to be cleaned
    :param broken: set to 1 to remove apostophes, 2 to replace with spaces
    :return: cleaned title
    """
    title = g.deaccent_string(title)
    title = strip_non_ascii_and_unprintable(title)
    title = title.lower()

    apostrophe_replacement = "s"
    if broken == 1:
        apostrophe_replacement = ""
    elif broken == 2:
        apostrophe_replacement = " s"

    title = _APOSTROPHE_SUBS.sub(apostrophe_replacement, title)

    title = _SINGLE_QUOTE.sub("", title)
    title = _SEPARATORS.sub(" ", title)
    title = _WHITESPACE.sub(" ", title)
    title = _AMPERSAND.sub("and", title)

    return title.strip()


def title_check(post_title, simple_info):
    meta_title = simple_info.get("title", simple_info.get("show_title", ""))
    aliases = simple_info.get("aliases", simple_info.get("show_aliases", []))
    post_cleaned = clean_title(post_title)
    if "show_title" in simple_info:
        country = simple_info.get("country", "")
        year = simple_info.get("year", "")
        post_cleaned = remove_country(post_cleaned, country)
        post_cleaned = remove_from_title(post_cleaned, year)
    meta_cleaned = clean_title(meta_title)
    titles_cleaned = [meta_cleaned, *[clean_title(alias) for alias in aliases]]
    episode_regex = r"(.*)((?:s(\d+) ?e(\d+))|(?:season ?(\d+) ?(?:episode|ep) ?(\d+))|(?: (\d+) ?x ?(\d+)))(.*)"

    split = re.split(rf"{simple_info.get('year')}", post_cleaned, 1, re.I)[0]
    split = re.split(
        rf"{'|'.join(_resolutions)}",
        split,
        1,
        re.I,
    )[0]
    split = split.rstrip()

    if "show_title" in simple_info:
        data = re.search(episode_regex, split)
        if data is None:
            return False
        else:
            data = data.groups()

        show_title = data[0].rstrip() if data[0] else None
        episode_title = data[8].lstrip() if data[8] else None

        if not any([show_title == title for title in titles_cleaned]):
            return False
        # if episode_title is not None and not episode_title == clean_title(
        # simple_info["episode_title"]
        # ):
        # return False

        numbers = []
        for pos in [(2, 3), (4, 5), (6, 7)]:
            if not any([None in (data[pos[0]], data[pos[1]])]):
                numbers.append((int(data[pos[0]]), int(data[pos[1]])))
        if numbers and not any(
            [
                i
                == (
                    int(simple_info["season_number"]),
                    int(simple_info["episode_number"]),
                )
                for i in numbers
            ]
        ):
            return False
        return True
    elif any([split == title for title in titles_cleaned]):
        return True

    return False


@site.register()
def _check_exclusions(clean_title):
    return any([i in clean_title for i in _exclusions])



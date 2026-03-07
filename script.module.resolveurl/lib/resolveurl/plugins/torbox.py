"""
    Plugin for ResolveURL
    Copyright (c) 2024 pikdum

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

from resolveurl import common
from resolveurl.common import i18n
from resolveurl.lib import helpers
from resolveurl.resolver import ResolverError, ResolveUrl
from six.moves import urllib_error, urllib_parse

logger = common.log_utils.Logger.get_logger(__name__)
logger.disable()

AGENT = "ResolveURL for Kodi"
VERSION = common.addon_version
USER_AGENT = "{0}/{1}".format(AGENT, VERSION)
FORMATS = common.VIDEO_FORMATS


class TorBoxResolver(ResolveUrl):
    name = "TorBox"
    domains = ["*"]
    api_url = "https://api.torbox.app/v1/api"

    def __init__(self):
        self.hosters = None
        self.hosts = None
        self.headers = {
            "User-Agent": USER_AGENT,
            "Authorization": "Bearer %s" % self.__get_token(),
        }

    def __api(self, endpoint, query=None, data=None, empty=None, json_data=False):
        try:
            if query:
                url = "{0}/{1}?{2}".format(
                    self.api_url, endpoint, urllib_parse.urlencode(query)
                )
                result = self.net.http_GET(url, headers=self.headers).content
            if data:
                url = "{0}/{1}".format(self.api_url, endpoint)
                result = self.net.http_POST(
                    url,
                    data,
                    headers=self.headers,
                    timeout=90,
                    jdata=json_data,
                ).content
            if not query and not data:
                url = "{0}/{1}".format(self.api_url, endpoint)
                result = self.net.http_GET(url, headers=self.headers).content
            if not result:
                return empty
            result = json.loads(result)
            if result.get("success"):
                return result.get("data")
            return empty
        except urllib_error.HTTPError as e:
            if e.code == 429:
                common.kodi.sleep(1500)
                return self.__api(endpoint, query, data, empty)
            return empty

    def __get(self, endpoint, query, empty=None):
        return self.__api(endpoint, query=query, empty=empty)

    def __post(self, endpoint, data, empty=None, json_data=False):
        return self.__api(endpoint, data=data, empty=empty, json_data=json_data)

    def __check_torrent_cached(self, btih):
        result = self.__get(
            "torrents/checkcached",
            {"hash": btih, "format": "list", "list_files": False},
        )
        return bool(result)

    def __create_torrent(self, magnet):
        result = self.__post(
            "torrents/createtorrent",
            {"magnet": magnet, "seed": 3, "allow_zip": False},
            {},
        )
        return result

    def __get_torrent_info(self, torrent_id):
        result = self.__get(
            "torrents/mylist", {"id": torrent_id, "bypass_cache": True}, {}
        )
        return result

    def __request_torrent_download(self, torrent_id, file_id):
        return self.__get(
            "torrents/requestdl",
            {"torrent_id": torrent_id, "file_id": file_id, "token": self.__get_token()},
        )

    def __delete_torrent(self, torrent_id):
        return self.__post(
            "torrents/controltorrent",
            {"torrent_id": torrent_id, "operation": "delete"},
            json_data=True,
        )

    def __create_webdl(self, url):
        result = self.__post("webdl/createwebdownload", {"link": url})
        return result

    def __get_webdl_info(self, webdl_id):
        result = self.__get("webdl/mylist", {"id": webdl_id, "bypass_cache": True}, {})
        return result

    def __request_webdl_download(self, webdl_id, file_id):
        return self.__get(
            "webdl/requestdl",
            {"web_id": webdl_id, "file_id": file_id, "token": self.__get_token()},
        )

    def __delete_webdl(self, webdl_id):
        return self.__post(
            "webdl/controlwebdownload",
            {"webdl_id": webdl_id, "operation": "delete"},
            json_data=True,
        )

    def __get_token(self):
        return self.get_setting("apikey")

    def __get_hash(self, media_id):
        r = re.search("""magnet:.+?urn:([a-zA-Z0-9]+):([a-zA-Z0-9]+)""", media_id, re.I)
        if not r or len(r.groups()) < 2:
            return None
        return r.group(2)

    # hacky workaround to get return_all working
    # we prefix with tb:$file_id| to indicate which file to download
    # then handle it when re-resolving
    def __get_file_id(self, media_id):
        r = re.search(r"""tb:(\d*)\|(.*)""", media_id, re.I)
        if not r or len(r.groups()) < 2:
            return (None, media_id)
        return (int(r.group(1)), r.group(2))

    def __get_media_url_torrent(
        self, host, media_id, cached_only=False, return_all=False
    ):
        with common.kodi.ProgressDialog("ResolveURL TorBox") as d:
            (file_id, media_id) = self.__get_file_id(media_id)
            btih = self.__get_hash(media_id)

            d.update(0, line1="Checking cache...")
            cached = self.__check_torrent_cached(btih)
            cached_only = self.get_setting("cached_only") == "true" or cached_only
            if not cached and cached_only:
                raise ResolverError("TorBox: {0}".format(i18n("cached_torrents_only")))

            d.update(0, line1="Adding torrent...")
            torrent_id = self.__create_torrent(media_id).get("torrent_id")
            if not torrent_id:
                raise ResolverError("Errror adding torrent")

            ready = cached
            while not ready:
                info = self.__get_torrent_info(torrent_id)
                ready = info.get("download_present", False)
                if ready:
                    break
                if d.is_canceled():
                    keep_transfer = common.kodi.yesnoDialog(
                        heading="ResolveURL TorBox Transfer",
                        line1="Keep transferring to TorBox Cloud in the background?"
                    )
                    if not keep_transfer:
                        raise ResolverError("TorBox Transfer Cancelled by user")
                    logger.log_debug("ResolveURL TorBox Transfer Cancelled by user - Transfer is alive")
                    return
                torrent_name = info.get("name")
                progress = int(info.get("progress", 0) * 100)
                status = "%s (ETA: %ss)" % (info.get("download_state"), info.get("eta"))
                d.update(
                    progress,
                    line1="Waiting for download...",
                    line2=status,
                    line3=torrent_name,
                )
                common.kodi.sleep(1500)

        files = self.__get_torrent_info(torrent_id).get("files", [])
        files = [f for f in files if any(f["name"].lower().endswith(x) for x in FORMATS)]

        if return_all:
            links = [
                {
                    "name": f.get("short_name"),
                    "link": "tb:%s|%s" % (f.get("id"), media_id),
                }
                for f in files
            ]
            return links

        if len(files) > 1 and file_id is None:
            _file = max(files, key=lambda x: x.get("size"))
            file_id = _file.get("id")
        elif isinstance(file_id, int):
            pass
        else:
            file_id = files[0]["id"]

        download_link = self.__request_torrent_download(torrent_id, file_id)

        if self.get_setting("clear_finished") == "true":
            self.__delete_torrent(torrent_id)

        return download_link

    def __get_media_url_webdl(
        self, host, media_id, cached_only=False, return_all=False
    ):
        with common.kodi.ProgressDialog("ResolveURL TorBox") as d:
            (file_id, media_id) = self.__get_file_id(media_id)

            # can't check cache with just a url, so skip
            # otherwise, follow similar implementation as torrents

            d.update(0, line1="Adding web download...")
            webdl_id = self.__create_webdl(media_id).get("webdownload_id")
            if not webdl_id:
                raise ResolverError("Errror adding web download")

            ready = False
            while not ready:
                info = self.__get_webdl_info(webdl_id)
                ready = info.get("download_present", False)
                if ready:
                    break
                if d.is_canceled():
                    keep_transfer = common.kodi.yesnoDialog(
                        heading="ResolveURL TorBox Transfer",
                        line1="Keep transferring to TorBox Cloud in the background?"
                    )
                    if not keep_transfer:
                        raise ResolverError("TorBox Transfer Cancelled by user")
                    logger.log_debug("ResolveURL TorBox Transfer Cancelled by user - Transfer is alive")
                    return
                webdl_name = info.get("name")
                progress = int(info.get("progress", 0) * 100)
                status = "%s (ETA: %ss)" % (info.get("download_state"), info.get("eta"))
                d.update(
                    progress,
                    line1="Waiting for download...",
                    line2=status,
                    line3=webdl_name,
                )
                common.kodi.sleep(1500)

        # don't think web downloads can have multiple files right now
        # but this might handle it if they ever do
        files = self.__get_webdl_info(webdl_id).get("files", [])

        if return_all:
            links = [
                {
                    "name": f.get("short_name"),
                    "link": "tb:%s|%s" % (f.get("id"), media_id),
                }
                for f in files
            ]
            return links

        # allow user to pick if multiple files
        if len(files) > 1 and file_id is None:
            links = [[f.get("short_name"), f.get("id")] for f in files]
            links.sort(key=lambda x: x[1])
            file_id = helpers.pick_source(links, auto_pick=False)
        elif isinstance(file_id, int):
            pass
        else:
            file_id = 0

        download_link = self.__request_webdl_download(webdl_id, file_id)

        if self.get_setting("clear_finished") == "true":
            self.__delete_webdl(webdl_id)

        return download_link

    def get_media_url(self, host, media_id, cached_only=False, return_all=False):
        (_, parsed_media_id) = self.__get_file_id(media_id)
        if parsed_media_id.startswith("magnet:"):
            return self.__get_media_url_torrent(host, media_id, cached_only, return_all)
        else:
            return self.__get_media_url_webdl(host, media_id, cached_only, return_all)

    def get_url(self, host, media_id):
        return media_id

    def get_host_and_id(self, url):
        return "torbox.app", url

    def valid_url(self, url, host):
        if not self.hosts:
            self.hosts = self.get_all_hosters()

        if url:
            # handle multi-file hack
            if url.startswith("tb:"):
                return True

            # magnet link
            if url.startswith("magnet:"):
                btih = self.__get_hash(url)
                return bool(btih) and self.get_setting("torrents") == "true"

            # webdl
            if not self.get_setting("web_downloads") == "true":
                return False

            try:
                host = urllib_parse.urlparse(url).hostname
            except:
                host = "unknown"

            host = host.replace("www.", "")
            if any(host in item for item in self.hosts):
                return True

        elif host:
            host = host.replace("www.", "")
            if any(host in item for item in self.hosts):
                return True

        return False

    @common.cache.cache_method(cache_limit=8)
    def get_all_hosters(self):
        hosts = []
        try:
            result = self.__get("webdl/hosters", None, [])
            hosts = [h.get("domains") for h in result if h.get("status", False)]
            hosts = [host for sublist in hosts for host in sublist]
            if self.get_setting("torrents") == "true":
                hosts.extend(["torrent", "magnet"])
        except Exception as e:
            logger.log_error("Error getting TorBox hosts: %s" % (e))
        return hosts

    @classmethod
    def get_settings_xml(cls):
        xml = super(cls, cls).get_settings_xml(include_login=False)
        xml.append(
            '<setting id="%s_torrents" type="bool" label="%s" default="true"/>'
            % (cls.__name__, i18n("torrents"))
        )
        xml.append(
            '<setting id="%s_cached_only" enable="eq(-1,true)" type="bool" label="%s" default="false" />'
            % (cls.__name__, i18n("cached_only"))
        )
        xml.append(
            '<setting id="%s_web_downloads" type="bool" label="%s" default="true"/>'
            % (cls.__name__, "Web Download Support")
        )
        xml.append(
            '<setting id="%s_clear_finished" type="bool" label="%s" default="true"/>'
            % (cls.__name__, "Clear Finished downloads from account")
        )
        xml.append(
            '<setting id="%s_apikey" enable="eq(-5,true)" type="text" label="%s" default=""/>'
            % (cls.__name__, "API Key")
        )
        return xml

    @classmethod
    def isUniversal(cls):
        return True

    @classmethod
    def _is_enabled(cls):
        return cls.get_setting("enabled") == "true" and cls.get_setting("apikey")

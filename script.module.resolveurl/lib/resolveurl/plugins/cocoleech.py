"""
    Plugin for ResolveURL
    Copyright (c) 2025 gujal

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
from six.moves import urllib_parse, urllib_error
import json
from resolveurl import common
from resolveurl.common import i18n
from resolveurl.resolver import ResolveUrl, ResolverError

logger = common.log_utils.Logger.get_logger(__name__)
logger.disable()

AGENT = 'ResolveURL'
VERSION = common.addon_version
USER_AGENT = '{0}/{1}'.format(AGENT, VERSION)
FORMATS = common.VIDEO_FORMATS

DOMAIN = 'https://members.cocoleech.com/'
auth_api = DOMAIN + 'auth/api'
torr_api = DOMAIN + 'api/v2'


class CocoLeechResolver(ResolveUrl):
    name = 'CocoLeech'
    domains = ['*']

    def __init__(self):
        self.hosts = None
        self.headers = {'User-Agent': USER_AGENT}
        if self.get_setting('apikey'):
            self.api_key = self.get_setting('apikey')

    def get_media_url(self, host, media_id, cached_only=False, return_all=False):
        if media_id.lower().startswith('magnet:'):
            r = re.search('''magnet:.+?urn:([a-zA-Z0-9]+):([a-zA-Z0-9]+)''', media_id, re.I)
            if r:
                _hash = r.group(2)
                cached = self.__check_cache(_hash)
                if not cached:
                    if cached_only or self.get_setting('cached_only') == 'true':
                        raise ResolverError('CocoLeech: {0}'.format(i18n('cached_torrents_only')))
                    else:
                        ok = self.__create_transfer(_hash)
                        if not ok:
                            raise ResolverError('CocoLeech: {0}'.format(i18n('no_stream')))

                transfer_info = self.__browse_magnet(_hash)
                if return_all:
                    sources = [
                        {'name': link.get('name'), 'link': link.get('downloadUrl')}
                        for link in transfer_info.get('files')
                        if any(link.get('name').lower().endswith(x) for x in FORMATS)
                    ]
                    return sources
                else:
                    # sources = []
                    # for link in transfer_info.get('files'):
                    #     if any(link.get('name').lower().endswith(x) for x in FORMATS):
                    #         sources.append((link.get('size'), link.get('downloadUrl')))
                    sources = [
                        (link.get('size'), link.get('downloadUrl'))
                        for link in transfer_info.get('files')
                        if any(link.get('name').lower().endswith(x) for x in FORMATS)
                    ]
                    return max(sources)[1]

        params = {'link': media_id, 'key': self.api_key}
        url = '{0}?{1}'.format(auth_api, urllib_parse.urlencode(params))
        result = self.net.http_GET(url, headers=self.headers).content
        try:
            js_result = json.loads(result)
        except json.decoder.JSONDecodeError:
            js_result = json.loads(result[1:])
        logger.log_debug('CocoLeech resolve: [{0}]'.format(js_result))

        if js_result.get('status') == '100':
            e = js_result.get('message')
            common.kodi.notify(msg=e)
            logger.log_error('CocoLeech resolve: [{0}]'.format(e))

        if js_result.get('download'):
            surl = js_result.get('download')
            available = False
            while not available:
                try:
                    _ = self.net.http_HEAD(surl, headers=self.headers)
                    available = True
                except urllib_error.HTTPError:
                    common.kodi.sleep(5000)
                    pass
            return surl

        raise ResolverError('CocoLeech: {0}'.format(i18n('no_stream')))

    def __check_cache(self, magnet_hash):
        try:
            params = {'hash': magnet_hash, 'key': self.api_key}
            url = '{0}/checkInstant?{1}'.format(torr_api, urllib_parse.urlencode(params))
            result = self.net.http_GET(url, headers=self.headers).content
            result = json.loads(result)
            if 'status' in result:
                if result.get('status') == '200':
                    if result.get('message') == 'Torrent cached':
                        return True
        except:
            pass

        return False

    def __browse_magnet(self, magnet_hash):
        params = {'hash': magnet_hash, 'key': self.api_key}
        url = '{0}/browse?{1}'.format(torr_api, urllib_parse.urlencode(params))
        result = self.net.http_GET(url, headers=self.headers).content
        result = json.loads(result)
        items = result.get('arguments').get('torrents')
        return items[0]

    def __create_transfer(self, magnet_hash, cached_only=False):
        params = {'hash': magnet_hash, 'key': self.api_key}
        url = '{0}/add?{1}'.format(torr_api, urllib_parse.urlencode(params))
        result = self.net.http_GET(url, headers=self.headers).content
        result = json.loads(result)
        if result.get('status') == "200":
            logger.log_debug('Transfer successfully started to the CocoLeech cloud')
            return self.__initiate_transfer(magnet_hash)
        else:
            raise ResolverError(result.get('message'))

    def __initiate_transfer(self, magnet_hash, interval=5):
        transfer_info = self.__list_transfer(magnet_hash)
        if transfer_info:
            line1 = transfer_info.get('name')
            line2 = i18n('cl_save')
            line3 = transfer_info.get('status')
            with common.kodi.ProgressDialog('ResolveURL CocoLeech {0}'.format(i18n('transfer')), line1, line2, line3) as pd:
                while not transfer_info.get('isComplete'):
                    common.kodi.sleep(1000 * interval)
                    transfer_info = self.__list_transfer(magnet_hash)
                    file_size = transfer_info.get('size')
                    file_size2 = round(float(file_size) / (1000 ** 3), 2)
                    line1 = transfer_info.get('name')

                    download_speed = round(float(transfer_info.get('rateDownload')) / (1000**2), 2)
                    progress = int(transfer_info.get('progress'))
                    line3 = "{0} {1}MB/s, {2}% {3} {4}GB {5}".format(
                        i18n('downloading'), download_speed, progress,
                        i18n('of'), file_size2, i18n('completed')
                    )

                    logger.log_debug(line3)
                    pd.update(progress, line1=line1, line3=line3)
                    if pd.is_canceled():
                        keep_transfer = common.kodi.yesnoDialog(
                            heading='ResolveURL CocoLeech {0}'.format(i18n('transfer')),
                            line1=i18n('cl_background')
                        )
                        if not keep_transfer:
                            self.__delete_magnet(magnet_hash)
                        logger.log_debug('ResolveURL CocoLeech {0} ID {1} :: {2}'.format(i18n('transfer'), magnet_hash, i18n('user_cancelled')))
                        return False
            common.kodi.sleep(1000 * interval)  # allow api time to generate the links
            return True

        else:
            self.__delete_magnet(magnet_hash)
            raise ResolverError('CocoLeech Magnet {0} :: {1}'.format(magnet_hash, transfer_info))

    def __list_transfer(self, magnet_hash):
        params = {'hash': magnet_hash, 'key': self.api_key}
        url = '{0}/list?{1}'.format(torr_api, urllib_parse.urlencode(params))
        result = self.net.http_GET(url, headers=self.headers).content
        magnets = json.loads(result)
        for magnet in magnets:
            if magnet.get('hash').lower() == magnet_hash.lower():
                return magnet

    def __delete_magnet(self, magnet_hash):
        params = {'hash': magnet_hash, 'key': self.api_key}
        url = '{0}/delete?{1}'.format(torr_api, urllib_parse.urlencode(params))
        result = self.net.http_GET(url, headers=self.headers).content
        result = json.loads(result)
        if result.get('status') == "200":
            logger.log_debug('Magnet hash "{0}" deleted from CocoLeech'.format(magnet_hash))
            return True

        return False

    def get_url(self, host, media_id):
        return media_id

    def get_host_and_id(self, url):
        return 'cocoleech.com', url

    @common.cache.cache_method(cache_limit=8)
    def get_hosts(self):
        hosts = []
        url = auth_api + '/domains'
        try:
            js_result = self.net.http_GET(url, headers=self.headers).content
            js_data = json.loads(js_result)
            for host in js_data:
                hosts.extend(host.get('domains'))
            if self.get_setting('torrents') == 'true':
                hosts.extend(['torrent', 'magnet'])
            logger.log_debug('Coocoleech hosts : {0}'.format(hosts))
        except Exception as e:
            logger.log_error('Error getting CL Hosts: {0}'.format(e))
        return hosts

    def valid_url(self, url, host):
        logger.log_debug('in valid_url {0} : {1}'.format(url, host))
        if url:
            if url.lower().startswith('magnet:') and self.get_setting('torrents') == 'true':
                return True
            host = urllib_parse.urlsplit(url).netloc

        if self.hosts is None:
            self.hosts = self.get_hosts()

        if any(item.lower() in host.lower() for item in self.hosts):
            return True

        return False

    # SiteAuth methods
    def login(self):
        if not self.get_setting('apikey'):
            self.authorize_resolver()

    def reset_authorization(self):
        self.set_setting('apikey', '')
        self.set_setting('user', '')

    def authorize_resolver(self):
        api_key = common.kodi.get_keyboard(i18n('api_key'))
        if api_key:
            url = '{0}/info?key={1}'.format(auth_api, api_key)
            js_result = self.net.http_GET(url, headers=self.headers).content
            js_data = json.loads(js_result)
            if js_data.get('status') == '200':
                if js_data.get('type') == 'Premium':
                    self.set_setting('apikey', api_key)
                    self.set_setting('user', js_data.get('username'))
                    return True
                else:
                    raise ResolverError(i18n('not_premium'))
            else:
                raise ResolverError(js_data.get('message'))

    @classmethod
    def get_settings_xml(cls):
        xml = super(cls, cls).get_settings_xml()
        xml.append('<setting id="{0}_torrents" type="bool" label="{1}" default="true"/>'.format(cls.__name__, i18n('torrents')))
        xml.append('<setting id="{0}_cached_only" enable="eq(-1,true)" type="bool" label="{1}" default="false" />'.format(cls.__name__, i18n('cached_only')))
        xml.append('<setting id="{0}_auth" type="action" label="{1}" action="RunPlugin(plugin://script.module.resolveurl/?mode=auth_cl)"/>'.format(cls.__name__, i18n('auth_my_account')))
        xml.append('<setting id="{0}_reset" type="action" label="{1}" action="RunPlugin(plugin://script.module.resolveurl/?mode=reset_cl)"/>'.format(cls.__name__, i18n('reset_my_auth')))
        xml.append('<setting id="{0}_user" enable="false" label="{1}" visible="eq(-4,true)" type="text" default=""/>'.format(cls.__name__, i18n('username')))
        xml.append('<setting id="{0}_apikey" visible="false" type="text" default=""/>'.format(cls.__name__))
        return xml

    @classmethod
    def _is_enabled(cls):
        return cls.get_setting('enabled') == 'true' and cls.get_setting('apikey')

    @classmethod
    def isUniversal(cls):
        return True

"""
    Plugin for ResolveURL
    Copyright (C) 2023 ErosVece

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
import json
import six
import time
from resolveurl import common
from resolveurl.common import i18n
from resolveurl.resolver import ResolveUrl, ResolverError
from resolveurl.lib import helpers

logger = common.log_utils.Logger.get_logger(__name__)
logger.disable()


class BoxbitResolver(ResolveUrl):
    name = 'Boxbit'
    domains = ['*']

    def __init__(self):
        self.hosters = None
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA,
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'}
        self.base_url = 'https://api.boxbit.app'

    # ResolveUrl methods
    def get_media_url(self, host, media_id):
        logger.log('in get_media_url %s : %s' % (host, media_id))
        token = self.get_setting('token')

        if token is None:
            raise ResolverError('No BB Token Available')

        uuid = self.get_setting('uuid')
        self.headers['Authorization'] = "Bearer {0}".format(token)
        data = {'link': media_id}
        while True:
            requestlink = "{0}/users/{1}/downloader/request-file".format(self.base_url, uuid)
            response = self.net.http_POST(requestlink, form_data=data, headers=self.headers, jdata=True)
            jsdata = response.content
            if response._response.code == 429:
                time.sleep(2)
            elif response._response.code == 200:
                videolink = json.loads(jsdata).get('link')
                self.headers['Referer'] = requestlink
                return videolink + helpers.append_headers(self.headers)
            else:
                msg = response.json().get('message', 'Unknown BB Error during resolve')
                logger.log_warning(msg)
                if isinstance(msg, six.text_type) and six.PY2:
                    msg = msg.encode('utf-8')
                raise ResolverError(msg)

    def get_url(self, host, media_id):
        return media_id

    def get_host_and_id(self, url):
        return 'boxbit.app', url

    def get_hosters(self):
        try:
            html = self.net.http_GET("{0}/filehosts/domains".format(self.base_url), headers=self.headers).content
            js_domains = json.loads(html)

            js_hosters = self.get_user_hosters_info()
            if js_hosters:
                workinghosters = []
                hosters = js_hosters['subscription']['current']['filehosts']
                for hoster in hosters:
                    hostdetails = hoster.get('details')
                    hostidentifier = hostdetails.get('identifier')
                    if hostdetails.get("status").lower() == "working":
                        for domain in js_domains.get(hostidentifier):
                            workinghosters.append(domain)
                    else:
                        logger.log("Skipping non working host: " + hostidentifier)
                return workinghosters
            else:
                return [host.lower() for item in js_domains.values() for host in item]
        except Exception as e:
            logger.log_error('Filehost list retrieval failed: %s' % (e))
            return []

    def valid_url(self, url, host):
        logger.log('in valid_url %s : %s' % (url, host))
        if self.hosters is None:
            self.hosters = self.get_hosters()

        if url:
            match = re.search('//(.*?)/', url)
            if match:
                logger.log('Boxbit checking host : {0}'.format(host))
                host = match.group(1)
            else:
                return False

        if host.startswith('www.'):
            host = host.replace('www.', '')
        if host and any(host in item for item in self.hosters):
            logger.log('True in valid_url')
            return True
        logger.log('False in valid_url')
        return False

    def get_user_hosters_info(self):
        try:
            token = self.get_setting('token')
            if token is None:
                raise ResolverError('No BB Token Available')

            uuid = self.get_setting('uuid')
            _ = self.login()
            user_url = "{0}/users/{1}?with[]=subscription&with[]=current_subscription_filehosts&with[]=current_subscription_filehost_usages".format(self.base_url, uuid)
            self.headers = {"Authorization": "Bearer {0}".format(token)}
            response = self.net.http_GET(user_url, headers=self.headers)
            if response._response.code == 200:
                jsdata = json.loads(response.content)
                return jsdata
            else:
                logger.log('Failed to retrieve user and hoster information.')
                return False
        except Exception as e:
            logger.log("Failed to retrieve user and hoster information: {0}".format(e))
            return False

    def refresh_token(self):
        try:
            token = self.get_setting('token')
            self.headers['Authorization'] = "Bearer {0}".format(token)
            response = self.net.http_POST("{0}/auth/refresh".format(self.base_url), headers=self.headers)
            if response._response.code == 200:
                data = json.loads(response.content)
                self.set_setting('token', data['auth']['access_token'])
                self.set_setting('uuid', data['user']['uuid'])
                self.set_setting('time_expired', time.time() + int(data['auth']['expires_in']))
                return True
            else:
                raise ResolverError('BB Refresh Token Failed')
        except Exception as e:
            msg = str(e)
            raise ResolverError('BB Refresh Token Failed: %s' % (msg))

    # SiteAuth methods
    def login(self):
        logger.log('BB Start Login')
        token = self.get_setting('token')
        uuid = self.get_setting('uuid')
        if token and uuid:  # try refresh token
            try:
                timeleft = self.getTimeExpirationTimeLeft()
                tokenRefreshRequired = timeleft < 3600
                if not tokenRefreshRequired:
                    logger.info("Trust login token without check")
                    return True
                else:
                    logger.log('Boxbit - Refreshing Token')
                    if self.refresh_token():
                        logger.log('Boxbit - Refreshing Token done')
                return True
            except Exception as e:
                msg = str(e)
        else:  # full login
            try:
                logger.log('Boxbit - Logging In')
                email = self.get_setting('email')
                password = self.get_setting('password')
                if email and password:
                    url = self.base_url + '/auth/login'
                    data = {'email': email, 'password': password}
                    html = self.net.http_POST(url, form_data=data, headers=self.headers, jdata=True)
                    if html._response.code == 200:
                        js_data = json.loads(html.content)
                        logger.log(js_data)
                        self.set_setting('token', js_data['auth']['access_token'])
                        self.set_setting('uuid', js_data['user']['uuid'])
                        self.set_setting('time_expired', time.time() + int(js_data['auth']['expires_in']))
                        return True
                    else:
                        msg = 'Login failed'
                else:
                    msg = 'No Email/Password'
            except Exception as e:
                msg = str(e)

            raise ResolverError('BB Login Failed: %s' % (msg))

    def getTimeExpirationTimeLeft(self):
        expirationtime = int(self.get_setting('time_expired'))
        if expirationtime < time.time():
            return 0
        else:
            return expirationtime - time.time()

    @classmethod
    def get_settings_xml(cls):
        xml = super(cls, cls).get_settings_xml(include_login=False)
        xml.append('<setting id="%s_login" type="bool" label="%s" default="false"/>' % (cls.__name__, i18n('login')))
        xml.append('<setting id="%s_email" enable="eq(-1,true)" type="text" label="%s" default=""/>' % (cls.__name__, i18n('email')))
        xml.append('<setting id="%s_password" enable="eq(-2,true)" type="text" label="%s" option="hidden" default=""/>' % (cls.__name__, i18n('password')))
        xml.append('<setting id="{0}_token" visible="false" type="text" default=""/>'.format(cls.__name__))
        xml.append('<setting id="{0}_uuid" visible="false" type="text" default=""/>'.format(cls.__name__))
        xml.append('<setting id="{0}_time_expired" visible="false" type="text" default=""/>'.format(cls.__name__))
        return xml

    @classmethod
    def isUniversal(self):
        return True

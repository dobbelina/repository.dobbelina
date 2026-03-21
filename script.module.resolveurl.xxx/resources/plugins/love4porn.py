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
from resolveurl import common
from resolveurl.lib import helpers
from resolveurl.resolver import ResolveUrl, ResolverError


class Love4PornResolver(ResolveUrl):
    name = 'Love4Porn'
    domains = ['love4porn.com']
    pattern = r'(?://|\.)(love4porn\.com)/(?:videos|embed)/(\d+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA,
                   'Referer': 'https://{0}/'.format(host)}
        html = self.net.http_GET(web_url, headers=headers).content
        r = re.search(r'''video_url:\s*['"]([^"']+)''', html, re.DOTALL)
        if r:
            headers.update({'Referer': web_url})
            url = r.group(1)
            if url.startswith('function/'):
                lcode = re.findall(r"license_code:\s*'([^']+)", html)[0]
                url = helpers.fun_decode(url, lcode)
            url = helpers.get_redirect_url(url, headers)
            return url + helpers.append_headers(headers)

        raise ResolverError('File not found')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/embed/{media_id}')

    @classmethod
    def _is_enabled(cls):
        return True

"""
    Plugin for ResolveURL
    Copyright (C) 2021 gujal

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
import codecs
from six.moves import urllib_parse
from resolveurl import common
from resolveurl.lib import helpers
from resolveurl.lib.jscrypto import jscrypto
from resolveurl.resolver import ResolveUrl, ResolverError


class PlayHDResolver(ResolveUrl):
    name = 'PlayHD'
    domains = ['playhd.one', 'playdrive.xyz', 'prohd.one', 'rajtamil.org']
    pattern = r'(?://|\.)((?:(?:play|pro)(?:hd|drive)|rajtamil)\.(?:one|xyz|org))/(?:embed|e|download)/([0-9a-zA-Z-:./$]+)'

    def __init__(self):
        self.net = common.Net(ssl_verify=False)

    def get_media_url(self, host, media_id):
        referer = ''
        if '$$' in media_id:
            media_id, referer = media_id.split('$$')
            referer = urllib_parse.urljoin(referer, '/')
        web_url = self.get_url(host, media_id)
        if not referer:
            referer = urllib_parse.urljoin(web_url, '/')
        headers = {'User-Agent': common.RAND_UA, 'Referer': referer}
        html = self.net.http_GET(web_url, headers=headers).content
        r = re.search(r"_decx\('([^']+)", html)
        if r:
            data = json.loads(r.group(1))
            ct = data.get('ct', False)
            salt = codecs.decode(data.get('s'), 'hex')
            html2 = jscrypto.decode(ct, 'GDPlayer-JASm(8234_)9312HJASi23lakka', salt)
            html2 = html2[1:-1].replace('\\"', '"')
            s = re.search(r'{\s*url:\s*"([^"]+)', html2)
            if s:
                headers.update({'Referer': 'https://{}/'.format(host)})
                aurl = s.group(1).replace('\\', '')
                jd = json.loads(self.net.http_GET(aurl, headers=headers).content)
                src = jd.get('sources')[0]
                if src:
                    url = src.get('file')
                    if url.startswith('//'):
                        url = 'https:' + url
                    urllib_parse.quote(url, safe=':/?&=')
                    headers.update({'verifypeer': 'false'})
                    return url + helpers.append_headers(headers)

        raise ResolverError('File Not Found or Removed')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, 'https://{host}/embed/{media_id}')

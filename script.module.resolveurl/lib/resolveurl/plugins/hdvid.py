"""
    Plugin for ResolveURL
    Copyright (C) 2016 Gujal

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

from resolveurl.lib import helpers
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError


class HDvidResolver(ResolveUrl):
    name = 'HDvid'
    domains = ['hdvid.tv', 'hdvid.fun', 'vidhdthe.online', 'hdvid.website', 'hdthevid.online',
               'hdthevid.xyz', 'bestvidhd.site', 'tovidhd5.space', 'tohidvrd.space']
    pattern = r'(?://|\.)((?:hdvid|vidhdthe|hdthevid|bestvidhd|tovidhd5|tohidvrd)\.' \
              r'(?:tv|fun|online|website|xyz|site|space))/' \
              r'(?:embed-)?([0-9a-zA-Z]+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.FF_USER_AGENT}
        html = self.net.http_GET(web_url, headers=headers).content
        sources = helpers.scrape_sources(html)
        if sources:
            headers.update({'verifypeer': 'false'})
            return helpers.pick_source(sources) + helpers.append_headers(headers)
        raise ResolverError('Video cannot be located.')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://hdvid.tv/embed-{media_id}.html')

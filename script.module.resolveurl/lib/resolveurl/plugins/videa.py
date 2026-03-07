"""
    Plugin for ResolveURL
    Copyright (C) 2020 gujal

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
import string
import random
from resolveurl.lib import helpers, rc4
from resolveurl.resolver import ResolveUrl, ResolverError
from six.moves import urllib_parse


class VideaResolver(ResolveUrl):
    name = 'Videa'
    domains = ['videa.hu', 'videakid.hu']
    pattern = r'(?://|\.)((?:videa|videakid)\.hu)/(?:player/?\?v=|player/v/|videok/)(?:.*-|)([0-9a-zA-Z]+)'
    url = ''
    videa_secret = 'xHb0ZvME5q8CBcoQi6AngerDu3FGO9fkUlwPmLVY_RTzj2hJIS4NasXWKy1td7p'
    key = ''
    cookie = ''

    def get_media_url(self, host, media_id, subs=False):
        found = False
        while not found:
            web_url = self.get_url(host, media_id)
            result = self.net.http_GET(web_url)
            videaXml = result.content
            r = re.search(r'<error.*?"noembed".*>(.*)</error>', videaXml)
            if r:
                self.url = r.group(1)
            else:
                found = True
        if not videaXml.startswith('<?xml'):
            self.key += result.get_headers(as_dict=True)['X-Videa-Xs']
            videaXml = rc4.decrypt(videaXml, self.key)
        sources = re.findall(r'video_source\s*name="(?P<label>[^"]+).*exp="(?P<exp>[^"]+)[^>]+>(?P<url>[^<]+)', videaXml)
        if not sources:
            master_hls = re.search(r'<master_playlist_url>([^<]+)', videaXml)
            if master_hls:
                sources = [('HLS_Live', '0', master_hls.group(1))]

        if subs:
            subtitles = {}
            s = re.findall(r'<subtitle\s*src="(?P<url>[^"]+)"\s*title="(?P<label>[^"]+)"', videaXml)
            if s:
                subtitles = {lang: 'https:' + suburl.replace('&amp;', '&') for suburl, lang in s}

        if sources:
            tmpSources = []
            for index, source in enumerate(sources):
                tmpSources.append((source[0], index))
            source = sources[helpers.pick_source(helpers.sort_sources_list(tmpSources))]
            url = 'https:' + source[2] if source[2].startswith('//') else source[2]
            hash_match = re.search(r'<hash_value_%s>([^<]+)<' % source[0], videaXml)
            if hash_match:
                hash_val = hash_match.group(1)
                direct_url = "%s?md5=%s&expires=%s" % (url, hash_val, source[1])
            else:
                direct_url = url
            if self.cookie:
                headers = {"Cookie": self.cookie}
                direct_url = direct_url + helpers.append_headers(headers)
            if subs:
                return direct_url.replace('&amp;', '&'), subtitles
            return direct_url.replace('&amp;', '&')

        raise ResolverError('Stream not found')

    def get_url(self, host, media_id):
        response = self.net.http_GET(self.url)
        cookie = response.get_headers(as_dict=True).get('Set-Cookie', '')
        html = response.content
        if '%s/player' % host in self.url:
            player_url = self.url
            player_page = html
        else:
            player_url = re.search(r'<iframe.*?src="(/player\?[^"]+)"', html).group(1)
            player_url = urllib_parse.urljoin(self.url, player_url)
            response = self.net.http_GET(player_url)
            player_page = response.content
            cookie = response.get_headers(as_dict=True).get('Set-Cookie', '')
        match = re.search(r'\bsl=([^;]+)', cookie)
        if match:
            self.cookie = match.group(0)
        nonce = re.search(r'_xt\s*=\s*"([^"]+)"', player_page).group(1)
        lo = nonce[:32]
        s = nonce[32:]
        result = ''
        for i in range(0, 32):
            result += s[i - (self.videa_secret.index(lo[i]) - 31)]
        query = urllib_parse.parse_qs(urllib_parse.urlparse(player_url).query)
        random_seed = ''
        for i in range(8):
            random_seed += random.choice(string.ascii_letters + string.digits)
        _s = random_seed
        _t = result[:16]
        self.key = result[16:] + random_seed
        if 'f' in query or 'v' in query:
            _param = 'f=%s' % query['f'][0] if 'f' in query else 'v=%s' % query['v'][0]
            return self._default_get_url(host, media_id, 'https://{host}/player/xml?platform=desktop&%s&_s=%s&_t=%s' % (_param, _s, _t))

        else:
            return None

    def get_host_and_id(self, url):
        self.url = url
        return super(VideaResolver, self).get_host_and_id(url)

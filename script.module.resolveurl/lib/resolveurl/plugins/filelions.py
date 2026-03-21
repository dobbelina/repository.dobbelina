"""
    Plugin for ResolveURL
    Copyright (C) 2023 gujal

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

import ast
import re
from six.moves import urllib_parse
from resolveurl import common
from resolveurl.lib import helpers
from resolveurl.resolver import ResolveUrl, ResolverError


class FileLionsResolver(ResolveUrl):
    name = 'FileLions'
    domains = [
        'filelions.com', 'filelions.to', 'ajmidyadfihayh.sbs', 'alhayabambi.sbs', 'vidhideplus.com',
        'moflix-stream.click', 'azipcdn.com', 'mlions.pro', 'alions.pro', 'dlions.pro',
        'filelions.live', 'motvy55.store', 'filelions.xyz', 'lumiawatch.top', 'filelions.online',
        'javplaya.com', 'fviplions.com', 'egsyxutd.sbs', 'filelions.site', 'filelions.co',
        'vidhide.com', 'vidhidepro.com', 'vidhidevip.com', 'javlion.xyz', 'fdewsdc.sbs',
        'techradar.ink', 'anime7u.com', 'coolciima.online', 'gsfomqu.sbs', 'vidhidepre.com',
        'katomen.online', 'vidhide.fun', 'vidhidehub.com', 'dhtpre.com', '6sfkrspw4u.sbs',
        'streamvid.su', 'movearnpre.com', 'bingezove.com', 'dingtezuni.com', 'dinisglows.com',
        'ryderjet.com', 'e4xb5c2xnz.sbs', 'smoothpre.com', 'videoland.sbs', 'taylorplayer.com',
        'mivalyo.com', 'vidhidefast.com', 'peytonepre.com', 'dintezuvio.com', 'callistanise.com',
        'minochinos.com', 'earnvids.xyz', 'lookmovie2.skin'
    ]
    pattern = r'(?://|\.)((?:filelions|ajmidyadfihayh|alhayabambi|techradar|moflix-stream|azipcdn|' \
              r'[mad]lions|lumiawatch|javplaya|javlion|fviplions|egsyxutd|fdewsdc|vidhide|peytone|' \
              r'anime7u|coolciima|gsfomqu|katomen|dht|6sfkrspw4u|ryderjet|e4xb5c2xnz|smooth|' \
              r'streamvid|movearnpre|bingezove|dingtezuni|dinisglows|motvy55|videoland|mivalyo|lookmovie2|' \
              r'taylorplayer|dintezuvio|callistanise|minochinos|earnvids)(?:pro|vip|pre|plus|hub|fast)?' \
              r'\.(?:su|com?|to|sbs|ink|click|pro|live|store|xyz|top|online|site|fun|skin))' \
              r'/((?:s|v|f|d|e|embed|file|download)/[0-9a-zA-Z$:/.]+)'

    def get_media_url(self, host, media_id, subs=False):
        if '$$' in media_id:
            media_id, referer = media_id.split('$$')
            referer = urllib_parse.urljoin(referer, '/')
        else:
            referer = False
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA}
        if referer:
            headers.update({'Referer': referer})
        html = self.net.http_GET(web_url, headers=headers).content
        html += helpers.get_packed_data(html)
        ref = urllib_parse.urljoin(web_url, '/')
        headers.update({'Referer': ref, 'Origin': ref[:-1], 'verifypeer': 'false'})
        links = re.search(r'var\s*links\s*=\s*([^;]+)', html)
        if links:
            links = ast.literal_eval(links.group(1))
            source = links.get('hls4') or links.get('hls3') or links.get('hls2')
            if source.startswith('/'):
                source = urllib_parse.urljoin(web_url, source)
            source = source + helpers.append_headers(headers)
            if subs:
                subtitles = helpers.scrape_subtitles(html, web_url)
                return source, subtitles
            return source

        source = re.search(r'''sources:\s*\[{file:\s*["']([^"']+)''', html)
        if source:
            source = source.group(1) + helpers.append_headers(headers)
            if subs:
                subtitles = helpers.scrape_subtitles(html, web_url)
                return source, subtitles
            return source

        raise ResolverError('File Not Found or Removed')

    def get_url(self, host, media_id):
        dead_domains = [
            'filelions.com', 'filelions.to', 'ajmidyadfihayh.sbs', 'alhayabambi.sbs', 'vidhideplus.com',
            'azipcdn.com', 'mlions.pro', 'alions.pro', 'dlions.pro', 'mivalyo.com', 'vidhidefast.com',
            'filelions.live', 'motvy55.store', 'filelions.xyz', 'lumiawatch.top', 'filelions.online',
            'fviplions.com', 'egsyxutd.sbs', 'filelions.site', 'filelions.co', 'vidhidepre.com',
            'vidhidepro.com', 'vidhidevip.com', 'e4xb5c2xnz.sbs', 'taylorplayer.com', 'ryderjet.com',
            'techradar.ink', 'anime7u.com', 'coolciima.online', 'gsfomqu.sbs', 'bingezove.com',
            'katomen.online', 'vidhide.fun', '6sfkrspw4u.sbs', 'dingtezuni.com', 'dinisglows.com',
            'dintezuvio.com'
        ]
        if host in dead_domains:
            host = 'callistanise.com'
        return self._default_get_url(host, media_id, template='https://{host}/{media_id}')

"""
    Plugin for ResolveURL
    Copyright (C) 2024 gujal

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

import binascii
import json
from resolveurl.lib import helpers, pyaes
from resolveurl.resolver import ResolveUrl, ResolverError
from resolveurl import common
from six.moves import urllib_parse


class KinoGerResolver(ResolveUrl):
    name = 'KinoGer'
    domains = [
        'kinoger.re', 'shiid4u.upn.one', 'moflix.upns.xyz', 'player.upn.one', 'disneycdn.net',
        'wasuytm.store', 'ultrastream.online', 'moflix.rpmplay.xyz', 'tuktuk.rpmvid.com', 'w1tv.xyz'
        'filedecrypt.link', 'asianembed.cam', 'videoshar.uns.bio', 'videoland.cfd', 'dzo.vidplayer.live',
        'watch.ezplayer.me', 'watch.streamcasthub.store', 'ultra.rpmvid.site', 'securecdn.shop',
        'srbe84.vidplayer.live', 'flimmer.rpmvip.com', 't1.p2pplay.pro', 'flixfilmesonline.strp2p.site',
        'filma365.strp2p.site', 'strp2p.site', 'vidmoly.cc', 'animeshqip.uns.bio', 'cimanow.upns.online',
        'kinoger.p2pplay.pro', 'embedplay.upns.ink', 'moviehax.strp2p.site'
    ]
    pattern = r'(?://|\.)((?:kinoger|wasuytm|ultrastream|(?:shiid4u|player)\.upn|(?:moflix|cimanow|embedplay)\.(?:upns|rpmplay)|' \
              r'(?:tuktuk|ultra)\.rpmvid|filedecrypt|(?:dzo|srbe84)\.vidplayer|video(?:shar\.uns|land)|' \
              r'w1tv|(?:flixfilmesonline\.|filma365\.|moviehax\.)?strp2p|flimmer\.rpmvip|(?:t1|kinoger)\.p2pplay|' \
              r'asianembed|securecdn|watch\.(?:ezplayer|streamcasthub)|disneycdn|vidmoly|animeshqip\.uns)' \
              r'\.(?:[mr]e|one|xyz|store|online|c[oa]m|net|l?i(?:nk|ve)|bio|cfd|site|shop|pro|cc))/#([A-Za-z0-9]+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        referer = urllib_parse.urljoin(web_url, '/')
        headers = {'User-Agent': common.FF_USER_AGENT,
                   'Referer': referer}
        edata = self.net.http_GET(web_url, headers=headers).content
        if edata:
            edata = binascii.unhexlify(edata[:-1])
            key = b'\x6b\x69\x65\x6d\x74\x69\x65\x6e\x6d\x75\x61\x39\x31\x31\x63\x61'
            iv = b'\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x6f\x69\x75\x79\x74\x72'
            decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
            ddata = decrypter.feed(edata)
            ddata += decrypter.feed()
            ddata = ddata.decode('utf-8')
            ddata = json.loads(ddata)
            # r = ddata.get('cf')  # Plays with xbmc Player
            r = ddata.get('source')  # Plays with Inputstream Adaptive
            if r:
                headers.update({'Origin': referer[:-1], 'verifypeer': 'false'})
                return r + helpers.append_headers(headers)

        raise ResolverError('No playable video found.')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/api/v1/video?id={media_id}')

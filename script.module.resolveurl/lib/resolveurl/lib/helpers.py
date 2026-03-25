# -*- coding: utf-8 -*-
"""
    ResolveURL Addon for Kodi
    Copyright (C) 2016 t0mm0, tknorris

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
import base64
import re
import six
import xbmcgui
from resolveurl.lib import jsunpack, unjuice, unjuice2
from six.moves import urllib_parse, urllib_request, urllib_error
from resolveurl import common
from resolveurl.resolver import ResolverError

PY2 = six.PY2
PY3 = six.PY3


def get_hidden(html, form_id=None, index=None, include_submit=True):
    hidden = {}
    if form_id:
        pattern = r'''<form [^>]*(?:id|name)\s*=\s*['"]?%s['"]?[^>]*>(.*?)</form>''' % (form_id)
    else:
        pattern = '''<form[^>]*>(.*?)</form>'''

    html = cleanse_html(html)

    for i, form in enumerate(re.finditer(pattern, html, re.DOTALL | re.I)):
        common.logger.log(form.group(1))
        if index is None or i == index:
            for field in re.finditer('''<input [^>]*type=['"]?hidden['"]?[^>]*>''', form.group(1)):
                match = re.search(r'''name\s*=\s*['"]([^'"]+)''', field.group(0))
                match1 = re.search(r'''value\s*=\s*['"]([^'"]*)''', field.group(0))
                if match and match1:
                    hidden[match.group(1)] = match1.group(1)

            if include_submit:
                match = re.search('''<input [^>]*type=['"]?submit['"]?[^>]*>''', form.group(1))
                if match:
                    name = re.search(r'''name\s*=\s*['"]([^'"]+)''', match.group(0))
                    value = re.search(r'''value\s*=\s*['"]([^'"]*)''', match.group(0))
                    if name and value:
                        hidden[name.group(1)] = value.group(1)

    common.logger.log_debug('Hidden fields are: %s' % (hidden))
    return hidden


def pick_source(sources, auto_pick=None):
    if auto_pick is None:
        auto_pick = common.get_setting('auto_pick') == 'true'

    if len(sources) == 1:
        return sources[0][1]
    elif len(sources) > 1:
        if auto_pick:
            return sources[0][1]
        else:
            result = xbmcgui.Dialog().select(common.i18n('choose_the_link'), [str(source[0]) if source[0] else 'Unknown' for source in sources])
            if result == -1:
                raise ResolverError(common.i18n('no_link_selected'))
            else:
                return sources[result][1]
    else:
        raise ResolverError(common.i18n('no_video_link'))


def append_headers(headers):
    return '|%s' % '&'.join(['%s=%s' % (key, urllib_parse.quote_plus(headers[key])) for key in headers])


def get_packed_data(html):
    packed_data = ''
    for match in re.finditer(r'''(eval\s*\(function\(p,a,c,k,e,.*?)</script>''', html, re.DOTALL | re.I):
        r = match.group(1)
        t = re.findall(r'(eval\s*\(function\(p,a,c,k,e,)', r, re.DOTALL | re.IGNORECASE)
        if len(t) == 1:
            if jsunpack.detect(r):
                packed_data += jsunpack.unpack(r)
        else:
            t = r.split('eval')
            t = ['eval' + x for x in t if x]
            for r in t:
                if jsunpack.detect(r):
                    packed_data += jsunpack.unpack(r)
    return packed_data


def get_juiced_data(html):
    juiced_data = ''
    for match in re.finditer(r'(JuicyCodes\.Run.+?[;\n<])', html, re.DOTALL | re.I):
        if unjuice.test(match.group(1)):
            juiced_data += unjuice.run(match.group(1))

    return juiced_data


def get_juiced2_data(html):
    juiced_data = ''
    for match in re.finditer(r'(_juicycodes\(.+?[;\n<])', html, re.DOTALL | re.I):
        if unjuice2.test(match.group(1)):
            juiced_data += unjuice2.run(match.group(1))

    return juiced_data


def sort_sources_list(sources):
    if len(sources) > 1:
        try:
            sources.sort(key=lambda x: int(re.sub(r"\D", "", x[0])), reverse=True)
        except:
            common.logger.log_debug(r'Scrape sources sort failed |int(re.sub("\D", "", x[0])|')
            try:
                sources.sort(key=lambda x: re.sub("[^a-zA-Z]", "", x[0].lower()))
            except:
                common.logger.log_debug('Scrape sources sort failed |re.sub("[^a-zA-Z]", "", x[0].lower())|')
    return sources


def parse_sources_list(html):
    sources = []
    r = re.search(r'''['"]?sources['"]?\s*:\s*\[(.*?)\]''', html, re.DOTALL)
    if r:
        sources = [(match[1], match[0].replace(r'\/', '/')) for match in re.findall(r'''['"]?file['"]?\s*:\s*['"]([^'"]+)['"][^}]*['"]?label['"]?\s*:\s*['"]([^'"]*)''', r.group(1), re.DOTALL)]
    return sources


def parse_html5_source_list(html):
    label_attrib = 'type' if not re.search(r'''<source\s+src\s*=.*?data-res\s*=.*?/\s*>''', html) else 'data-res'
    sources = [(match[1], match[0].replace(r'\/', '/')) for match in re.findall(r'''<source\s+src\s*=\s*['"]([^'"]+)['"](?:.*?''' + label_attrib + r'''\s*=\s*['"](?:video/)?([^'"]+)['"])''', html, re.DOTALL)]
    return sources


def parse_smil_source_list(smil):
    sources = []
    base = re.search(r'base\s*=\s*"([^"]+)', smil).groups()[0]
    for i in re.finditer(r'src\s*=\s*"([^"]+)(?:"\s*(?:width|height)\s*=\s*"([^"]+))?', smil):
        label = 'Unknown'
        if (len(i.groups()) > 1) and (i.group(2) is not None):
            label = i.group(2)
        sources += [(label, '%s playpath=%s' % (base, i.group(1)))]
    return sources


def scrape_sources(html, result_blacklist=None, scheme='http', patterns=None, generic_patterns=True, url=None):
    if patterns is None:
        patterns = []

    def __parse_to_list(_html, regex):
        _blacklist = ['.jpg', '.jpeg', '.gif', '.png', '.js', '.css', '.htm', '.html', '.php', '.srt', '.sub', '.xml', '.swf', '.vtt']
        _blacklist = set(_blacklist + result_blacklist)
        streams = []
        labels = []
        for r in re.finditer(regex, _html, re.DOTALL):
            match = r.groupdict()
            stream_url = match['url']
            if not (stream_url.startswith('http') or stream_url.startswith('/')):
                if re.search("^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$", stream_url):
                    stream_url = b64decode(stream_url).strip()
            if stream_url.startswith('//'):
                stream_url = scheme + ':' + stream_url
            elif not stream_url.startswith('http'):
                stream_url = urllib_parse.urljoin(url, stream_url)
            stream_url = stream_url.replace('&amp;', '&')

            file_name = urllib_parse.urlparse(stream_url[:-1]).path.split('/')[-1] if stream_url.endswith("/") else urllib_parse.urlparse(stream_url).path.split('/')[-1]
            label = match.get('label', file_name)
            if label is None:
                label = file_name
            blocked = not file_name or any(item in file_name.lower() for item in _blacklist) or any(item in label for item in _blacklist)
            if '://' not in stream_url or blocked or (stream_url in streams) or any(stream_url == t[1] for t in source_list):
                continue
            labels.append(label)
            streams.append(stream_url)

        matches = zip(labels, streams) if six.PY2 else list(zip(labels, streams))
        if matches:
            common.logger.log_debug('Scrape sources |%s| found |%s|' % (regex, matches))
        return matches

    if result_blacklist is None:
        result_blacklist = []
    elif isinstance(result_blacklist, str):
        result_blacklist = [result_blacklist]

    html = html.replace(r"\/", "/")
    html += get_packed_data(html)

    source_list = []
    if generic_patterns or not patterns:
        source_list += __parse_to_list(html, r'''["']?label\s*["']?\s*[:=]\s*["']?(?P<label>[^"',]+)["']?(?:[^}\]]+)["']?\s*file\s*["']?\s*[:=,]?\s*["'](?P<url>[^"']+)''')
        source_list += __parse_to_list(html, r'''["']?\s*(?:file|src)\s*["']?\s*[:=,]?\s*["'](?P<url>[^"']+)(?:[^}>\]]+)["']?\s*label\s*["']?\s*[:=]\s*["']?(?P<label>[^"',]+)''')
        source_list += __parse_to_list(html, r'''video[^><]+src\s*[=:]\s*['"](?P<url>[^'"]+)''')
        source_list += __parse_to_list(html, r'''source\s+src\s*=\s*['"](?P<url>[^'"]+)['"](?:.*?res\s*=\s*['"](?P<label>[^'"]+))?''')
        source_list += __parse_to_list(html, r'''["'](?:file|url)["']\s*[:=]\s*["'](?P<url>[^"']+)''')
        source_list += __parse_to_list(html, r'''param\s+name\s*=\s*"src"\s*value\s*=\s*"(?P<url>[^"]+)''')
    for regex in patterns:
        source_list += __parse_to_list(html, regex)

    source_list = list(set(source_list))

    common.logger.log(source_list)
    source_list = sort_sources_list(source_list)

    return source_list


def scrape_subtitles(html, rurl='', scheme='http', patterns=None, generic_patterns=True):
    if patterns is None:
        patterns = []

    def __parse_to_dict(_html, regex):
        labels = []
        subs = []
        for r in re.finditer(regex, _html, re.DOTALL):
            match = r.groupdict()
            subs_url = match.get('url').replace('&amp;', '&')
            file_name = urllib_parse.urlparse(subs_url[:-1]).path.split('/')[-1] if subs_url.endswith("/") else urllib_parse.urlparse(subs_url).path.split('/')[-1]
            label = match.get('label', file_name)
            if label is None:
                label = file_name
            if subs_url.startswith('//'):
                subs_url = scheme + ':' + subs_url
            elif subs_url.startswith('/'):
                subs_url = urllib_parse.urljoin(rurl, subs_url)
            if ('://' not in subs_url) or (subs_url in subs) or ('empty' in subs_url):
                continue
            labels.append(label)
            subs.append(subs_url)

        matches = {lang: url for lang, url in zip(labels, subs) if len(lang) > 1}
        if matches:
            common.logger.log_debug('Scrape sources |%s| found |%s|' % (regex, matches))
        return matches

    html = html.replace(r"\/", "/")
    html += get_packed_data(html)

    subtitles = {}
    if generic_patterns or not patterns:
        subtitles.update(__parse_to_dict(html, r'''{\s*file:\s*["'](?P<url>[^"']+)["'],\s*label:\s*["'](?P<label>[^"']+)["'],\s*kind:\s*["'](?:captions|subtitles)["']'''))
        subtitles.update(__parse_to_dict(html, r'''<track\s*kind=['"]?(?:captions|subtitles)['"]?\s*src=['"](?P<url>[^'"]+)['"]\s*srclang=['"](?P<label>[^'"]+)'''))
        subtitles.update(__parse_to_dict(html, r'''<track\s*kind="(?:captions|subtitles)"\s*label="(?P<label>[^"]+)"\s*srclang="[^"]+"\s*src="(?P<url>[^"]+)'''))
        subtitles.update(__parse_to_dict(html, r'''"tracks":.+?"kind":\s*"captions",\s*"file":\s*"(?P<url>[^"]+).+?"label":\s*"(?P<label>[^"]+)'''))
        subtitles.update(__parse_to_dict(html, r'''"file":\s*"(?P<url>[^"]+).+?"label":\s*"(?P<label>[^"]+)","kind":"(?:captions|subtitles)"'''))

    for regex in patterns:
        subtitles.update(__parse_to_dict(html, regex))

    return subtitles


def get_media_url(
        url, result_blacklist=None, subs=False,
        patterns=None, generic_patterns=True,
        subs_patterns=None, generic_subs_patterns=True,
        referer=True, redirect=True,
        ssl_verify=True, verifypeer=True):
    if patterns is None:
        patterns = []
    if subs_patterns is None:
        subs_patterns = []
    scheme = urllib_parse.urlparse(url).scheme
    if result_blacklist is None:
        result_blacklist = []
    elif isinstance(result_blacklist, str):
        result_blacklist = [result_blacklist]

    result_blacklist = list(set(result_blacklist + ['.smil']))  # smil(not playable) contains potential sources, only blacklist when called from here
    net = common.Net(ssl_verify=ssl_verify)
    headers = {'User-Agent': common.RAND_UA}
    rurl = urllib_parse.urljoin(url, '/')
    if isinstance(referer, six.string_types):
        headers.update({'Referer': referer})
    elif referer:
        headers.update({'Referer': rurl})
    response = net.http_GET(url, headers=headers, redirect=redirect)
    cookie = response.get_cookies()
    if cookie:
        headers.update({'Cookie': cookie})
    html = response.content
    headers.update({'Referer': rurl, 'Origin': rurl[:-1]})
    if not verifypeer:
        headers.update({'verifypeer': 'false'})
    source_list = scrape_sources(html, result_blacklist, scheme, patterns, generic_patterns, rurl)
    source = pick_source(source_list)
    source = urllib_parse.quote(source, '/:?=&!') + append_headers(headers)
    if subs:
        subtitles = scrape_subtitles(html, rurl, scheme, subs_patterns, generic_subs_patterns)
        return source, subtitles
    return source


def cleanse_html(html):
    for match in re.finditer('<!--(.*?)-->', html, re.DOTALL):
        if match.group(1)[-2:] != '//':
            html = html.replace(match.group(0), '')

    html = re.sub(r'''<(div|span)[^>]+style=["'](visibility:\s*hidden|display:\s*none);?["']>.*?</\\1>''', '', html, re.I | re.DOTALL)
    return html


def get_dom(html, tag):
    start_str = '<%s' % (tag.lower())
    end_str = '</%s' % (tag.lower())

    results = []
    html = html.lower()
    while html:
        start = html.find(start_str)
        end = html.find(end_str, start)
        pos = html.find(start_str, start + 1)
        while pos < end and pos != -1:
            tend = html.find(end_str, end + len(end_str))
            if tend != -1:
                end = tend
            pos = html.find(start_str, pos + 1)

        if start == -1 and end == -1:
            break
        elif start > -1 and end > -1:
            result = html[start:end]
        elif end > -1:
            result = html[:end]
        elif start > -1:
            result = html[start:]
        else:
            break

        results.append(result)
        html = html[start + len(start_str):]

    return results


def fun_decode(vu, lc, hr='16'):
    import time

    def calcseed(lc, hr):
        f = lc.replace('$', '').replace('0', '1')
        j = int(len(f) / 2)
        k = int(f[0:j + 1])
        el = int(f[j:])
        fi = abs(el - k) * 4
        s = str(fi)
        i = int(int(hr) / 2) + 2
        m = ''
        for g2 in range(j + 1):
            for h in range(1, 5):
                n = int(lc[g2 + h]) + int(s[g2])
                if n >= i:
                    n -= i
                m += str(n)
        return m

    if vu.startswith('function/'):
        vup = vu.split('/')
        uhash = vup[7][0: 2 * int(hr)]
        nchash = vup[7][2 * int(hr):]
        seed = calcseed(lc, hr)
        if seed and uhash:
            for k in range(len(uhash) - 1, -1, -1):
                el = k
                for m in range(k, len(seed)):
                    el += int(seed[m])
                while el >= len(uhash):
                    el -= len(uhash)
                n = ''
                for o in range(len(uhash)):
                    n += uhash[el] if o == k else uhash[k] if o == el else uhash[o]
                uhash = n
            vup[7] = uhash + nchash
        vu = '/'.join(vup[2:]) + '&rnd={}'.format(int(time.time() * 1000))
    return vu


def get_redirect_url(url, headers={}, form_data=None):
    class NoRedirection(urllib_request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    if form_data:
        if isinstance(form_data, dict):
            form_data = urllib_parse.urlencode(form_data)
        request = urllib_request.Request(url, six.b(form_data), headers=headers)
    else:
        request = urllib_request.Request(url, headers=headers)

    opener = urllib_request.build_opener(NoRedirection())
    try:
        response = opener.open(request, timeout=20)
    except urllib_error.HTTPError as e:
        response = e
    return response.headers.get('location') or url


def girc(page_data, url, co=None):
    """
    Code adapted from https://github.com/vb6rocod/utils/
    Copyright (C) 2019 vb6rocod
    and https://github.com/addon-lab/addon-lab_resolver_Project
    Copyright (C) 2021 ADDON-LAB, KAR10S
    """
    net = common.Net()
    hdrs = {'User-Agent': common.FF_USER_AGENT,
            'Referer': url}
    rurl = 'https://www.google.com/recaptcha/api.js'
    aurl = 'https://www.google.com/recaptcha/api2'
    key = re.search(r'(?:src="{0}\?.*?render|data-sitekey)="?([^"]+)'.format(rurl), page_data)
    if key:
        if co is None:
            co = b64encode((url[:-1] + ':443')).replace('=', '')
        key = key.group(1)
        rurl = '{0}?render={1}'.format(rurl, key)
        page_data1 = net.http_GET(rurl, headers=hdrs).content
        v = re.findall('releases/([^/]+)', page_data1)[0]
        rdata = {'ar': 1,
                 'k': key,
                 'co': co,
                 'hl': 'en',
                 'v': v,
                 'size': 'invisible',
                 'cb': '123456789'}
        page_data2 = net.http_GET('{0}/anchor?{1}'.format(aurl, urllib_parse.urlencode(rdata)), headers=hdrs).content
        rtoken = re.search('recaptcha-token.+?="([^"]+)', page_data2)
        if rtoken:
            rtoken = rtoken.group(1)
        else:
            return ''
        pdata = {'v': v,
                 'reason': 'q',
                 'k': key,
                 'c': rtoken,
                 'sa': '',
                 'co': co}
        hdrs.update({'Referer': aurl})
        page_data3 = net.http_POST('{0}/reload?k={1}'.format(aurl, key), form_data=pdata, headers=hdrs).content
        gtoken = re.search('rresp","([^"]+)', page_data3)
        if gtoken:
            return gtoken.group(1)

    return ''


def arc4(t, n):
    n = base64.b64decode(n)
    u = 0
    h = ''
    s = list(range(256))
    for e in range(256):
        x = t[e % len(t)]
        u = (u + s[e] + (x if isinstance(x, int) else ord(x))) % 256
        s[e], s[u] = s[u], s[e]

    e = u = 0
    for c in range(len(n)):
        e = (e + 1) % 256
        u = (u + s[e]) % 256
        s[e], s[u] = s[u], s[e]
        h += chr((n[c] if isinstance(n[c], int) else ord(n[c])) ^ s[(s[e] + s[u]) % 256])
    return h


def xor_string(encurl, key):
    """
    Code adapted from https://github.com/vb6rocod/utils/
    Copyright (C) 2019 vb6rocod
    """
    strurl = base64.b64decode(encurl).decode('utf-8')
    surl = ''
    for i in range(len(strurl)):
        surl += chr(ord(strurl[i]) ^ ord(key[i % len(key)]))
    return surl


def tear_decode(data_file, data_seed):
    from ctypes import c_int32 as i32

    def replacer(match):
        chars = {
            '0': '5',
            '1': '6',
            '2': '7',
            '5': '0',
            '6': '1',
            '7': '2'
        }
        return chars[match.group(0)]

    def str2bytes(a16):
        a21 = []
        for i in a16:
            a21.append(ord(i))
        return a21

    def bytes2str(a10):
        a13 = 0
        a14 = len(a10)
        a15 = ''
        while True:
            if a13 >= a14:
                break
            a15 += chr(255 & a10[a13])
            a13 += 1
        return a15

    def digest_pad(a36):
        a41 = []
        a39 = 0
        a40 = len(a36)
        a43 = 15 - (a40 % 16)
        a41.append(a43)
        while a39 < a40:
            a41.append(a36[a39])
            a39 += 1
        a45 = a43
        while a45 > 0:
            a41.append(0)
            a45 -= 1
        return a41

    def blocks2bytes(a29):
        a34 = []
        a33 = 0
        a32 = len(a29)
        while a33 < a32:
            a34 += [255 & rshift(i32(a29[a33]).value, 24)]
            a34 += [255 & rshift(i32(a29[a33]).value, 16)]
            a34 += [255 & rshift(i32(a29[a33]).value, 8)]
            a34 += [255 & a29[a33]]
            a33 += 1
        return a34

    def bytes2blocks(a22):
        a27 = []
        a28 = 0
        a26 = 0
        a25 = len(a22)
        while True:
            a27.append(((255 & a22[a26]) << 24) & 0xFFFFFFFF)
            a26 += 1
            if a26 >= a25:
                break
            a27[a28] |= ((255 & a22[a26]) << 16 & 0xFFFFFFFF)
            a26 += 1
            if a26 >= a25:
                break
            a27[a28] |= ((255 & a22[a26]) << 8 & 0xFFFFFFFF)
            a26 += 1
            if a26 >= a25:
                break
            a27[a28] |= (255 & a22[a26])
            a26 += 1
            if a26 >= a25:
                break
            a28 += 1
        return a27

    def xor_blocks(a76, a77):
        return [a76[0] ^ a77[0], a76[1] ^ a77[1]]

    def unpad(a46):
        a49 = 0
        a52 = []
        a53 = (7 & a46[a49])
        a49 += 1
        a51 = (len(a46) - a53)
        while a49 < a51:
            a52 += [a46[a49]]
            a49 += 1
        return a52

    def rshift(a, b):
        return (a % 0x100000000) >> b

    def tea_code(a79, a80):
        a85 = a79[0]
        a83 = a79[1]
        a87 = 0

        for a86 in range(32):
            a85 += i32((((i32(a83).value << 4) ^ rshift(i32(a83).value, 5)) + a83) ^ (a87 + a80[(a87 & 3)])).value
            a85 = i32(a85 | 0).value
            a87 = i32(a87).value - i32(1640531527).value
            a83 += i32(
                (((i32(a85).value << 4) ^ rshift(i32(a85).value, 5)) + a85) ^ (a87 + a80[(rshift(a87, 11) & 3)])).value
            a83 = i32(a83 | 0).value
        return [a85, a83]

    def binarydigest(a55):
        a63 = [1633837924, 1650680933, 1667523942, 1684366951]
        a62 = [1633837924, 1650680933]
        a61 = a62
        a66 = [0, 0]
        a68 = [0, 0]
        a59 = bytes2blocks(digest_pad(str2bytes(a55)))
        a65 = 0
        a67 = len(a59)
        while a65 < a67:
            a66[0] = a59[a65]
            a65 += 1
            a66[1] = a59[a65]
            a65 += 1
            a68[0] = a59[a65]
            a65 += 1
            a68[1] = a59[a65]
            a65 += 1
            a62 = tea_code(xor_blocks(a66, a62), a63)
            a61 = tea_code(xor_blocks(a68, a61), a63)
            a64 = a62[0]
            a62[0] = a62[1]
            a62[1] = a61[0]
            a61[0] = a61[1]
            a61[1] = a64

        return [a62[0], a62[1], a61[0], a61[1]]

    def ascii2bytes(a99):
        a2b = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10,
               'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20,
               'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25, 'a': 26, 'b': 27, 'c': 28, 'd': 29, 'e': 30,
               'f': 31, 'g': 32, 'h': 33, 'i': 34, 'j': 35, 'k': 36, 'l': 37, 'm': 38, 'n': 39, 'o': 40,
               'p': 41, 'q': 42, 'r': 43, 's': 44, 't': 45, 'u': 46, 'v': 47, 'w': 48, 'x': 49, 'y': 50,
               'z': 51, '0': 52, '1': 53, '2': 54, '3': 55, '4': 56, '5': 57, '6': 58, '7': 59, '8': 60,
               '9': 61, '-': 62, '_': 63}
        a6 = -1
        a7 = len(a99)
        a9 = 0
        a8 = []

        while True:
            while True:
                a6 += 1
                if a6 >= a7:
                    return a8
                if a99[a6] in a2b.keys():
                    break
            a8.insert(a9, i32(i32(a2b[a99[a6]]).value << 2).value)
            while True:
                a6 += 1
                if a6 >= a7:
                    return a8
                if a99[a6] in a2b.keys():
                    break
            a3 = a2b[a99[a6]]
            a8[a9] |= rshift(i32(a3).value, 4)
            a9 += 1
            a3 = (15 & a3)
            if (a3 == 0) and (a6 == (a7 - 1)):
                return a8
            a8.insert(a9, i32(a3).value << 4)
            while True:
                a6 += 1
                if a6 >= a7:
                    return a8
                if a99[a6] in a2b.keys():
                    break
            a3 = a2b[a99[a6]]
            a8[a9] |= rshift(i32(a3).value, 2)
            a9 += 1
            a3 = (3 & a3)
            if (a3 == 0) and (a6 == (a7 - 1)):
                return a8
            a8.insert(a9, i32(a3).value << 6)
            while True:
                a6 += 1
                if a6 >= a7:
                    return a8
                if a99[a6] in a2b.keys():
                    break
            a8[a9] |= a2b[a99[a6]]
            a9 += 1

        return a8

    def ascii2binary(a0):
        return bytes2blocks(ascii2bytes(a0))

    def tea_decode(a90, a91):
        a95 = a90[0]
        a96 = a90[1]
        a97 = i32(-957401312).value
        for a98 in range(32):
            a96 = i32(a96).value - ((((i32(a95).value << 4) ^ rshift(i32(a95).value, 5)) + a95) ^ (
                a97 + a91[(rshift(i32(a97).value, 11) & 3)]))
            a96 = i32(a96 | 0).value
            a97 = i32(a97).value + 1640531527
            a97 = i32(a97 | 0).value
            a95 = i32(a95).value - i32(
                (((i32(a96).value << 4) ^ rshift(i32(a96).value, 5)) + a96) ^ (a97 + a91[(a97 & 3)])).value
            a95 = i32(a95 | 0).value
        return [a95, a96]

    if data_seed is None or data_file is None:
        return ''

    data_seed = re.sub('[012567]', replacer, data_seed)
    new_data_seed = binarydigest(data_seed)
    new_data_file = ascii2binary(data_file)
    a69 = 0
    a70 = len(new_data_file)
    a71 = [1633837924, 1650680933]
    a73 = [0, 0]
    a74 = []
    while a69 < a70:
        a73[0] = new_data_file[a69]
        a69 += 1
        a73[1] = new_data_file[a69]
        a69 += 1
        a72 = xor_blocks(a71, tea_decode(a73, new_data_seed))
        a74 += a72
        a71[0] = a73[0]
        a71[1] = a73[1]
    return re.sub('[012567]', replacer, bytes2str(unpad(blocks2bytes(a74))))


def duboku_decode(encurl):
    base64_decode_chars = [
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, 62, -1, -1, -1, 63, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1,
        -1, -1, -1, -1, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1, -1, 26, 27, 28,
        29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
        49, 50, 51, -1, -1, -1, -1, -1
    ]

    length = len(encurl)
    i = 0
    out = []
    while i < length:
        while True:
            c1 = base64_decode_chars[ord(encurl[i]) & 0xff]
            i += 1
            if not (i < length and c1 == -1):
                break
        if c1 == -1:
            break
        while True:
            c2 = base64_decode_chars[ord(encurl[i]) & 0xff]
            i += 1
            if not (i < length and c2 == -1):
                break
        if c2 == -1:
            break
        out.append(chr((c1 << 2) | ((c2 & 0x30) >> 4)))
        while True:
            c3 = ord(encurl[i]) & 0xff
            i += 1
            if c3 == 61:
                return ''.join(out)
            c3 = base64_decode_chars[c3]
            if not (i < length and c3 == -1):
                break
        if c3 == -1:
            break
        out.append(chr(((c2 & 0XF) << 4) | ((c3 & 0x3C) >> 2)))
        while True:
            c4 = ord(encurl[i]) & 0xff
            i += 1
            if c4 == 61:
                return ''.join(out)
            c4 = base64_decode_chars[c4]
            if not (i < length and c4 == -1):
                break
        if c4 == -1:
            break
        out.append(chr(((c3 & 0x03) << 6) | c4))
    return ''.join(out)


def base164(e):
    t = 'АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
    n = ''
    o = 0
    while o < len(e):
        r = t.index(e[o])
        o += 1
        i = t.index(e[o])
        o += 1
        s = t.index(e[o])
        o += 1
        a = t.index(e[o])
        o += 1
        r = r << 2 | i >> 4
        i = (15 & i) << 4 | s >> 2
        c = (3 & s) << 6 | a
        n += chr(r)
        if s != 64:
            n += chr(i)
        if a != 64:
            n += chr(c)
    return n


def Tdecode(vidurl):
    replacemap = {'M': r'\u041c', 'A': r'\u0410', 'B': r'\u0412', 'C': r'\u0421', 'E': r'\u0415', '=': '~', '+': '.', '/': ','}

    for key in replacemap:
        vidurl = vidurl.replace(replacemap[key], key)
    vidurl = base64.b64decode(vidurl)
    return vidurl.decode('utf-8')


def b64decode(t, binary=False):
    if len(t) % 4 != 0:
        t += '=' * (-len(t) % 4)
    r = base64.b64decode(t)
    return r if binary else six.ensure_str(r)


def b64encode(b):
    return six.ensure_str(base64.b64encode(b if isinstance(b, bytes) else six.b(b)))

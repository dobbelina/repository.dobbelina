'''
    Cumination
    Copyright (C) 2015 Whitecream

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
'''

import re
import os
import sqlite3
from six.moves import urllib_parse
import six
import json
import random
import time
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import xbmc

bu = 'https://chaturbate.com/'
rapi = 'https://chaturbate.com/api/ts/roomlist/room-list/'
tapi = 'https://chaturbate.com/api/ts/hashtags/tag-table-data/'
site = AdultSite('chaturbate', '[COLOR hotpink]Chaturbate[/COLOR]', bu, 'chaturbate.png', 'chaturbate', True)

addon = utils.addon
_cb_proxy = None
_cb_proxy_state = None
HTTP_HEADERS_IPAD = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 8_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B410 Safari/600.1.4'}


@site.register(default_mode=True)
def Main():
    female = addon.getSetting("chatfemale") == "true"
    male = addon.getSetting("chatmale") == "true"
    couple = addon.getSetting("chatcouple") == "true"
    trans = addon.getSetting("chattrans") == "true"

    site.add_dir('[COLOR red]Refresh Chaturbate images[/COLOR]', '', 'clean_database', '', Folder=False)
    # site.add_dir('[COLOR hotpink]Look for Online Models[/COLOR]', rapi + '?limit=100&offset=0&keywords=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Look for Online Models[/COLOR]', site.url + 'ax/search/?keywords=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Featured[/COLOR]', rapi + '?limit=100&offset=0', 'List', '', '')
    site.add_dir('[COLOR yellow]Current Hour\'s Top Cams[/COLOR]', bu + 'api/ts/contest/leaderboard/', 'topCams', '', '')
    site.add_dir('[COLOR yellow]Online Favorites[/COLOR]', bu, 'onlineFav', '', '')
    site.add_dir('[COLOR yellow]Followed Cams[/COLOR]', rapi + '?enable_recommendations=true&follow=true&limit=100&offline=false&offset=0', 'List', '', '')

    if female:
        site.add_dir('[COLOR violet]Female[/COLOR]', rapi + '?genders=f&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - Female[/COLOR]', tapi + '?sort=ht&page=1&g=f&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Female[/COLOR]', rapi + '?genders=f&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Female[/COLOR]', rapi + '?genders=f&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=SA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Female[/COLOR]', rapi + '?genders=f&limit=100&regions=O&offset=0', 'List', '', '')
    if couple:
        site.add_dir('[COLOR violet]Couple[/COLOR]', rapi + '?genders=c&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - Couple[/COLOR]', tapi + '?sort=ht&page=1&g=c&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Couple[/COLOR]', rapi + '?genders=c&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Couple[/COLOR]', rapi + '?genders=c&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=SA&offCoupleMaleset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Couple[/COLOR]', rapi + '?genders=c&limit=100&regions=O&offset=0', 'List', '', '')
    if male:
        site.add_dir('[COLOR violet]Male[/COLOR]', rapi + '?genders=m&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - Male[/COLOR]', tapi + '?sort=ht&page=1&g=m&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - Male[/COLOR]', rapi + '?genders=m&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - Male[/COLOR]', rapi + '?genders=m&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=SA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - Male[/COLOR]', rapi + '?genders=m&limit=100&regions=O&offset=0', 'List', '', '')
    if trans:
        site.add_dir('[COLOR violet]TransSexual[/COLOR]', rapi + '?genders=t&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Tags - TransSexual[/COLOR]', tapi + '?sort=ht&page=1&g=t&limit=100', 'Tags', '', '')
        site.add_dir('[COLOR hotpink]New Cams - TransSexual[/COLOR]', rapi + '?genders=t&new_cams=true&limit=100&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Teen Cams (18+) - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=18&to_age=19&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]20 to 30 Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=20&to_age=30&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]30 to 50 Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=30&to_age=50&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Mature Cams (50+) - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&from_age=50&to_age=200&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]North American Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=NA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]South American Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=SA&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Euro Russian Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=ER&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Asian Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=AS&offset=0', 'List', '', '')
        site.add_dir('[COLOR hotpink]Other Region Cams - TransSexual[/COLOR]', rapi + '?genders=t&limit=100&regions=O&offset=0', 'List', '', '')

    utils.eod()


def Online(stamp):
    days, weeks, years = None, None, None
    mins, secs = divmod(int(time.time()) - stamp, 60)
    hours, mins = divmod(mins, 60)
    if hours > 23:
        days, hours = divmod(hours, 24)
    if days and days > 6:
        weeks, days = divmod(days, 7)
    if weeks and weeks > 51:
        years, weeks = divmod(weeks, 52)
    if years:
        ret = '{:2d} years {:2d} weeks'.format(years, weeks)
    elif weeks:
        ret = '{:2d} weeks {:2d} days'.format(weeks, days)
    elif days:
        ret = '{:2d} days {:2d} hours'.format(days, hours)
    else:
        ret = '{:2d} hours {:2d} minutes'.format(hours, mins)
    ret = re.sub(r'(\s0\s\S+)', '', ret)
    ret = re.sub(r'(\s1\s\S+)s', r'\1', ret)
    return ret


@site.register()
def List(url, page=1):
    if 'follow=true' in url and 'offline=false' in url:
        site.add_dir('[COLOR yellow]Offline Rooms[/COLOR]', rapi + '?enable_recommendations=true&follow=true&limit=100&offline=true&offset=0', 'List', '', '')
    if 'follow=true' in url:
        login()
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)
    if not isinstance(page, int):
        page = 1

    listhtml = utils._getHtml(url)
    listhtml = json.loads(listhtml)
    models = listhtml.get('rooms')
    for model in models:
        name = model.get('username')
        videopage = '{0}{1}/'.format(bu, name)
        age = model.get('display_age')
        age = 'Unknown' if age is None else age
        location = model.get('location')
        if location:
            location = location.encode('utf8') if six.PY2 else location
            location = utils.cleantext(location)
        else:
            location = ''

        subject = model.get('subject')
        subject = subject.encode('utf8') if six.PY2 else subject
        subject = re.sub(r'<a.+', '', subject).strip()
        if 'offline=true' not in url:
            subject = utils.cleantext(subject) + "[CR][CR][COLOR deeppink]Location: [/COLOR]" + location + "[CR]" \
                + "[COLOR deeppink]Duration: [/COLOR]{0}[CR]".format(Online(model.get('start_timestamp'))) \
                + "[COLOR deeppink]Watching: [/COLOR]{0}[CR]".format(model.get('num_users')) \
                + "[COLOR deeppink]Followers: [/COLOR]{0}".format(model.get('num_followers'))
            name = '{0} [COLOR deeppink][{1}][/COLOR] {2}'.format(name, age, model.get('current_show'))
        else:
            subject = utils.cleantext(subject)
            if model.get('start_timestamp'):
                ago = re.sub(r'^\s*(\d+\s+\S+).*$', r'\1', Online(model.get('start_timestamp')))
                name = '{0} [COLOR deeppink][{1}][/COLOR] [COLOR blue]{2} ago[/COLOR]'.format(name, age, ago)
            else:
                name = '{0} [COLOR deeppink][{1}][/COLOR]'.format(name, age)
        tags = model.get('tags')
        if tags:
            tags = '[COLOR deeppink]#[/COLOR]' + ', [COLOR deeppink]#[/COLOR]'.join(tags)
            tags = tags.encode('utf-8') if six.PY2 else tags
            subject += "[CR][CR]" + tags
        img = model.get('img')

        id = model.get('username')
        follow = model.get('is_following')
        contextfollow = (utils.addon_sys + "?mode=chaturbate.Follow&id=" + urllib_parse.quote_plus(id))
        contextunfollow = (utils.addon_sys + "?mode=chaturbate.Unfollow&id=" + urllib_parse.quote_plus(id))
        contextmenu = [('[COLOR violet]Follow [/COLOR]{}'.format(name), 'RunPlugin(' + contextfollow + ')')] if not follow else [('[COLOR violet]Unfollow [/COLOR]{}'.format(name), 'RunPlugin(' + contextunfollow + ')')]
        contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(id))
        contextmenu.append(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(id), 'RunPlugin(' + contextrecord + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, subject, contextm=contextmenu, noDownload=True)

    total_items = listhtml.get('total_count')
    nextp = (page * 100) < total_items
    if nextp:
        next = (page * 100) + 1
        lastpg = -1 * (-total_items // 100)
        page = page + 1
        nurl = re.sub(r'offset=\d+', 'offset={0}'.format(next), url)
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page - 1, lastpg), nurl, 'List', site.img_next, page)

    utils.eod()


@site.register()
def SList(url):
    hdr = utils.base_hdrs.copy()
    hdr.update({'X-Requested-With': 'XMLHttpRequest'})
    listhtml = utils._getHtml(url, site.url, headers=hdr)
    jlist = json.loads(listhtml)
    for model in jlist.get('online', []):
        img = 'https://thumb.live.mmcdn.com/riw/{}.jpg'.format(model)
        contextfollow = (utils.addon_sys + "?mode=chaturbate.Follow&id=" + urllib_parse.quote_plus(model))
        contextunfollow = (utils.addon_sys + "?mode=chaturbate.Unfollow&id=" + urllib_parse.quote_plus(model))
        contextmenu = [('[COLOR violet]Follow [/COLOR]{}'.format(model), 'RunPlugin(' + contextfollow + ')'), ('[COLOR violet]Unfollow [/COLOR]{}'.format(model), 'RunPlugin(' + contextunfollow + ')')]
        videopage = '{0}{1}/'.format(bu, model)
        site.add_download_link(model, videopage, 'Playvid', img, contextm=contextmenu, noDownload=True)
    utils.eod()


@site.register(clean_mode=True)
def clean_database(showdialog=True):
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    try:
        with conn:
            list = conn.execute("SELECT id, cachedurl FROM texture WHERE url LIKE '%%%s%%';" % ".live.mmcdn.com")
            for row in list:
                conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                try:
                    os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                except:
                    pass
            conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".live.mmcdn.com")
            if showdialog:
                utils.notify('Finished', 'Chaturbate images cleared')
    except:
        pass


@site.register()
def Playvid(url, name):
    playmode = int(addon.getSetting('chatplay'))
    listhtml = utils._getHtml(url, headers=HTTP_HEADERS_IPAD)

    r = re.search(r'initialRoomDossier\s*=\s*"([^"]+)', listhtml)
    if r:
        data = six.b(r.group(1)).decode('unicode-escape')
        data = data if six.PY3 else data.encode('utf8')
        data = json.loads(data)
    else:
        data = False

    if data:
        m3u8stream = data.get('hls_source')
    else:
        m3u8stream = False

    # m3u8stream = m3u8stream.replace('playlist.m3u8', 'playlist_sfm4s.m3u8').replace('live-hls', 'live-c-fhls').replace('live-edge', 'live-c-fhls')

    if playmode == 0:
        if m3u8stream:
            import socket, threading, gzip, zlib  # noqa: E401
            # py2 (kodi 18.x leia) doesnt have http.server / socketserver,
            # those are py3 names. fall back to py2 names so the proxy
            # imports cleanly on older builds. issue #1845
            try:
                from http.server import BaseHTTPRequestHandler
                from socketserver import TCPServer, ThreadingMixIn
            except ImportError:
                from BaseHTTPServer import BaseHTTPRequestHandler
                from SocketServer import TCPServer, ThreadingMixIn
            from six.moves.urllib.request import Request as _Req, urlopen as _uopen
            from six.moves.urllib.parse import urljoin as _urljoin

            def _read_body(resp):
                # mmcdn edges return gzipped bodies even without Accept-Encoding,
                # sometimes with Content-Encoding header and sometimes without.
                # decompress on either signal so downstream decode/passthrough is clean.
                raw = resp.read()
                ce = (resp.headers.get('Content-Encoding') or '').lower()
                if ce == 'gzip' or raw[:2] == b'\x1f\x8b':
                    try:
                        raw = gzip.decompress(raw)
                    except Exception:
                        pass
                elif ce == 'deflate':
                    try:
                        raw = zlib.decompress(raw)
                    except Exception:
                        try:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                        except Exception:
                            pass
                return raw

            try:
                global _cb_proxy, _cb_proxy_state

                # Debug log for proxy events (toggle via Settings > enh_debug)
                _dbg_path = os.path.join(utils.TRANSLATEPATH('special://temp'), 'cb_proxy.log')
                _dbg_on = addon.getSetting('enh_debug') == 'true'

                def _dbg(msg):
                    if not _dbg_on:
                        return
                    try:
                        with open(_dbg_path, 'a') as f:
                            f.write('{} {}\n'.format(time.strftime('%H:%M:%S'), msg))
                    except Exception:
                        pass

                # Signal the previous stream's monitor/reconnect threads to exit
                # so the old srv reference doesn't keep the old proxy alive.
                if _cb_proxy_state is not None:
                    _dbg('CLEANUP: signalling old state stopping=True')
                    _cb_proxy_state['stopping'] = True
                    _cb_proxy_state = None

                if _cb_proxy is not None:
                    _dbg('CLEANUP: shutting down previous proxy {}'.format(
                        getattr(_cb_proxy, 'server_address', '?')))
                    try:
                        _cb_proxy.shutdown()
                        _dbg('CLEANUP: shutdown() OK')
                    except Exception as cex1:
                        _dbg('CLEANUP: shutdown() FAILED: {}'.format(cex1))
                    try:
                        _cb_proxy.server_close()
                        _dbg('CLEANUP: server_close() OK')
                    except Exception as cex2:
                        _dbg('CLEANUP: server_close() FAILED: {}'.format(cex2))
                    _cb_proxy = None

                headers = HTTP_HEADERS_IPAD.copy()
                headers['Referer'] = url
                req = _Req(m3u8stream, headers=headers)
                master_raw = _read_body(_uopen(req, timeout=10)).decode('utf-8', 'replace')
                base = m3u8stream.rsplit('/', 1)[0] + '/'

                master_fixed = re.sub(
                    r'^(?!https?://)(?!#)(.+)$',
                    lambda m: _urljoin(base, m.group(1)),
                    master_raw, flags=re.MULTILINE)
                master_fixed = re.sub(
                    r'URI="(?!https?://)(.*?)"',
                    lambda m: 'URI="' + _urljoin(base, m.group(1)) + '"',
                    master_fixed, flags=re.IGNORECASE)

                # Bind proxy port first so we can rewrite chunklist URLs
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
                sock.close()

                # State for session reconnection
                _proxy_state = {
                    'stream_url': m3u8stream,
                    'headers': headers,
                    'url_map': {},
                    'last_refresh': 0,
                    'lock': threading.Lock(),
                    'chunklist_cache': {},
                    'seg_cdn_urls': {},
                    'latest_seg': {},
                }

                # Populate initial chunklist URL map (type_key -> cdn_url)
                for _line in master_fixed.splitlines():
                    _line = _line.strip()
                    if _line and not _line.startswith('#') and 'chunklist_' in _line:
                        _km = re.search(r'(chunklist_\d+_\w+)', _line)
                        if _km:
                            _proxy_state['url_map'][_km.group(1)] = _line
                for _mi in re.finditer(r'URI="(https?://[^"]*chunklist_[^"]*)"', master_fixed, re.IGNORECASE):
                    _km = re.search(r'(chunklist_\d+_\w+)', _mi.group(1))
                    if _km:
                        _proxy_state['url_map'][_km.group(1)] = _mi.group(1)
                _dbg('PROXY START port={} keys={}'.format(port, list(_proxy_state['url_map'].keys())))

                # Rewrite only .m3u8 chunklist URLs to go through our proxy
                # (leave init segments / .m4s files as direct CDN URLs)
                master_fixed = re.sub(
                    r'^(https?://[^\s]+\.m3u8[^\s]*)$',
                    lambda m: 'http://127.0.0.1:{}/chunklist?url={}'.format(port, urllib_parse.quote(m.group(1), safe='')),
                    master_fixed, flags=re.MULTILINE)
                master_fixed = re.sub(
                    r'URI="(https?://[^"]+\.m3u8[^"]*)"',
                    lambda m: 'URI="http://127.0.0.1:{}/chunklist?url={}"'.format(port, urllib_parse.quote(m.group(1), safe='')),
                    master_fixed, flags=re.IGNORECASE)
                master_bytes = master_fixed.encode('utf-8')

                def _refresh_session():
                    """Re-fetch master playlist to get fresh session tokens."""
                    now = time.time()
                    with _proxy_state['lock']:
                        if now - _proxy_state['last_refresh'] < 2:
                            return False
                        _proxy_state['last_refresh'] = now
                    try:
                        rq = _Req(_proxy_state['stream_url'], headers=_proxy_state['headers'])
                        raw = _read_body(_uopen(rq, timeout=10)).decode('utf-8', 'replace')
                        burl = _proxy_state['stream_url'].rsplit('/', 1)[0] + '/'
                        fixed = re.sub(
                            r'^(?!https?://)(?!#)(.+)$',
                            lambda m: _urljoin(burl, m.group(1)),
                            raw, flags=re.MULTILINE)
                        fixed = re.sub(
                            r'URI="(?!https?://)(.*?)"',
                            lambda m: 'URI="' + _urljoin(burl, m.group(1)) + '"',
                            fixed, flags=re.IGNORECASE)
                        new_map = {}
                        for line in fixed.splitlines():
                            line = line.strip()
                            if line and not line.startswith('#') and 'chunklist_' in line:
                                km = re.search(r'(chunklist_\d+_\w+)', line)
                                if km:
                                    new_map[km.group(1)] = line
                        for mi in re.finditer(r'URI="(https?://[^"]*chunklist_[^"]*)"', fixed, re.IGNORECASE):
                            km = re.search(r'(chunklist_\d+_\w+)', mi.group(1))
                            if km:
                                new_map[km.group(1)] = mi.group(1)
                        with _proxy_state['lock']:
                            _proxy_state['url_map'].update(new_map)
                            # Invalidate cached chunklists and segment maps so the
                            # next ISA request pulls a fresh chunklist with the new
                            # JWT session instead of serving stale dead-segment bodies.
                            _proxy_state['chunklist_cache'].clear()
                            _proxy_state['seg_cdn_urls'].clear()
                            _proxy_state['latest_seg'].clear()
                        _dbg('REFRESH OK new_keys={} caches_cleared'.format(list(new_map.keys())))
                        return True
                    except Exception as e:
                        _dbg('REFRESH FAIL {}'.format(e))
                        return False

                def _force_stop(reason):
                    _proxy_state['stopping'] = True
                    _dbg('FORCE STOP: {}'.format(reason))
                    # skip the global Stop if player moved to another proxy
                    # (sibling playvid). still tear our own proxy down below.
                    try:
                        cur = xbmc.Player().getPlayingFile() or ''
                    except Exception:
                        cur = ''
                    if cur and ':{}/'.format(port) not in cur:
                        _dbg('PlayerControl(Stop) skipped, player on diff proxy {}'.format(cur))
                    else:
                        try:
                            xbmc.executebuiltin('PlayerControl(Stop)')
                            _dbg('PlayerControl(Stop) sent')
                        except Exception as ex2:
                            _dbg('PlayerControl(Stop) FAILED: {}'.format(ex2))
                    time.sleep(3)
                    try:
                        _cb_proxy.shutdown()
                    except Exception as sex:
                        _dbg('shutdown err: {}'.format(sex))
                    try:
                        _cb_proxy.server_close()
                        _dbg('Proxy server shutdown')
                    except Exception as sex:
                        _dbg('close err: {}'.format(sex))

                def _bg_reconnect():
                    needs_force_stop = True
                    try:
                        for _attempt in range(15):
                            if _proxy_state.get('stopping'):
                                _dbg('RECONNECT aborted - proxy stopping')
                                needs_force_stop = False
                                return
                            _dbg('RECONNECT attempt={}/15'.format(_attempt + 1))
                            if _refresh_session():
                                _dbg('RECONNECT OK attempt={}'.format(_attempt + 1))
                                with _proxy_state['lock']:
                                    _proxy_state['reconnecting'] = False
                                _dbg('WATCHDOG waiting 8s to check ISA')
                                time.sleep(8)
                                if _proxy_state.get('stopping'):
                                    needs_force_stop = False
                                    return
                                gap = time.time() - _proxy_state.get('last_request', 0)
                                _dbg('WATCHDOG gap={:.1f}s'.format(gap))
                                if gap > 6:
                                    _dbg('WATCHDOG over threshold, rechecking in 3s')
                                    time.sleep(3)
                                    if _proxy_state.get('stopping'):
                                        needs_force_stop = False
                                        return
                                    gap2 = time.time() - _proxy_state.get('last_request', 0)
                                    _dbg('WATCHDOG recheck gap={:.1f}s'.format(gap2))
                                    if gap2 > 6:
                                        needs_force_stop = False
                                        _force_stop('ISA silent {:.0f}s after reconnect'.format(gap2))
                                        return
                                    _dbg('WATCHDOG OK on recheck -- ISA recovered')
                                else:
                                    _dbg('WATCHDOG OK -- ISA still active')
                                needs_force_stop = False
                                return
                            time.sleep(2)
                        _dbg('GIVING UP after 15 attempts')
                    except Exception as ex:
                        try:
                            _dbg('RECONNECT THREAD CRASHED: {}'.format(ex))
                        except Exception:
                            pass
                    finally:
                        if needs_force_stop and not _proxy_state.get('stopping'):
                            try:
                                _force_stop('reconnect exhausted')
                            except Exception:
                                pass

                def _trigger_reconnect(reason):
                    with _proxy_state['lock']:
                        if _proxy_state.get('reconnecting') or _proxy_state.get('stopping'):
                            return
                        _proxy_state['reconnecting'] = True
                    _dbg('RECONNECT TRIGGERED: {}'.format(reason))
                    t2 = threading.Thread(target=_bg_reconnect)
                    t2.daemon = True
                    t2.start()

                # Localhost proxy: serves master + proxies chunklists with auto-reconnect
                class _H(BaseHTTPRequestHandler):
                    def do_GET(self):
                        if self.path.startswith('/chunklist'):
                            parsed = urllib_parse.urlparse(self.path)
                            params = urllib_parse.parse_qs(parsed.query)
                            req_url = params.get('url', [None])[0]
                            if not req_url:
                                self.send_error(400)
                                return
                            km = re.search(r'(chunklist_\d+_\w+)', req_url)
                            type_key = km.group(1) if km else None
                            cdn_url = _proxy_state['url_map'].get(type_key, req_url) if type_key else req_url
                            _proxy_state['last_request'] = time.time()

                            def _fetch_and_absolutize(u):
                                """Fetch chunklist, absolutize relative URIs, and route segments through proxy."""
                                creq = _Req(u, headers=_proxy_state['headers'])
                                resp = _uopen(creq, timeout=10)
                                raw = _read_body(resp).decode('utf-8', 'replace')
                                cbase = u.rsplit('/', 1)[0] + '/'
                                raw = re.sub(
                                    r'^(?!https?://)(?!#)(\S+)$',
                                    lambda m: _urljoin(cbase, m.group(1)),
                                    raw, flags=re.MULTILINE)
                                raw = re.sub(
                                    r'URI="(?!https?://)([^"]+)"',
                                    lambda m: 'URI="' + _urljoin(cbase, m.group(1)) + '"',
                                    raw, flags=re.IGNORECASE)
                                # Track current CDN segment URLs for fallback
                                for _l in raw.splitlines():
                                    _l = _l.strip()
                                    if _l and not _l.startswith('#') and '.m4s' in _l:
                                        _sn = _l.rsplit('/', 1)[-1].split('?')[0]
                                        _proxy_state['seg_cdn_urls'][_sn] = _l
                                        if type_key:
                                            _proxy_state['latest_seg'][type_key] = _l
                                # Rewrite segment URLs to go through localhost proxy
                                raw = re.sub(
                                    r'^(https?://[^\s]+\.m4s[^\s]*)$',
                                    lambda m: 'http://127.0.0.1:{}/segment?url={}'.format(port, urllib_parse.quote(m.group(1), safe='')),
                                    raw, flags=re.MULTILINE)
                                raw = re.sub(
                                    r'URI="(https?://[^"]+\.m4s[^"]*)"',
                                    lambda m: 'URI="http://127.0.0.1:{}/segment?url={}"'.format(port, urllib_parse.quote(m.group(1), safe='')),
                                    raw, flags=re.IGNORECASE)
                                return raw.encode('utf-8')

                            try:
                                data = _fetch_and_absolutize(cdn_url)
                                if type_key:
                                    _proxy_state['chunklist_cache'][type_key] = data
                                self.send_response(200)
                                self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                                self.send_header('Content-Length', str(len(data)))
                                self.end_headers()
                                self.wfile.write(data)
                            except Exception as e:
                                # If we already gave up, keep hammering stop
                                if _proxy_state.get('stopping'):
                                    _dbg('STOP REINFORCED (ISA still retrying)')
                                    try:
                                        xbmc.executebuiltin('PlayerControl(Stop)')
                                    except Exception:
                                        pass
                                    endlist = b'#EXTM3U\n#EXT-X-ENDLIST\n'
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                                    self.send_header('Content-Length', str(len(endlist)))
                                    self.end_headers()
                                    self.wfile.write(endlist)
                                    return

                                # CDN session died ,kick off background reconnect
                                _dbg('CHUNKLIST FAIL type={} err={}'.format(type_key, e))
                                _trigger_reconnect('chunklist fail type={}: {}'.format(type_key, e))

                                # While reconnecting, try serving from refreshed URLs
                                if type_key and not _proxy_state.get('stopping'):
                                    new_url = _proxy_state['url_map'].get(type_key)
                                    if new_url and new_url != cdn_url:
                                        try:
                                            data = _fetch_and_absolutize(new_url)
                                            self.send_response(200)
                                            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                                            self.send_header('Content-Length', str(len(data)))
                                            self.end_headers()
                                            self.wfile.write(data)
                                            _dbg('SERVED from refreshed URL type={}'.format(type_key))
                                            return
                                        except Exception:
                                            pass

                                # Serve cached playlist to keep ISA alive during reconnect
                                cached = _proxy_state['chunklist_cache'].get(type_key) if type_key else None
                                if cached:
                                    _dbg('SERVING CACHED playlist type={}'.format(type_key))
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                                    self.send_header('Content-Length', str(len(cached)))
                                    self.end_headers()
                                    self.wfile.write(cached)
                                else:
                                    endlist = b'#EXTM3U\n#EXT-X-ENDLIST\n'
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                                    self.send_header('Content-Length', str(len(endlist)))
                                    self.end_headers()
                                    self.wfile.write(endlist)
                        elif self.path.startswith('/segment'):
                            parsed = urllib_parse.urlparse(self.path)
                            params = urllib_parse.parse_qs(parsed.query)
                            seg_url = params.get('url', [None])[0]
                            if not seg_url:
                                self.send_error(400)
                                return
                            seg_name = seg_url.rsplit('/', 1)[-1].split('?')[0]
                            _proxy_state['last_request'] = time.time()
                            # Try the requested URL first
                            try:
                                sreq = _Req(seg_url, headers=_proxy_state['headers'])
                                sresp = _uopen(sreq, timeout=10)
                                data = sresp.read()
                                ct = sresp.headers.get('Content-Type', 'video/mp4')
                                self.send_response(200)
                                self.send_header('Content-Type', ct)
                                self.send_header('Content-Length', str(len(data)))
                                self.end_headers()
                                self.wfile.write(data)
                                return
                            except Exception as e:
                                _dbg('SEG FAIL {} {}'.format(seg_name, e))
                                _trigger_reconnect('segment fail: {}'.format(seg_name))
                            # Fallback: try current CDN URL for same segment name
                            current_url = _proxy_state['seg_cdn_urls'].get(seg_name)
                            if current_url and current_url != seg_url:
                                try:
                                    sreq = _Req(current_url, headers=_proxy_state['headers'])
                                    sresp = _uopen(sreq, timeout=10)
                                    data = sresp.read()
                                    ct = sresp.headers.get('Content-Type', 'video/mp4')
                                    self.send_response(200)
                                    self.send_header('Content-Type', ct)
                                    self.send_header('Content-Length', str(len(data)))
                                    self.end_headers()
                                    self.wfile.write(data)
                                    _dbg('SEG FALLBACK OK {}'.format(seg_name))
                                    return
                                except Exception as e2:
                                    _dbg('SEG FALLBACK FAIL {}'.format(e2))
                            # Last resort: serve the latest known segment for this track
                            tm = re.search(r'(video|audio)_(\d+)_llhls', seg_name)
                            if tm:
                                for tk, latest in _proxy_state['latest_seg'].items():
                                    if tm.group(1) in tk and tm.group(2) in tk:
                                        try:
                                            sreq = _Req(latest, headers=_proxy_state['headers'])
                                            sresp = _uopen(sreq, timeout=10)
                                            data = sresp.read()
                                            ct = sresp.headers.get('Content-Type', 'video/mp4')
                                            self.send_response(200)
                                            self.send_header('Content-Type', ct)
                                            self.send_header('Content-Length', str(len(data)))
                                            self.end_headers()
                                            self.wfile.write(data)
                                            _dbg('SEG LATEST OK {}'.format(seg_name))
                                            return
                                        except Exception as e3:
                                            _dbg('SEG LATEST FAIL {}'.format(e3))
                                            break
                            self.send_error(502)
                            return
                        else:
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                            self.send_header('Content-Length', str(len(master_bytes)))
                            self.end_headers()
                            self.wfile.write(master_bytes)

                    def do_HEAD(self):
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                        self.end_headers()

                    def log_message(self, *a):
                        pass

                class _S(ThreadingMixIn, TCPServer):
                    daemon_threads = True
                    allow_reuse_address = True

                srv = _S(('127.0.0.1', port), _H)
                _cb_proxy = srv
                _cb_proxy_state = _proxy_state
                t = threading.Thread(target=srv.serve_forever)
                t.daemon = True
                t.start()

                def _monitor_player():
                    """Poll xbmc.Player state and tear down the proxy when playback ends."""
                    _dbg('MONITOR: thread started for port={}'.format(port))
                    my_port_tag = ':{}/'.format(port)
                    try:
                        mon = xbmc.Monitor()
                        player = xbmc.Player()
                        # Grace window (15s) for ISA to actually begin playing OUR URL.
                        # We wait until getPlayingFile() actually points at us before
                        # starting the watch-for-stop loop, otherwise a rapid click
                        # would see the old stream's URL and immediately self-destruct.
                        confirmed = False
                        for _ in range(30):
                            if mon.abortRequested() or _proxy_state.get('stopping'):
                                break
                            try:
                                cur = player.getPlayingFile() if player.isPlaying() else ''
                            except Exception:
                                cur = ''
                            if cur and my_port_tag in cur:
                                confirmed = True
                                break
                            if mon.waitForAbort(0.5):
                                break
                        if not confirmed:
                            _dbg('MONITOR: never confirmed as active stream within 15s, tearing down')
                        else:
                            _dbg('MONITOR: confirmed active stream, watching for stop')
                            while not mon.abortRequested() and not _proxy_state.get('stopping'):
                                if not player.isPlaying():
                                    _dbg('MONITOR: player stopped, shutting down proxy')
                                    break
                                # We already confirmed we're the active URL, so if
                                # getPlayingFile now points elsewhere the user moved on.
                                try:
                                    cur = player.getPlayingFile()
                                except Exception:
                                    cur = ''
                                if cur and my_port_tag not in cur:
                                    _dbg('MONITOR: port={} no longer active (now {}), stopping'.format(port, cur))
                                    break
                                if mon.waitForAbort(1):
                                    break
                    except Exception as mex:
                        _dbg('MONITOR THREAD CRASHED: {}'.format(mex))
                    _dbg('MONITOR: teardown entered addr={}'.format(
                        getattr(srv, 'server_address', '?')))
                    _proxy_state['stopping'] = True
                    try:
                        srv.shutdown()
                        _dbg('MONITOR: shutdown() OK')
                    except Exception as mex2:
                        _dbg('MONITOR: shutdown err {}'.format(mex2))
                    try:
                        srv.server_close()
                        _dbg('MONITOR: proxy shutdown complete')
                    except Exception as mex3:
                        _dbg('MONITOR: close err {}'.format(mex3))

                _mt = threading.Thread(target=_monitor_player)
                _mt.daemon = True
                _mt.start()

                videourl = 'http://127.0.0.1:{}/master.m3u8'.format(port)
            except Exception:
                videourl = "{0}|{1}".format(m3u8stream, urllib_parse.urlencode(HTTP_HEADERS_IPAD))
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    elif playmode == 1:
        if data:
            streamserver = "rtmp://{}/live-edge".format(m3u8stream.split('/')[2])
            # streamserver = "rtmp://{}/live-edge".format(data['flash_host'])
            modelname = data['broadcaster_username']
            username_full = data['viewer_username']
            username = 'anonymous'
            room_pass = data['room_pass']
            swfurl = 'https://ssl-ccstatic.highwebmedia.com/theatermodeassets/CBV_TS_v1.0.swf'
            edge_auth = data['edge_auth']
            videourl = "%s app=live-edge swfUrl=%s pageUrl=%s conn=S:%s conn=S:%s conn=S:3.22 conn=S:%s conn=S:%s conn=S:%s playpath=mp4" % (streamserver, swfurl, url, username_full, modelname, username, room_pass, edge_auth)
        else:
            utils.notify('Oh oh', 'Couldn\'t find a playable webcam link')
            return

    vp = utils.VideoPlayer(name)
    vp.IA_check = 'IA'
    vp.play_from_direct_link(videourl)
    vp.progress.close()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = urllib_parse.quote_plus(keyword)
        url += title
        SList(url)


@site.register()
def topCams(url):
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)
    response = utils._getHtml(url)
    jsonTop = json.loads(response)['top']
    for iTop in jsonTop:
        subject = '[COLOR deeppink]Name: [/COLOR]' + iTop['room_user'] + '[CR]' \
            + '[CR][COLOR deeppink]Points: [/COLOR]' + str(iTop['points']) + '[CR]' \
            + '[COLOR deeppink]Watching: [/COLOR]' + str(iTop['viewers'])
        site.add_download_link(iTop['room_user'], bu + iTop['room_user'] + '/', 'Playvid',
                               iTop['image_url'], subject, noDownload=True)
    utils.eod()


@site.register()
def Tags(url, page=1):
    cat = re.search(r'&g=([^&]*)', url).group(1)
    html = utils.getHtml(url, site.url)
    jdata = json.loads(html)
    total = jdata["total"]
    for tag in jdata["hashtags"]:
        name = tag["hashtag"]
        count = tag["room_count"]
        img = tag["top_rooms"][0].get("img", '') if tag["top_rooms"] else ''
        tagurl = rapi + '?genders={0}&hashtags={1}&limit=100&offset=0'.format(cat, name)
        name += ' [COLOR hotpink][' + str(count) + '][/COLOR]'
        site.add_dir(name, tagurl, 'List', img, 1)
    if page * 100 < total:
        lastpg = -1 * (-total // 100)
        np_url = url.replace('&page={}'.format(page), '&page={}'.format(page + 1))
        site.add_dir('Next Page.. (Currently in Page {0} of {1})'.format(page, lastpg), np_url, 'Tags', site.img_next, page=page + 1)
    utils.eod()


@site.register()
def onlineFav(url):
    if addon.getSetting("chaturbate") == "true":
        clean_database(False)

    wmArray = ["C9m5N", "tfZSl", "jQrKO", "5XO2a", "WXomN", "zM6MR", "Lb2aB", "cIbs3", "zM6MR", "mnzQo", "N6TZA"]
    chaturbate_url = 'https://chaturbate.com/affiliates/api/onlinerooms/?format=json&wm=' + random.choice(wmArray)
    data_chat = utils._getHtml(chaturbate_url, '')
    model_list = json.loads(data_chat)
    model_lookup = {item['username']: item for item in model_list}
    conn = sqlite3.connect(utils.favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT DISTINCT name, url, image FROM favorites WHERE mode='chaturbate.Playvid'")
    result = c.fetchall()
    c.close()
    for (name, url, image) in result:
        stripped_name = name.split('[COLOR')[0].strip()
        if stripped_name in model_lookup:
            model = model_lookup[stripped_name]
            image = model["image_url"]
            current_show = ''
            if "current_show" in model:
                if model["current_show"] != "public":
                    current_show = '[COLOR blue] {}[/COLOR]'.format(model["current_show"])
            subject = model["room_subject"] if utils.PY3 else model["room_subject"].encode('utf8')
            location = model["location"] if utils.PY3 else model["location"].encode('utf8')
            subject = utils.cleantext(subject.split(' #')[0]) + "[CR][CR][COLOR deeppink]Location: [/COLOR]" + location + "[CR]" \
                + "[COLOR deeppink]Duration: [/COLOR]" + str(round(model["seconds_online"] / 3600, 1)) + " hrs[CR]" \
                + "[COLOR deeppink]Watching: [/COLOR]" + str(model["num_users"]) + " viewers"
            tags = '[COLOR deeppink]#[/COLOR]' + ', [COLOR deeppink]#[/COLOR]'.join(model["tags"])
            tags = tags if utils.PY3 else tags.encode('utf8')
            subject += "[CR][CR]" + tags

            contextmenu = []
            id = model["username"]
            contextrecord = (utils.addon_sys + "?mode=chaturbate.Record&id=" + urllib_parse.quote_plus(id))
            contextmenu.append(('[COLOR violet]Find recordings featuring [/COLOR]{}[COLOR violet] on Cloudbate[/COLOR]'.format(id), 'RunPlugin(' + contextrecord + ')'))

            site.add_download_link(name + current_show, url, 'Playvid', image, utils.cleantext(subject), noDownload=True, fav='del', contextm=contextmenu)
    utils.eod()


def login():
    sessionid = addon.getSetting('sessionid')
    if len(sessionid) == 32:
        session_cookie = get_cookie()
        if sessionid not in session_cookie:
            cookie = {'solution': {"cookies": [{'name': "sessionid", 'domain': ".chaturbate.com", 'value': sessionid, 'path': '/', 'secure': True, 'expiry': None, 'httpOnly': None}],
                                   "userAgent": utils.USER_AGENT}}
            utils.savecookies(cookie)

    url = 'https://chaturbate.com/followed-cams/'
    loginurl = 'https://chaturbate.com/auth/login/?next=/followed-cams/'

    loginhtml = utils._getHtml(url, site.url)
    if '<h1>Chaturbate Login</h1>' not in loginhtml:
        return

    username = utils._get_keyboard(default='', heading='Input your Chaturbate username')
    password = utils._get_keyboard(default='', heading='Input your Chaturbate password', hidden=True)

    match = re.compile(r'"csrfmiddlewaretoken"\s+value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(loginhtml)
    if not match:
        return

    csrfmiddlewaretoken = match[0]
    hdr = utils.base_hdrs
    hdr.update({'Referer': 'https://chaturbate.com/auth/login/?next=/followed-cams/'})
    postRequest = {"next": "/followed-cams/",
                   "csrfmiddlewaretoken": csrfmiddlewaretoken,
                   "username": username,
                   "password": password,
                   "rememberme": "on"}
    response = utils._postHtml(loginurl, headers=hdr, form_data=postRequest)
    if '<h1>Chaturbate Login</h1>' in response:
        utils.notify('Chaturbate', 'Login failed please check your username and password')


@site.register()
def Unfollow(id):
    url = 'https://chaturbate.com/follow/unfollow/{}/'.format(id)
    html = utils._getHtml(url, site.url)
    if '<h1>Chaturbate Login</h1>' in html:
        login()
        html = utils._getHtml(url, site.url)
    match = re.compile(r'"csrfmiddlewaretoken"\s+value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if not match:
        return
    csrfmiddlewaretoken = match[0]
    hdr = utils.base_hdrs
    hdr.update({'Referer': 'https://chaturbate.com/'})
    postRequest = {"csrfmiddlewaretoken": csrfmiddlewaretoken}
    response = utils._postHtml(url, headers=hdr, form_data=postRequest)
    if '"following": false' in response:
        utils.notify('Chaturbate', 'NOT FOLLOWING [COLOR hotpink]{}[/COLOR]'.format(id))
        utils.refresh()


@site.register()
def Follow(id):
    url = 'https://chaturbate.com/follow/follow/{}/'.format(id)
    html = utils._getHtml(url, site.url)
    if '<h1>Chaturbate Login</h1>' in html:
        login()
        html = utils._getHtml(url, site.url)
    match = re.compile(r'"csrfmiddlewaretoken"\s+value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    if not match:
        return
    csrfmiddlewaretoken = match[0]
    hdr = utils.base_hdrs
    hdr.update({'Referer': 'https://chaturbate.com/'})
    postRequest = {"csrfmiddlewaretoken": csrfmiddlewaretoken}
    response = utils._postHtml(url, headers=hdr, form_data=postRequest)
    if '"following": true' in response:
        utils.notify('Chaturbate', 'FOLLOWING [COLOR hotpink]{}[/COLOR]'.format(id))
        utils.refresh()


def get_cookie():
    domain = ".chaturbate.com"
    cookiestr = ""
    for cookie in utils.cj:
        if cookie.domain == domain and cookie.name == 'sessionid':
            cookiestr = cookie.value
    return cookiestr


@site.register()
def Record(id):
    url = 'https://www.cloudbate.com/search/{0}/'
    contexturl = (utils.addon_sys + "?mode=cloudbate.Search&url={}&keyword={}".format(urllib_parse.quote_plus(url), id))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')
    utils.eod()

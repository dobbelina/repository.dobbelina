"""
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
"""

import base64
import gzip
import json
import os.path
import re
import sqlite3
import ssl
import sys
import tempfile
import time
from functools import wraps
from math import ceil

import six
import StorageServer
from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon
from resources.lib import cloudflare, random_ua, strings
from resources.lib.basics import (addDir, addon, addon_handle, addon_sys,
                                  cookiePath, cum_image, cuminationicon, eod,
                                  favoritesdb, keys, searchDir)
from resources.lib.brotlidecpy import decompress
from resources.lib.url_dispatcher import URL_Dispatcher
from resources.lib.jsonrpc import toggle_debug
from six.moves import (html_parser, http_cookiejar, urllib_error, urllib_parse,
                       urllib_request)

cache = StorageServer.StorageServer("cumination", int(addon.getSetting('cache_time')))
url_dispatcher = URL_Dispatcher('utils')

USER_AGENT = random_ua.get_ua()
PY2 = six.PY2
PY3 = six.PY3
TRANSLATEPATH = xbmcvfs.translatePath if PY3 else xbmc.translatePath
LOGINFO = xbmc.LOGINFO if PY3 else xbmc.LOGNOTICE
KODIVER = float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])

base_hdrs = {'User-Agent': USER_AGENT,
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
             'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
             'Accept-Encoding': 'gzip',
             'Accept-Language': 'en-US,en;q=0.8',
             'Connection': 'keep-alive'}

progress = xbmcgui.DialogProgress()
dialog = xbmcgui.Dialog()

urlopen = urllib_request.urlopen
cj = http_cookiejar.LWPCookieJar(TRANSLATEPATH(cookiePath))
Request = urllib_request.Request

handlers = [urllib_request.HTTPBasicAuthHandler(), urllib_request.HTTPHandler(), urllib_request.HTTPSHandler()]
ssl_context = ssl._create_unverified_context()
ssl._create_default_https_context = ssl._create_unverified_context
handlers.append(urllib_request.HTTPSHandler(context=ssl_context))


def kodilog(logvar, level=LOGINFO):
    xbmc.log("@@@@Cumination: " + str(logvar), level)


@url_dispatcher.register()
def clear_cache():
    """
    Clear the cache database.
    """
    msg = i18n('cache_cleared')
    cache.table_name = 'cumination'
    cache.cacheDelete('%get%')
    xbmcgui.Dialog().notification('Cumination', msg, cuminationicon, 3000, False)


@url_dispatcher.register()
def clear_cookies():
    msg = i18n('cookies_cleared')
    cj.clear()
    cj.save(cookiePath, ignore_discard=True)
    xbmcgui.Dialog().notification('Cumination', msg, cuminationicon, 3000, False)


def i18n(string_id):
    try:
        return six.ensure_str(addon.getLocalizedString(strings.STRINGS[string_id]))
    except Exception as e:
        kodilog('Failed String Lookup: %s (%s)' % (string_id, e))
        return string_id


if cj is not None:
    if os.path.isfile(TRANSLATEPATH(cookiePath)):
        try:
            cj.load(ignore_discard=True)
        except:
            try:
                xbmcvfs.delete(TRANSLATEPATH(cookiePath))
                pass
            except:
                dialog.ok(i18n('oh_oh'), i18n('cookie_lock'))
                pass
    cookie_handler = urllib_request.HTTPCookieProcessor(cj)
    handlers += [cookie_handler]

opener = urllib_request.build_opener(*handlers)
urllib_request.install_opener(opener)


class StopDownloading(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class NoRedirection(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def downloadVideo(url, name):

    def _pbhook(downloaded, filesize, url=None, dp=None, name=''):
        try:
            percent = min(int((downloaded * 100) / filesize), 100)
            currently_downloaded = float(downloaded) / (1024 * 1024)
            kbps_speed = int(downloaded / (time.perf_counter() if PY3 else time.clock() - start))
            if kbps_speed > 0:
                eta = (filesize - downloaded) / kbps_speed
            else:
                eta = 0
            kbps_speed = kbps_speed / 1024
            total = float(filesize) / (1024 * 1024)
            mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total)
            e = 'Speed: %.02f Kb/s ' % kbps_speed
            e += 'ETA: %02d:%02d' % divmod(eta, 60)
            dp.update(percent, '{0}[CR]{1}[CR]{2}'.format(name[:50], mbs, e))
        except:
            percent = 100
            dp.update(percent)
        if dp.iscanceled():
            dp.close()
            raise StopDownloading('Stopped Downloading')

    def getResponse(url, headers2, size):
        try:
            if size > 0:
                size = int(size)
                headers2['Range'] = 'bytes=%d-' % size

            req = Request(url, headers=headers2)

            resp = urlopen(req, timeout=30)
            return resp
        except:
            return None

    def doDownload(url, dest, dp, name):
        headers = {}
        if '|' in url:
            url, uheaders = url.split('|')
            headers = dict(urllib_parse.parse_qsl(uheaders))

        if 'User-Agent' not in list(headers.keys()):
            headers.update({'User-Agent': USER_AGENT})

        resp = getResponse(url, headers, 0)

        if not resp:
            dialog.ok("Cumination", '{0}[CR]{1}'.format(i18n('dnld_fail'), i18n('no_resp')))
            return False
        try:
            content = int(resp.headers['Content-Length'])
        except:
            content = 0
        try:
            resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
        except:
            resumable = False
        if resumable:
            six.print_("Download is resumable")

        if content < 1:
            dialog.ok("Cumination", '{0}[CR]{1}'.format(i18n('unkn_size'), i18n('no_dnld')))
            return False

        size = 8192
        mb = content / (1024 * 1024)

        if content < size:
            size = content

        total = 0
        errors = 0
        count = 0
        resume = 0
        sleep = 0

        six.print_('{0} : {1}MB {2} '.format(i18n('file_size'), mb, dest))
        f = xbmcvfs.File(dest, 'w')

        chunk = None
        chunks = []

        while True:
            downloaded = total
            for c in chunks:
                downloaded += len(c)
            percent = min(100 * downloaded / content, 100)

            _pbhook(downloaded, content, url, dp, name)

            chunk = None
            error = False

            try:
                chunk = resp.read(size)
                if not chunk:
                    if percent < 99:
                        error = True
                    else:
                        while len(chunks) > 0:
                            c = chunks.pop(0)
                            f.write(c)
                            del c
                        f.close()
                        return True

            except Exception as e:
                six.print_(str(e))
                error = True
                sleep = 10
                errno = 0

                if hasattr(e, 'errno'):
                    errno = e.errno

                if errno == 10035:  # 'A non-blocking socket operation could not be completed immediately'
                    pass

                if errno == 10054:  # 'An existing connection was forcibly closed by the remote host'
                    errors = 10  # force resume
                    sleep = 30

                if errno == 11001:  # 'getaddrinfo failed'
                    errors = 10  # force resume
                    sleep = 30

            if chunk:
                errors = 0
                chunks.append(chunk)
                if len(chunks) > 5:
                    c = chunks.pop(0)
                    f.write(c)
                    total += len(c)
                    del c

            if error:
                errors += 1
                count += 1
                xbmc.sleep(sleep * 1000)

            if (resumable and errors > 0) or errors >= 10:
                if (not resumable and resume >= 50) or resume >= 500:
                    # Give up!
                    return False

                resume += 1
                errors = 0
                if resumable:
                    chunks = []
                    # create new response
                    resp = getResponse(url, headers, total)
                else:
                    # use existing response
                    pass

    def clean_filename(s):
        if not s:
            return ''
        badchars = '\\/:*?\"<>|\''
        for c in badchars:
            s = s.replace(c, '')
        return s.strip()

    download_path = addon.getSetting('download_path')
    if download_path == '':
        try:
            download_path = dialog.browse(0, i18n('dnld_path'), "", "", False, False)
            addon.setSetting(id='download_path', value=download_path)
            if not xbmcvfs.exists(download_path):
                xbmcvfs.mkdir(download_path)
        except:
            pass
    if download_path != '':
        dp = xbmcgui.DialogProgress()
        name = re.sub(r'\[COLOR.+?\/COLOR\]', '', name).strip()
        dp.create(i18n('cum_dnld'), name[:50])
        tmp_file = tempfile.mktemp(dir=download_path, suffix=".mp4")
        tmp_file = xbmc.makeLegalFilename(tmp_file) if PY2 else xbmcvfs.makeLegalFilename(tmp_file)
        start = time.perf_counter() if PY3 else time.clock()
        try:
            downloaded = doDownload(url, tmp_file, dp, name)
            if downloaded:
                if PY2:
                    vidfile = xbmc.makeLegalFilename(download_path + clean_filename(name) + ".mp4")
                else:
                    vidfile = xbmcvfs.makeLegalFilename(download_path + clean_filename(name) + ".mp4")
                try:
                    xbmcvfs.rename(tmp_file, vidfile)
                    return vidfile
                except:
                    return tmp_file
            else:
                raise StopDownloading(i18n('stop_dnld'))
        except:
            while xbmcvfs.exists(tmp_file):
                try:
                    xbmcvfs.delete(tmp_file)
                    break
                except:
                    pass


def notify(header=None, msg='', duration=5000, icon=None):
    if header is None:
        header = 'Cumination'
    if icon is None:
        icon = cuminationicon
    elif icon == 'thumb':
        icon = xbmc.getInfoImage("ListItem.Thumb")
    elif not icon.startswith('http'):
        icon = cuminationicon
    dialog.notification(header, msg, icon, duration, False)


@url_dispatcher.register()
def setview():
    skin = xbmc.getSkinDir().lower()
    win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    viewtype = str(win.getFocusId())
    addon.setSetting('setview', ';'.join([skin, viewtype]))
    addon.setSetting('customview', 'true')
    viewName = xbmc.getInfoLabel('Container.Viewmode')
    notify(i18n('dflt_view_set'), '{0} {1}'.format(i18n('dflt_set'), viewName))
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def refresh():
    xbmc.executebuiltin('Container.Refresh')


def playvid(videourl, name, download=None, subtitle=None):
    if download == 1:
        downloadVideo(videourl, name)
    else:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
        subject = xbmc.getInfoLabel("ListItem.Plot")
        listitem = xbmcgui.ListItem(name)
        listitem.setArt({'thumb': iconimage, 'icon': "DefaultVideo.png", 'poster': iconimage})
        if KODIVER > 19.8:
            vtag = listitem.getVideoInfoTag()
            vtag.setTitle(name)
            vtag.setGenres(['Porn'])
            vtag.setPlot(subject)
            vtag.setPlotOutline(subject)
        else:
            listitem.setInfo('video', {'Title': name, 'Genre': 'Porn', 'plot': subject, 'plotoutline': subject})

        videourl, listitem = inputstream_check(videourl, listitem)

        if subtitle:
            listitem.setSubtitles([subtitle])

        if int(sys.argv[1]) == -1:
            xbmc.Player().play(videourl, listitem)
        else:
            listitem.setPath(str(videourl))
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)


def inputstream_check(url, listitem):
    supported_endings = [[".hls", 'application/vnd.apple.mpegstream_url'],
                         [".mpd", 'application/dash+xml'],
                         [".ism", 'application/vnd.ms-sstr+xml']]

    m3u8_use_ia = True if addon.getSetting("m3u8_use_ia") == "true" else False
    if m3u8_use_ia:
        supported_endings.append([".m3u8", 'application/x-mpegURL'])
    adaptive_type = None
    for ending in supported_endings:
        if ending[0] in url:
            if ending[0] == ".m3u8":
                adaptive_type = "hls"
            else:
                adaptive_type = ending[0][1:]
            mime_type = ending[1]

    if adaptive_type:
        from inputstreamhelper import Helper
        is_helper = Helper(adaptive_type)
        if not is_helper.check_inputstream():
            return url, listitem

        IA = 'inputstream' if six.PY3 else 'inputstreamaddon'
        listitem.setProperty(IA, 'inputstream.adaptive')

        if '|' in url:
            url, strhdr = url.split('|')
            listitem.setProperty('inputstream.adaptive.stream_headers', strhdr)

        listitem.setProperty('inputstream.adaptive.manifest_type', adaptive_type)
        listitem.setMimeType(mime_type)
        listitem.setContentLookup(False)

    return url, listitem


@url_dispatcher.register()
def PlayStream(name, url):
    item = xbmcgui.ListItem(name, path=url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    return


def getHtml(url, referer='', headers=None, NoCookie=None, data=None, error='return', ignoreCertificateErrors=False):
    return cache.cacheFunction(_getHtml, url, referer, headers, NoCookie, data, error, ignoreCertificateErrors)


def _getHtml(url, referer='', headers=None, NoCookie=None, data=None, error='return', ignoreCertificateErrors=False):
    url = urllib_parse.quote(url, r':/%?+&=')

    if data:
        if type(data) != str:
            data = urllib_parse.urlencode(data)
        data = data if PY2 else six.b(data)
    if headers is None:
        headers = base_hdrs
    if 'User-Agent' not in headers.keys():
        headers.update({'User-Agent': USER_AGENT})

    req = Request(url, data, headers)
    if len(referer) > 1:
        req.add_header('Referer', referer)
    if data:
        req.add_header('Content-Length', len(data))
    try:
        if ignoreCertificateErrors:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urlopen(req, timeout=30, context=ctx)
        else:
            response = urlopen(req, timeout=30)
    except urllib_error.HTTPError as e:
        if error is True:
            response = e
        else:
            if e.info().get('Content-Encoding', '').lower() == 'gzip':
                buf = six.BytesIO(e.read())
                f = gzip.GzipFile(fileobj=buf)
                result = f.read()
                f.close()
            else:
                result = e.read()
            result = result.decode('latin-1', errors='ignore') if PY3 else result.encode('utf-8')
            if e.code == 503 and 'cf-browser-verification' in result:
                result = cloudflare.solve(url, cj, USER_AGENT)
            elif e.code == 403 and 'cf-alert-error' in result:
                # Drop to TLS1.2 and try again
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                handle = [urllib_request.HTTPSHandler(context=ctx)]
                opener = urllib_request.build_opener(*handle)
                try:
                    response = opener.open(req, timeout=30)
                except urllib_error.HTTPError as e:
                    if e.info().get('Content-Encoding', '').lower() == 'gzip':
                        buf = six.BytesIO(e.read())
                        f = gzip.GzipFile(fileobj=buf)
                        result = f.read()
                        f.close()
                    else:
                        result = e.read()
                    if e.code == 403 and 'cf-alert-error' in result:
                        # Drop to TLS1.1 and try again
                        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
                        handle = [urllib_request.HTTPSHandler(context=ctx)]
                        opener = urllib_request.build_opener(*handle)
                        try:
                            response = opener.open(req, timeout=30)
                        except:
                            notify(i18n('oh_oh'), i18n('site_down'))
                            if 'return' in error:
                                # Give up
                                return ''
                            else:
                                raise
            elif 400 < e.code < 500:
                if not e.code == 403:
                    notify(i18n('oh_oh'), i18n('not_exist'))
                raise
            else:
                notify(i18n('oh_oh'), i18n('site_down'))
                raise
    except urllib_error.URLError as e:
        if 'return' in error:
            notify(i18n('oh_oh'), i18n('slow_site'))
            xbmc.log(str(e), xbmc.LOGDEBUG)
            return ''
        elif 'raise' in error:
            raise
    except Exception as e:
        if 'SSL23_GET_SERVER_HELLO' in str(e):
            notify(i18n('oh_oh'), i18n('python_old'))
            raise
        else:
            notify(i18n('oh_oh'), i18n('site_down'))
            raise
        return None

    cencoding = response.info().get('Content-Encoding', '')
    if cencoding.lower() == 'gzip':
        buf = six.BytesIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        result = f.read()
        f.close()
    else:
        result = response.read()

    if cencoding.lower() == 'br':
        result = decompress(result)

    encoding = None
    content_type = response.headers.get('content-type', '')
    if 'charset=' in content_type:
        encoding = content_type.split('charset=')[-1]

    if encoding is None:
        epattern = r'<meta\s+http-equiv="Content-Type"\s+content="(?:.+?);\s+charset=(.+?)"'
        epattern = epattern.encode('utf8') if PY3 else epattern
        r = re.search(epattern, result, re.IGNORECASE)
        if r:
            encoding = r.group(1).decode('utf8') if PY3 else r.group(1)
        else:
            epattern = r'''<meta\s+charset=["']?([^"'>]+)'''
            epattern = epattern.encode('utf8') if PY3 else epattern
            r = re.search(epattern, result, re.IGNORECASE)
            if r:
                encoding = r.group(1).decode('utf8') if PY3 else r.group(1)

    if encoding is not None:
        result = result.decode(encoding.lower(), errors='ignore')
        result = result.encode('utf8') if PY2 else result
    else:
        result = result.decode('latin-1', errors='ignore') if PY3 else result.encode('utf-8')

    if not NoCookie:
        # Cope with problematic timestamp values on RPi on OpenElec 4.2.1
        try:
            cj.save(cookiePath, ignore_discard=True)
        except:
            pass
    response.close()

    if 'sucuri_cloudproxy_js' in result:
        headers['Cookie'] = get_sucuri_cookie(result)
        result = getHtml(url, referer, headers=headers)
    return result


def get_sucuri_cookie(html):
    s = re.compile(r"S\s*=\s*'([^']+)").findall(html)[0]
    s = base64.b64decode(s.encode('ascii'))
    s = s.decode('latin-1').replace(' ', '')
    s = re.sub(r'String\.fromCharCode\(([^)]+)\)', r'chr(\1)', s)
    s = re.sub(r'\.slice\((\d+),(\d+)\)', r'[\1:\2]', s)
    s = re.sub(r'\.charAt\(([^)]+)\)', r'[\1]', s)
    s = re.sub(r'\.substr\((\d+),(\d+)\)', r'[\1:\1+\2]', s)
    s = re.sub(r';location.reload\(\);', '', s)
    s = re.sub(r'\n', '', s)
    s = re.sub(r'document\.cookie', 'cookie', s)
    sucuri_cookie = ''
    if ';cookie=' in s:
        s, c = s.split(';cookie=')
        exec(s)
        cookie = eval(c)
    else:
        exec(s)
    if sucuri_cookie == '':
        sucuri_cookie = cookie
    sucuri_cookie = re.compile('([^=]+)=(.*)').findall(sucuri_cookie)[0]
    sucuri_cookie = '%s=%s' % (sucuri_cookie[0], sucuri_cookie[1])
    return sucuri_cookie


def postHtml(url, form_data={}, headers={}, json_data={}, compression=True, NoCookie=None):
    return cache.cacheFunction(_postHtml, url, form_data, headers, json_data, compression, NoCookie)


def _postHtml(url, form_data={}, headers={}, json_data={}, compression=True, NoCookie=None):
    if form_data:
        form_data = urllib_parse.urlencode(form_data)
        form_data = form_data if PY2 else six.b(form_data)
        req = urllib_request.Request(url, form_data)
    elif json_data:
        json_data = json.dumps(json_data)
        json_data = json_data.encode('utf8') if PY3 else json_data
        req = urllib_request.Request(url, json_data)
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib_request.Request(url)
        req.get_method = lambda: 'POST'
    if 'User-Agent' not in headers.keys():
        req.add_header('User-Agent', USER_AGENT)
    for k, v in list(headers.items()):
        req.add_header(k, v)
    if compression:
        req.add_header('Accept-Encoding', 'gzip')

    try:
        response = urllib_request.urlopen(req)
    except urllib_error.HTTPError as e:
        if e.info().get('Content-Encoding', '').lower() == 'gzip':
            buf = six.BytesIO(e.read())
            f = gzip.GzipFile(fileobj=buf)
            result = f.read()
            f.close()
        else:
            result = e.read()

        if e.code == 503 and 'cf-browser-verification' in result:
            result = cloudflare.solve(url, cj, USER_AGENT)
        elif e.code == 403 and 'cf-alert-error' in result:
            # Drop to TLS1.2 and try again
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            handle = [urllib_request.HTTPSHandler(context=ctx)]
            opener = urllib_request.build_opener(*handle)
            try:
                response = opener.open(req, timeout=30)
            except urllib_error.HTTPError as e:
                if e.info().get('Content-Encoding', '').lower() == 'gzip':
                    buf = six.BytesIO(e.read())
                    f = gzip.GzipFile(fileobj=buf)
                    result = f.read()
                    f.close()
                else:
                    result = e.read()
                if e.code == 403 and 'cf-alert-error' in result:
                    # Drop to TLS1.1 and try again
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
                    handle = [urllib_request.HTTPSHandler(context=ctx)]
                    opener = urllib_request.build_opener(*handle)
                    try:
                        response = opener.open(req, timeout=30)
                    except:
                        notify(i18n('oh_oh'), i18n('site_down'))
                        raise
        elif 400 < e.code < 500:
            if not e.code == 403:
                notify(i18n('oh_oh'), i18n('not_exist'))
            raise
        else:
            notify(i18n('oh_oh'), i18n('site_down'))
            raise
    except urllib_error.URLError as e:
        notify(i18n('oh_oh'), i18n('slow_site'))
        xbmc.log(str(e), xbmc.LOGDEBUG)
        raise
    # except Exception as e:
    #     if 'SSL23_GET_SERVER_HELLO' in str(e):
    #         notify(i18n('oh_oh'), i18n('python_old'))
    #         raise
    #     else:
    #         notify(i18n('oh_oh'), i18n('site_down'))
    #         raise
    #     return None

    if response.info().get('Content-Encoding', '').lower() == 'gzip':
        buf = six.BytesIO(response.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()
        f.close()
    else:
        data = response.read()

    encoding = None

    content_type = response.headers.get('content-type', '')
    if 'charset=' in content_type:
        encoding = content_type.split('charset=')[-1]

    if encoding is None:
        epattern = r'<meta\s+http-equiv="Content-Type"\s+content="(?:.+?);\s+charset=(.+?)"'
        epattern = epattern.encode('utf8') if PY3 else epattern
        r = re.search(epattern, data, re.IGNORECASE)
        if r:
            encoding = r.group(1).decode('utf8') if PY3 else r.group(1)

    if encoding is not None:
        data = data.decode(encoding.lower(), errors='ignore')
        data = data.encode('utf8') if PY2 else data
    else:
        data = data.decode('ascii', errors='ignore') if PY3 else data.encode('utf8')

    if not NoCookie:
        cj.save(cookiePath, ignore_discard=True)

    response.close()
    return data


def checkUrl(url, headers={}):
    if 'User-Agent' not in headers.keys():
        headers.update({'User-Agent': USER_AGENT})
    req = Request(url, headers=headers)
    req.get_method = lambda: 'HEAD'
    try:
        response = urlopen(req, timeout=60)
        code = response.code
    except urllib_error.HTTPError as e:
        code = e.code
    return code == 200


def getHtml2(url):
    return cache.cacheFunction(_getHtml2, url)


def _getHtml2(url):
    req = Request(url)
    response = urlopen(req, timeout=60)
    data = response.read()
    response.close()
    data = data.decode('latin-1') if PY3 else data
    return data


def getVideoLink(url, referer='', headers=None, data=None):
    if not headers:
        headers = base_hdrs

    if 'User-Agent' not in headers:
        headers.update({'User-Agent': base_hdrs.get('User-Agent')})

    req2 = Request(url, data=data, headers=headers)

    if referer:
        req2.add_header('Referer', referer)

    opener = urllib_request.build_opener(NoRedirection())

    try:
        response = opener.open(req2, timeout=30)
    except urllib_error.HTTPError as e:
        response = e

    return response.headers.get('location') or url


def parse_query(query):
    toint = ['page', 'download', 'favmode', 'channel', 'section']
    q = {'mode': 'main.INDEX'}
    if query.startswith('?'):
        query = query[1:]
    queries = urllib_parse.parse_qs(query)
    for key in queries:
        if len(queries[key]) == 1:
            if key in toint:
                try:
                    q[key] = int(queries[key][0])
                except:
                    q[key] = queries[key][0]
            else:
                q[key] = queries[key][0]
        else:
            q[key] = queries[key]
    return q


def cleantext(text):
    if PY3:
        import html
        text = html.unescape(text)
    else:
        h = html_parser.HTMLParser()
        text = h.unescape(text.decode('utf8')).encode('utf8')
    text = text.replace('&amp;', '&')
    text = text.replace('&apos;', "'")
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&ndash;', '-')
    text = text.replace('&quot;', '"')
    text = text.replace('&ntilde;', '~')
    text = text.replace('&rsquo;', '\'')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&equals;', '=')
    text = text.replace('&quest;', '?')
    text = text.replace('&comma;', ',')
    text = text.replace('&period;', '.')
    text = text.replace('&colon;', ':')
    text = text.replace('&lpar;', '(')
    text = text.replace('&rpar;', ')')
    text = text.replace('&excl;', '!')
    text = text.replace('&dollar;', '$')
    text = text.replace('&num;', '#')
    text = text.replace('&ast;', '*')
    text = text.replace('&lowbar;', '_')
    text = text.replace('&lsqb;', '[')
    text = text.replace('&rsqb;', ']')
    text = text.replace('&half;', '1/2')
    text = text.replace('&DiacriticalTilde;', '~')
    text = text.replace('&OpenCurlyDoubleQuote;', '"')
    text = text.replace('&CloseCurlyDoubleQuote;', '"')
    return text.strip()


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def get_vidhost(url):
    """
    Trim the url to get the video hoster
    :return vidhost
    """
    parts = url.split('/')[2].split('.')
    vidhost = '{}.{}'.format(parts[-2], parts[-1])
    return vidhost


def get_language(lang_code):
    languages = {
        "aa": "Afar", "ab": "Abkhazian", "af": "Afrikaans", "am": "Amharic", "ar": "Arabic", "as": "Assamese", "ay": "Aymara",
        "az": "Azerbaijani", "ba": "Bashkir", "be": "Byelorussian", "bg": "Bulgarian", "bh": "Bihari", "bi": "Bislama", "bn": "Bengali",
        "bo": "Tibetan", "br": "Breton", "ca": "Catalan", "co": "Corsican", "cs": "Czech", "cy": "Welch", "da": "Danish", "de": "German",
        "dz": "Bhutani", "el": "Greek", "en": "English", "eo": "Esperanto", "es": "Spanish", "et": "Estonian", "eu": "Basque",
        "fa": "Persian", "fi": "Finnish", "fj": "Fiji", "fo": "Faeroese", "fr": "French", "fy": "Frisian", "ga": "Irish",
        "gd": "Scots Gaelic", "gl": "Galician", "gn": "Guarani", "gu": "Gujarati", "ha": "Hausa", "hi": "Hindi", "he": "Hebrew",
        "hr": "Croatian", "hu": "Hungarian", "hy": "Armenian", "ia": "Interlingua", "id": "Indonesian", "ie": "Interlingue",
        "ik": "Inupiak", "in": "former Indonesian", "is": "Icelandic", "it": "Italian", "iu": "Inuktitut (Eskimo)", "iw": "former Hebrew",
        "ja": "Japanese", "ji": "former Yiddish", "jw": "Javanese", "ka": "Georgian", "kk": "Kazakh", "kl": "Greenlandic", "km": "Cambodian",
        "kn": "Kannada", "ko": "Korean", "ks": "Kashmiri", "ku": "Kurdish", "ky": "Kirghiz", "la": "Latin", "ln": "Lingala", "lo": "Laothian",
        "lt": "Lithuanian", "lv": "Latvian,  Lettish", "mg": "Malagasy", "mi": "Maori", "mk": "Macedonian", "ml": "Malayalam", "mn": "Mongolian",
        "mo": "Moldavian", "mr": "Marathi", "ms": "Malay", "mt": "Maltese", "my": "Burmese", "na": "Nauru", "ne": "Nepali", "nl": "Dutch",
        "no": "Norwegian", "oc": "Occitan", "om": "(Afan) Oromo", "or": "Oriya", "pa": "Punjabi", "pl": "Polish", "ps": "Pashto,  Pushto",
        "pt": "Portuguese", "qu": "Quechua", "rm": "Rhaeto-Romance", "rn": "Kirundi", "ro": "Romanian", "ru": "Russian", "rw": "Kinyarwanda",
        "sa": "Sanskrit", "sd": "Sindhi", "sg": "Sangro", "sh": "Serbo-Croatian", "si": "Singhalese", "sk": "Slovak", "sl": "Slovenian",
        "sm": "Samoan", "sn": "Shona", "so": "Somali", "sq": "Albanian", "sr": "Serbian", "ss": "Siswati", "st": "Sesotho", "su": "Sudanese",
        "sv": "Swedish", "sw": "Swahili", "ta": "Tamil", "te": "Tegulu", "tg": "Tajik", "th": "Thai", "ti": "Tigrinya", "tk": "Turkmen",
        "tl": "Tagalog", "tn": "Setswana", "to": "Tonga", "tr": "Turkish", "ts": "Tsonga", "tt": "Tatar", "tw": "Twi", "ug": "Uigur",
        "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek", "vi": "Vietnamese", "vo": "Volapuk", "wo": "Wolof", "xh": "Xhosa", "yi": "Yiddish",
        "yo": "Yoruba", "za": "Zhuang", "zh": "Chinese", "zu": "Zulu"
    }

    return languages.get(lang_code.lower(), lang_code)


def get_country(country_code):
    countries = {
        "af": "Afghanistan", "al": "Albania", "dz": "Algeria", "as": "American Samoa", "ad": "Andorra", "ao": "Angola", "ai": "Anguilla",
        "ag": "Antigua & Barbuda", "ar": "Argentina", "am": "Armenia", "aw": "Aruba", "au": "Australia", "at": "Austria", "az": "Azerbaijan",
        "bs": "Bahamas", "bh": "Bahrain", "bd": "Bangladesh", "bb": "Barbados", "by": "Belarus", "be": "Belgium", "bz": "Belize", "bj": "Benin",
        "bm": "Bermuda", "bt": "Bhutan", "bo": "Bolivia", "ba": "Bosnia & Herzegovina", "bw": "Botswana", "bv": "Bouvet Island", "br": "Brazil",
        "bn": "Brunei Darussalam", "bg": "Bulgaria", "bf": "Burkina Faso", "bi": "Burundi", "kh": "Cambodia", "cm": "Cameroon", "ca": "Canada",
        "cv": "Cape Verde", "ky": "Cayman Islands", "cf": "Central African Republic", "td": "Chad", "cl": "Chile", "cn": "China", "co": "Colombia",
        "km": "Comoros", "cg": "Congo", "cd": "Congo,  the Democratic Republic of the", "ck": "Cook Islands", "cr": "Costa Rica", "ci": "Cote D'Ivoire",
        "hr": "Croatia", "cu": "Cuba", "cw": "Curacao", "cy": "Cyprus", "cz": "Czech Republic", "dk": "Denmark", "dj": "Djibouti", "dm": "Dominica",
        "do": "Dominican Republic", "ec": "Ecuador", "eg": "Egypt", "sv": "El Salvador", "gq": "Equatorial Guinea", "er": "Eritrea", "ee": "Estonia",
        "et": "Ethiopia", "fk": "Falkland Islands (Malvinas)", "fo": "Faroe Islands", "fj": "Fiji", "fi": "Finland", "fr": "France", "gf": "French Guiana",
        "pf": "French Polynesia", "ga": "Gabon", "gm": "Gambia", "ge": "Georgia", "de": "Germany", "gh": "Ghana", "gi": "Gibraltar", "gr": "Greece",
        "gl": "Greenland", "gd": "Grenada", "gp": "Guadeloupe", "gu": "Guam", "gt": "Guatemala", "gn": "Guinea", "gw": "Guinea-Bissau", "gy": "Guyana",
        "ht": "Haiti", "va": "Holy See (Vatican City)", "hn": "Honduras", "hk": "Hong Kong", "hu": "Hungary", "is": "Iceland", "in": "India",
        "id": "Indonesia", "ir": "Iran", "iq": "Iraq", "ie": "Ireland", "il": "Israel", "it": "Italy", "jm": "Jamaica", "jp": "Japan", "je": "Jersey",
        "jo": "Jordan", "kz": "Kazakhstan", "ke": "Kenya", "ki": "Kiribati", "kp": "Korea,  Democratic People\'s Republic of", "kr": "Korea,  Republic of",
        "kw": "Kuwait", "kg": "Kyrgyzstan", "la": "Lao", "lv": "Latvia", "lb": "Lebanon", "ls": "Lesotho", "lr": "Liberia", "ly": "Libyan Arab Jamahiriya",
        "li": "Liechtenstein", "lt": "Lithuania", "lu": "Luxembourg", "mo": "Macao", "mk": "Macedonia", "mg": "Madagascar", "mw": "Malawi", "my": "Malaysia",
        "mv": "Maldives", "ml": "Mali", "mt": "Malta", "mh": "Marshall Islands", "mq": "Martinique", "mr": "Mauritania", "mu": "Mauritius", "mx": "Mexico",
        "fm": "Micronesia", "md": "Moldova", "mc": "Monaco", "mn": "Mongolia", "me": "Montenegro", "ms": "Montserrat", "ma": "Morocco", "mz": "Mozambique",
        "mm": "Myanmar", "na": "Namibia", "nr": "Nauru", "np": "Nepal", "nl": "Netherlands", "an": "Netherlands Antilles", "nc": "New Caledonia",
        "nz": "New Zealand", "ni": "Nicaragua", "ne": "Niger", "ng": "Nigeria", "nu": "Niue", "nf": "Norfolk Island", "mp": "Northern Mariana Islands",
        "no": "Norway", "om": "Oman", "pk": "Pakistan", "pw": "Palau", "ps": "Palestine", "pa": "Panama", "pg": "Papua New Guinea", "py": "Paraguay",
        "pe": "Peru", "ph": "Philippines", "pn": "Pitcairn", "pl": "Poland", "pt": "Portugal", "pr": "Puerto Rico", "qa": "Qatar", "re": "Reunion",
        "ro": "Romania", "ru": "Russian Federation", "rw": "Rwanda", "bl": "Saint Barths", "sh": "Saint Helena", "kn": "Saint Kitts and Nevis",
        "lc": "Saint Lucia", "pm": "Saint Pierre & Miquelon", "vc": "Saint Vincent & the Grenadines", "ws": "Samoa", "sm": "San Marino",
        "st": "Sao Tome & Principe", "sa": "Saudi Arabia", "sn": "Senegal", "rs": "Serbia", "sc": "Seychelles", "sl": "Sierra Leone", "sg": "Singapore",
        "sk": "Slovakia", "si": "Slovenia", "sb": "Solomon Islands", "so": "Somalia", "za": "South Africa", "es": "Spain", "lk": "Sri Lanka", "sd": "Sudan",
        "sr": "Suriname", "sj": "Svalbard & Jan Mayen", "sz": "Swaziland", "se": "Sweden", "ch": "Switzerland", "sy": "Syrian Arab Republic", "tw": "Taiwan",
        "tj": "Tajikistan", "tz": "Tanzania", "th": "Thailand", "tl": "Timor-Leste", "tg": "Togo", "tk": "Tokelau", "to": "Tonga", "tt": "Trinidad & Tobago",
        "tn": "Tunisia", "tr": "Turkey", "tm": "Turkmenistan", "tc": "Turks & Caicos", "tv": "Tuvalu", "ug": "Uganda", "ua": "Ukraine", "ae": "United Arab Emirates",
        "gb": "United Kingdom", "us": "United States", "um": "United States Minor Outlying Islands", "uy": "Uruguay", "uz": "Uzbekistan", "vu": "Vanuatu",
        "ve": "Venezuela", "vn": "Viet Nam", "vg": "Virgin Islands,  British", "vi": "Virgin Islands,  U.S.", "wf": "Wallis & Futuna", "eh": "Western Sahara",
        "ye": "Yemen", "zm": "Zambia", "zw": "Zimbabwe"
    }

    return countries.get(country_code.lower(), country_code)


def _get_keyboard(default="", heading="", hidden=False):
    """ shows a keyboard and returns a value """
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText().encode("utf8") if PY2 else keyboard.getText()
    return default


def streamdefence(html):
    if '<iframe' not in html:
        decoded = html
        for _ in range(2):
            match = re.findall(r'\("([^"]+)', decoded, re.DOTALL | re.IGNORECASE)[0]
            decoded = base64.b64decode(match.encode('ascii'))
            decoded = base64.b64decode(decoded).decode('ascii')
        match = re.search(r'var\s[^"=]+="([^"]+)', decoded)
        if match:
            decoded = base64.b64decode(match.group(1).encode('ascii')).decode('ascii')
            return decoded
    return html


@url_dispatcher.register()
def setSorted():
    addon.setSetting('keywords_sorted', 'true')
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def setUnsorted():
    addon.setSetting('keywords_sorted', 'false')
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def oneSearch(url, page, channel):
    vq = _get_keyboard(heading=i18n('srch_for'))
    if not vq:
        return False, 0
    keyword = urllib_parse.quote_plus(vq)
    searchcmd = (
        sys.argv[0]
        + "?url=" + urllib_parse.quote_plus(url)
        + "&mode=" + str(channel)
        + "&keyword=" + keyword
    )
    xbmc.executebuiltin('Container.Update(' + searchcmd + ')')


@url_dispatcher.register()
def newSearch(url=None, channel=None, keyword=None):
    vq = _get_keyboard(default=keyword, heading=i18n('srch_for'))
    if not vq:
        return False, 0
    if not keyword:
        addKeyword(vq)
    elif keyword != vq:
        updateKeyword(keyword, vq)
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def clearSearch():
    delallKeyword()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def alphabeticalSearch(url, channel, keyword=None):
    if keyword:
        searchDir(url, channel, page=None, alphabet=keyword)
    else:
        key_list = keys()
        for c, count in sorted(key_list.items()):
            name = '[COLOR deeppink]{}[/COLOR] [COLOR lightpink]({})[/COLOR]'.format(c, count)
            addDir(name, url, "utils.alphabeticalSearch", cum_image('cum-search.png'), '', channel, keyword=c)
        eod()


def addKeyword(keyword):
    if check_if_keyword_exists(keyword):
        notify(i18n('error'), i18n('keyword_exists'))
        return
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO keywords VALUES (?)", (urllib_parse.quote_plus(keyword),))
    conn.commit()
    conn.close()


def updateKeyword(keyword, new_keyword):
    if check_if_keyword_exists(new_keyword):
        notify(i18n('error'), i18n('keyword_exists'))
        return
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE keywords SET keyword='{}' WHERE keyword='{}'".format(urllib_parse.quote_plus(new_keyword), urllib_parse.quote_plus(keyword)))
    conn.commit()
    conn.close()


@url_dispatcher.register()
def delallKeyword():
    yes = dialog.yesno(i18n('warning'), '{0}[CR]{1}?'.format(i18n('clear_kwds'), i18n('continue')))  # , nolabel='No', yeslabel='Yes')
    if yes:
        conn = sqlite3.connect(favoritesdb)
        c = conn.cursor()
        c.execute("DELETE FROM keywords;")
        conn.commit()
        conn.close()


@url_dispatcher.register()
def delKeyword(keyword):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM keywords WHERE keyword = ?", (urllib_parse.quote_plus(keyword),))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def backup_keywords():
    path = dialog.browseSingle(0, i18n('bkup_dir'), '')
    progress.create(i18n('backing_up'), i18n('init'))
    if not path:
        return
    import datetime
    import json
    progress.update(25, i18n('read_db'))
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM keywords")
    keywords = [{"keyword": keyword} for (keyword,) in c.fetchall()]
    if not keywords:
        progress.close()
        notify(i18n('words_empty'), i18n('no_words'))
        return
    conn.close()
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_content = {"meta": {"type": "cumination-keywords", "version": 1, "datetime": time}, "data": keywords}
    if progress.iscanceled():
        progress.close()
        return
    progress.update(75, i18n('write_bkup'))
    filename = "cumination-keywords_" + time + '.bak'
    compressbackup = True if addon.getSetting("compressbackup") == "true" else False
    if compressbackup:
        import gzip
        try:
            if PY3:
                with gzip.open(path + filename, "wt", encoding="utf-8") as fav_file:
                    json.dump(backup_content, fav_file)
            else:
                with gzip.open(path + filename, "wb") as fav_file:
                    json.dump(backup_content, fav_file)
        except IOError:
            progress.close()
            notify(i18n('invalid_path'), i18n('write_permission'))
            return
    else:
        try:
            if PY3:
                with gzip.open(path + filename, "wt", encoding="utf-8") as fav_file:
                    json.dump(backup_content, fav_file)
            else:
                with gzip.open(path + filename, "wb") as fav_file:
                    json.dump(backup_content, fav_file)
        except IOError:
            progress.close()
            notify(i18n('invalid_path'), i18n('write_permission'))
            return
    progress.close()
    dialog.ok(i18n('bkup_complete'), "{0} {1}".format(i18n('bkup_file'), path + filename))


def check_if_keyword_exists(keyword):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM keywords WHERE keyword = ?", (urllib_parse.quote_plus(keyword),))
    row = c.fetchone()
    conn.close()
    if row:
        return True
    return False


@url_dispatcher.register()
def restore_keywords():
    path = dialog.browseSingle(1, i18n('slct_file'), '')
    if not path:
        return
    import json
    compressbackup = True if addon.getSetting("compressbackup") == "true" else False
    if compressbackup:
        import gzip
        try:
            if PY3:
                with gzip.open(path, "rt", encoding="utf-8") as fav_file:
                    backup_content = json.load(fav_file)
            else:
                with gzip.open(path, "rb") as fav_file:
                    backup_content = json.load(fav_file)

        except (ValueError, IOError):
            notify(i18n('error'), i18n('invalid_bkup'))
            return
        if not backup_content["meta"]["type"] in ("cumination-keywords", "uwc-keywords"):
            notify(i18n('error'), i18n('invalid_bkup'))
            return
    else:
        try:
            if PY3:
                with gzip.open(path, "rt", encoding="utf-8") as fav_file:
                    backup_content = json.load(fav_file)
            else:
                with gzip.open(path, "rb") as fav_file:
                    backup_content = json.load(fav_file)

        except (ValueError, IOError):
            notify(i18n('error'), i18n('invalid_bkup'))
            return
        if not backup_content["meta"]["type"] in ("cumination-keywords", "uwc-keywords"):
            notify(i18n('error'), i18n('invalid_bkup'))
            return
    keywords = backup_content["data"]
    if not keywords:
        notify(i18n('error'), i18n('empty_bkup'))
    added = 0
    skipped = 0
    for keyword in keywords:
        keyw = keyword['keyword']
        if check_if_keyword_exists(keyw):
            skipped += 1
        else:
            addKeyword(keyw)
            added += 1
    xbmc.executebuiltin('Container.Refresh')
    dialog.ok(i18n('rstr_cmpl'), "{0}[CR]{1}: {2}[CR]{3}: {4}".format(i18n('rstr_msg'), i18n('added'), added, i18n('skipped'), skipped))


@url_dispatcher.register()
def openSettings():
    addon.openSettings()


def textBox(heading, announce):
    class TextBox():

        def __init__(self, *args, **kwargs):
            self.WINDOW = 10147
            self.CONTROL_LABEL = 1
            self.CONTROL_TEXTBOX = 5
            xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW, ))
            self.win = xbmcgui.Window(self.WINDOW)
            xbmc.sleep(500)
            self.setControls()

        def setControls(self):
            self.win.getControl(self.CONTROL_LABEL).setLabel(heading)
            try:
                f = open(announce)
                text = f.read()
            except:
                text = announce
            self.win.getControl(self.CONTROL_TEXTBOX).setText(str(text))
            return

    TextBox()
    while xbmc.getCondVisibility('Window.IsVisible(10147)'):
        xbmc.sleep(500)


def selector(dialog_name, select_from, setting_valid=False, sort_by=None, reverse=False, show_on_one=False):
    """
    Shows a dialog where the user can choose from the values provided
    Returns the value of the selected key, or None if no selection was made

    Usage:
        dialog_name = title of the dialog shown
        select_from = a list or a dictionary which contains the options

        optional arguments
        setting_valid (False) = sets if the passed addon setting id should be considered
                         if the addon setting is enabled, the dialog won't be shown and the first element
                         will be selected automatically
        sort_by (None) = in case of dictionaries the keys will be sorted according this value
                  in case of a list, the list will be ordered
        reverse (False) = sets if order should be reversed
    """
    if isinstance(select_from, dict):
        keys = sorted(list(select_from.keys()), key=sort_by, reverse=reverse)
        values = [select_from[x] for x in keys]
    else:
        keys = sorted(select_from, key=sort_by, reverse=reverse)
        values = None
    if not keys:
        return None
    if (setting_valid and int(addon.getSetting(setting_valid)) != 4) or (len(keys) == 1 and not show_on_one):
        selected = 0
    else:
        selected = dialog.select(dialog_name, keys)
    if selected == -1:
        return None
    return values[selected] if values else keys[selected]


def prefquality(video_list, sort_by=None, reverse=False):
    maxquality = int(addon.getSetting('qualityask'))
    if maxquality == 4:
        return selector(i18n('pick_qual'), video_list, sort_by=sort_by, reverse=reverse)

    vidurl = None
    if isinstance(video_list, dict):
        qualities = [2160, 1080, 720, 576]
        quality = qualities[maxquality]
        for key in video_list.copy():
            if key.lower().endswith('p60'):
                video_list[key.replace('p60', '')] = video_list[key]
                video_list.pop(key)
            else:
                if key.lower() == '4k':
                    video_list['2160'] = video_list[key]
                    video_list.pop(key)

        video_list = [(int(''.join([y for y in key if y.isdigit()])), value) for key, value in list(video_list.items())]
        video_list = sorted(video_list, reverse=True)

        for video in video_list:
            if quality >= video[0]:
                vidurl = video[1]
                break
            else:
                if str(quality) in str(video[0]):
                    vidurl = video[1]
                    break
        if not vidurl:
            vidurl = video_list[-1][1]
    else:
        keys = sorted(video_list, key=sort_by, reverse=reverse)
        if not keys:
            return None
        vidurl = keys[0]

    return vidurl


class VideoPlayer():
    def __init__(self, name, download=False, regex=r'''(?:src|SRC|href|HREF)=\s*["']([^'"]+)''', direct_regex="""<source.*?src=(?:"|')([^"']+)[^>]+>"""):
        self.regex = regex
        self.direct_regex = direct_regex
        self.name = name
        self.download = download
        self.progress = progress
        self.progress.create(i18n('plyng_vid'), "[CR]{0}[CR]".format(i18n('srch_vid')))

        import resolveurl
        self.resolveurl = resolveurl
        xxx_plugins_path = 'special://home/addons/script.module.resolveurl.xxx/resources/plugins/'
        if xbmcvfs.exists(xxx_plugins_path):
            self.resolveurl.add_plugin_dirs(TRANSLATEPATH(xxx_plugins_path))

    def _cancellable(f):
        @wraps(f)
        def wrapped(inst, *args, **kwargs):
            if inst.progress.iscanceled():
                inst.progress.close()
                return
            return f(inst, *args, **kwargs)
        return wrapped

    @_cancellable
    def _clean_urls(self, url_list):
        filtered_words = ['google']
        filtered_ends = ['.js', '.css', '/premium.html', '.jpg', '.gif', '.png', '.ico']
        added = set()
        new_list = []
        for source in url_list:
            to_break = False
            if source._url in added or not source:
                continue
            for word in filtered_words:
                if word in source._url or to_break:
                    to_break = True
                    break
            for end in filtered_ends:
                if source._url.endswith(end) or to_break:
                    to_break = True
                    break
            else:
                source.title = source._domain.split('.')[0]
                added.add(source._url)
                new_list.append(source)
        return new_list

    def play_from_site_link(self, url, referrer=''):
        self.progress.update(25, "[CR]{0}[CR]".format(i18n('load_vpage')))
        html = getHtml(url, referrer)
        self.play_from_html(html, url)

    @_cancellable
    def play_from_html(self, html, url=None):
        self.progress.update(40, "[CR]{0}[CR]".format(i18n('srch_host')))
        solved_suburls = self._check_suburls(html, url)
        self.progress.update(60, "[CR]{0}[CR]".format(i18n('srch_host')))
        direct_links = None
        if self.direct_regex:
            direct_links = re.compile(self.direct_regex, re.DOTALL | re.IGNORECASE).findall(html)
            if direct_links:
                selected = urllib_parse.urljoin(url, direct_links[0]) if direct_links[0].startswith('/') else direct_links[0]
                self.progress.update(50, "[CR]{0}[CR]".format(i18n('play_dlink')))
                self.play_from_direct_link(selected)
            elif not self.regex:
                notify(i18n('oh_oh'), i18n('not_found'))
        if self.regex and not direct_links:
            scraped_sources = self.resolveurl.scrape_supported(html, self.regex)
            scraped_sources = scraped_sources if scraped_sources else []
            scraped_sources.extend(solved_suburls)
            self.play_from_link_list(scraped_sources)
        if not self.direct_regex and not self.regex:
            raise ValueError(i18n('no_regex'))

    @_cancellable
    def play_from_link_list(self, links):
        use_universal = True if addon.getSetting("universal_resolvers") == "true" else False
        sources = self._clean_urls([self.resolveurl.HostedMediaFile(x, title=x.split('/')[2], include_universal=use_universal) for x in links])
        if not sources:
            notify(i18n('oh_oh'), i18n('not_found'))
            return
        self._select_source(sources)

    @_cancellable
    def _select_source(self, sources):
        if not len(sources) > 1 or addon.getSetting("dontask") == "true":
            source = sources[0]
        else:
            source = self.resolveurl.choose_source(sources)
        if source:
            self.play_from_link_to_resolve(source)

    @_cancellable
    def play_from_link_to_resolve(self, source):
        if isinstance(source, six.string_types):
            self.play_from_link_list([source])
            return
        self.progress.update(80, "[CR]{0}[CR]{1} {2}".format(i18n('to_smr'), i18n('play_from'), source.title))
        try:
            link = source.resolve()
        except self.resolveurl.resolver.ResolverError:
            link = False  # ResolveURL returns False in some cases when resolving fails
        if not link:
            notify(i18n('rslv_fail'), '{0} {1}'.format(source.title, i18n('not_rslv')))
        else:
            playvid(link, self.name, self.download)

    @_cancellable
    def play_from_direct_link(self, direct_link):
        self.progress.update(90, "[CR]{0}[CR]".format(i18n('play_dlink')))
        playvid(direct_link, self.name, self.download)

    @_cancellable
    def _check_suburls(self, html, referrer_url):
        sdurl = re.compile(r'''streamdefence\.com/view.php\?ref=([^"']+)''', re.DOTALL | re.IGNORECASE).findall(html)
        sdurl_world = re.compile(r'''.strdef\.world/([^"']+)''', re.DOTALL | re.IGNORECASE).findall(html)
        fcurl = re.compile(r'filecrypt\.cc/Container/([^\.]+)\.html', re.DOTALL | re.IGNORECASE).findall(html)
        shortixurl = re.compile(r'1155xmv\.com/\?u=(\w+)', re.DOTALL | re.IGNORECASE).findall(html)
        klurl = re.compile(r'(https://www.keeplinks.org/[^/]+/[0-9a-fA-f]+)', re.DOTALL | re.IGNORECASE).findall(html)
        links = []
        if sdurl or sdurl_world or fcurl or shortixurl or klurl:
            self.progress.update(50, "[CR]{0}[CR]".format(i18n('fnd_sbsite')))
        if sdurl:
            links.extend(self._solve_streamdefence(sdurl, referrer_url, False))
        elif sdurl_world:
            links.extend(self._solve_streamdefence(sdurl_world, referrer_url, True))
        elif fcurl:
            links.extend(self._solve_filecrypt(fcurl, referrer_url))
        elif shortixurl:
            links.extend(self._solve_shortix(shortixurl, referrer_url))
        elif klurl:
            links.extend(self._solve_keeplinks(klurl, referrer_url))
        return links

    @_cancellable
    def _solve_streamdefence(self, sdurls, url, world=False):
        self.progress.update(55, "[CR]{0}[CR]".format(i18n('load_strdfn')))
        sdpages = ''
        for sd_url in sdurls:
            if not world:
                sdurl = 'http://www.streamdefence.com/view.php?ref=' + sd_url
            else:
                sdurl = 'https://www.strdef.world/' + sd_url
            sdsrc = getHtml(sdurl, url if url else sdurl)
            sdpage = streamdefence(sdsrc)
            sdpages += sdpage
        sources = set(re.compile(r'<iframe.+?src="([^"]+)', re.DOTALL | re.IGNORECASE).findall(sdpages))
        return sources

    @_cancellable
    def _solve_filecrypt(self, fc_urls, url):
        self.progress.update(55, "[CR]{0}[CR]".format(i18n('load_fcrypt')))
        sites = set()
        for fc_url in fc_urls:
            fcurl = 'http://filecrypt.cc/Container/' + fc_url + ".html"
            fcsrc = getHtml(fcurl, url if url else fcurl, base_hdrs)
            fcmatch = re.compile(r"openLink.?'([\w\-]*)',", re.DOTALL | re.IGNORECASE).findall(fcsrc)
            for fclink in fcmatch:
                fcpage = "http://filecrypt.cc/Link/" + fclink + ".html"
                fcpagesrc = getHtml(fcpage, fcurl)
                fclink2 = re.search('''top.location.href='([^']+)''', fcpagesrc)
                if fclink2:
                    try:
                        fcurl2 = getVideoLink(fclink2.group(1), fcpage)
                        sites.add(fcurl2)
                    except:
                        pass
        return sites

    @_cancellable
    def _solve_shortix(self, shortixurls, url):
        self.progress.update(55, "[CR]{0}[CR]".format(i18n('load_shortix')))
        sources = set()
        for shortix in shortixurls:
            shortixurl = 'https://1155xmv.com/?u=' + shortix
            shortixsrc = getHtml(shortixurl, url if url else shortixurl)
            sources.add(re.compile('src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(shortixsrc)[0])
        return sources

    @_cancellable
    def _solve_keeplinks(self, klurls, url):
        self.progress.update(55, "[CR]{0}[CR]".format(i18n('load_kl')))
        sources = []
        klurls = set(klurls)
        for klurl in klurls:
            headers = {'Cookie': 'flag[{0}]=1'.format(klurl.split('/')[-1])}
            klsrc = getHtml(klurl, klurl, headers=headers)
            srcs = re.compile('class="numlive.+?href="([^"\r]+)', re.DOTALL | re.IGNORECASE).findall(klsrc)
            sources.extend(srcs)
        return sources


def showimage(url):
    xbmc.executebuiltin('ShowPicture({0})'.format(url))


def playvideo(videosource, name, download=None, url=None, regex=r'''(?:src|SRC|href|HREF)=\s*["']([^'"]+)'''):
    """Deprecated function, use VideoPlayer class.
    Exists for compatiblity with old site plug-ins."""
    vp = VideoPlayer(name, download, regex)
    vp.play_from_html(videosource)


def PLAYVIDEO(url, name, download=None, regex=r'''(?:src|SRC|href|HREF)=\s*["']([^'"]+)'''):
    """Deprecated function, use VideoPlayer class.
    Exists for compatiblity with old site plug-ins."""
    vp = VideoPlayer(name, download, regex)
    vp.play_from_site_link(url, url)


def next_page(site, list_mode, html, re_npurl, re_npnr=None, re_lpnr=None, videos_per_page=None, contextm=None, baseurl=None):
    match = re.compile(re_npurl, re.DOTALL | re.IGNORECASE).findall(html)
    if match:
        npurl = fix_url(match[0], site.url, baseurl).replace('&amp;', '&')
        np = ''
        npnr = 0
        if re_npnr:
            match = re.compile(re_npnr, re.DOTALL | re.IGNORECASE).findall(html)
            if match:
                npnr = match[0]
                np = npnr
        lp = ''
        lpnr = 0
        if re_lpnr:
            match = re.compile(re_lpnr, re.DOTALL | re.IGNORECASE).findall(html)
            lpnr = match[0] if match else 0
            if videos_per_page:
                lpnr = int(ceil(int(lpnr) / int(videos_per_page)))
            lp = '/' + str(lpnr) if match else ''
        if np:
            np = '(' + np
            lp = lp + ')'

        cm = None
        if contextm:
            cm_page = (addon_sys + "?mode=" + str(contextm) + "&list_mode=" + list_mode + "&url=" + urllib_parse.quote_plus(npurl) + "&np=" + str(npnr) + "&lp=" + str(lpnr))
            cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('Next Page {}{}'.format(np, lp), npurl, list_mode, contextm=cm)


def fix_url(url, siteurl=None, baseurl=None):
    if siteurl:
        baseurl = baseurl if baseurl else siteurl[:-1]
        if url.startswith('//'):
            url = siteurl.split(':')[0] + ':' + url
        elif url.startswith('?'):
            url = baseurl + url
        elif url.startswith('/'):
            url = siteurl[:-1] + url
        elif '/' not in url:
            url = baseurl + url
        elif not url.startswith('http'):
            url = siteurl + url
    return url


def videos_list(site, playvid, html, delimiter, re_videopage, re_name=None, re_img=None, re_quality=None, re_duration=None, contextm=None, skip=None):
    videolist = re.split(delimiter, html)
    if videolist:
        videolist.pop(0)
        for video in videolist:
            if skip and skip in video:
                continue
            match = re.search(re_videopage, video, flags=re.DOTALL | re.IGNORECASE)
            if match:
                videopage = fix_url(match.group(1), site.url)
            else:
                continue
            name = ''
            if re_name:
                match = re.search(re_name, video, flags=re.DOTALL | re.IGNORECASE)
                if match:
                    name = re.sub(r"\\u([0-9A-Fa-f]{4})", lambda x: six.unichr(int(x.group(1), 16)), match.group(1).strip())
                    name = six.ensure_str(name)
                    name = cleantext(name)
            img = ''
            if re_img:
                match = re.search(re_img, video, flags=re.DOTALL | re.IGNORECASE)
                if match:
                    img = fix_url(match.group(1).replace('&amp;', '&'), site.url)
            quality = ''
            if re_quality:
                match = re.search(re_quality, video, flags=re.DOTALL | re.IGNORECASE)
                if match:
                    quality = match.group(1) if match.groups() else match.group(0)
            duration = ''
            if re_duration:
                match = re.search(re_duration, video, flags=re.DOTALL | re.IGNORECASE)
                if match:
                    duration = match.group(1)
            cm = ''
            if contextm:
                if isinstance(contextm, six.string_types):
                    cm_related = (addon_sys + "?mode=" + str(contextm) + "&url=" + urllib_parse.quote_plus(videopage))
                    cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]
                else:
                    cm = [(x[0], x[1].replace("&url=", "&url=" + urllib_parse.quote_plus(videopage))) for x in contextm]
            site.add_download_link(name, videopage, playvid, img, name, quality=quality, duration=duration, contextm=cm)


def _bencode(text):
    return six.ensure_str(base64.b64encode(six.ensure_binary(text)))


def _bdecode(text):
    return six.ensure_str(base64.b64decode(text))


class LookupInfo:
    def __init__(self, siteurl, url, default_mode, lookup_list):
        self.siteurl = siteurl
        self.url = url
        self.default_mode = default_mode
        self.lookup_list = lookup_list

    def url_constructor(self, url):
        # Default url_constructor - can be overridden in derived classes
        return 'http:' + url if url.startswith('//') else self.siteurl + url

    def getinfo(self):
        try:
            listhtml = getHtml(self.url)
        except:
            return None

        infodict = {}

        item_names = [item_name for item_name, _, _ in self.lookup_list]

        for item_name, pattern, mode in self.lookup_list:
            if isinstance(pattern, list):
                match = re.compile(pattern[0], re.DOTALL | re.IGNORECASE).findall(listhtml)
                if match:
                    listhtml = match[0]
                    pattern = pattern[1]

            matches = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(listhtml)

            if matches:
                for url, name in matches:
                    name = "{} - {}".format(item_name, name.strip())
                    if not mode:
                        mode = self.default_mode
                    infodict[name] = (self.url_constructor(url), mode)

        if infodict:
            selected_item = selector('Choose item', infodict, show_on_one=True)
            if not selected_item:
                return
            contexturl = (addon_sys
                          + "?mode=" + selected_item[1]
                          + "&url=" + urllib_parse.quote_plus(selected_item[0]))
            xbmc.executebuiltin('Container.Update(' + contexturl + ')')
        else:
            if len(item_names) > 1:
                item_names_str = ', '.join(item_names[:-1]) + ' or ' + item_names[-1]
            else:
                item_names_str = item_names[0]
            notify('Notify', 'No {} found for this video'.format(item_names_str))
        return


class logger:
    log_message_prefix = '[{} ({})]: '.format(
        addon.getAddonInfo('name'), addon.getAddonInfo('version'))

    @staticmethod
    def log(message, level=xbmc.LOGDEBUG):
        message = logger.log_message_prefix + str(message)
        xbmc.log(message, level)

    @staticmethod
    def info(message):
        logger.log(message, xbmc.LOGINFO if PY3 else xbmc.LOGNOTICE)

    @staticmethod
    def error(message):
        logger.log(message, xbmc.LOGERROR)

    @staticmethod
    def debug(*messages):
        for message in messages:
            logger.log(message, xbmc.LOGDEBUG)

    @staticmethod
    def warning(message):
        logger.log(message, xbmc.LOGWARNING)


@url_dispatcher.register()
def ToggleDebug():
    result = toggle_debug()
    return result

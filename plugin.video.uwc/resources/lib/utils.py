#-*- coding: utf-8 -*-

'''
    Ultimate Whitecream
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

__scriptname__ = "Ultimate Whitecream"
__author__ = "Whitecream"
__scriptid__ = "plugin.video.uwc"
__credits__ = "Whitecream, Fr33m1nd, anton40, NothingGnome, holisticdioxide"
__version__ = "1.1.64"

import urllib
import urllib2
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import cookielib
import os.path
import sys
import time
import tempfile
import sqlite3
import urlparse
import base64
from StringIO import StringIO
import gzip
import requests

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import cloudflare
from jsunpack import unpack
import random_ua
import xbmcvfs
from functools import wraps
from kvs import decryptHash


from url_dispatcher import URL_Dispatcher

url_dispatcher = URL_Dispatcher()

USER_AGENT = random_ua.get_ua()

headers = {'User-Agent': USER_AGENT,
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'gzip',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
openloadhdr = headers

addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon(id=__scriptid__)

progress = xbmcgui.DialogProgress()
dialog = xbmcgui.Dialog()

rootDir = addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = xbmc.translatePath(rootDir)
resDir = os.path.join(rootDir, 'resources')
imgDir = os.path.join(resDir, 'images')
uwcicon = xbmc.translatePath(os.path.join(rootDir, 'icon.png'))
changelog = xbmc.translatePath(os.path.join(rootDir, 'changelog.txt'))

profileDir = addon.getAddonInfo('profile')
profileDir = xbmc.translatePath(profileDir).decode("utf-8")
cookiePath = os.path.join(profileDir, 'cookies.lwp')
kodiver = xbmc.getInfoLabel("System.BuildVersion").split(".")[0]

if not os.path.exists(profileDir):
    os.makedirs(profileDir)

urlopen = urllib2.urlopen
cj = cookielib.LWPCookieJar(xbmc.translatePath(cookiePath))
Request = urllib2.Request

handlers = [urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler()]

if (2, 7, 8) < sys.version_info < (2, 7, 12):
    try:
        import ssl; ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        handlers += [urllib2.HTTPSHandler(context=ssl_context)]
    except:
        pass

if cj != None:
    if os.path.isfile(xbmc.translatePath(cookiePath)):
        try:
            cj.load()
        except:
            try:
                os.remove(xbmc.translatePath(cookiePath))
                pass
            except:
                dialog.ok('Oh oh','The Cookie file is locked, please restart Kodi')
                pass
    cookie_handler = urllib2.HTTPCookieProcessor(cj)
    handlers += [cookie_handler]

opener = urllib2.build_opener(*handlers)
opener = urllib2.install_opener(opener)

favoritesdb = os.path.join(profileDir, 'favorites.db')

def uwcimage(filename):
    img = os.path.join(imgDir, filename)
    return img

class StopDownloading(Exception):
    def __init__(self, value): self.value = value
    def __str__(self): return repr(self.value)

def downloadVideo(url, name):

    def _pbhook(downloaded, filesize, url=None, dp=None):
        try:
            percent = min((downloaded*100)/filesize, 100)
            currently_downloaded = float(downloaded) / (1024 * 1024)
            kbps_speed = int(downloaded / (time.clock() - start))
            if kbps_speed > 0:
                eta = (filesize - downloaded) / kbps_speed
            else:
                eta = 0
            kbps_speed = kbps_speed / 1024
            total = float(filesize) / (1024 * 1024)
            mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total)
            e = 'Speed: %.02f Kb/s ' % kbps_speed
            e += 'ETA: %02d:%02d' % divmod(eta, 60)
            dp.update(percent,'',mbs,e)
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

    def doDownload(url, dest, dp):
        try:
            headers = dict(urlparse.parse_qsl(url.rsplit('|', 1)[1]))
        except:
            headers = dict('')

        if 'openload' in url:
            headers = openloadhdr

        if 'spankbang.com' in url:
            url = getVideoLink(url,url)

        url = url.split('|')[0]
        file = dest.rsplit(os.sep, 1)[-1]
        resp = getResponse(url, headers, 0)

        if not resp:
            xbmcgui.Dialog().ok("Ultimate Whitecream", 'Download failed', 'No response from server')
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
            print "Download is resumable"

        if content < 1:
            xbmcgui.Dialog().ok("Ultimate Whitecream", 'Unknown filesize', 'Unable to download')
            return False

        size = 8192
        mb   = content / (1024 * 1024)

        if content < size:
            size = content

        total   = 0
        errors  = 0
        count   = 0
        resume  = 0
        sleep   = 0

        print 'Download File Size : %dMB %s ' % (mb, dest)
        f = xbmcvfs.File(dest, 'w')

        chunk  = None
        chunks = []

        while True:
            downloaded = total
            for c in chunks:
                downloaded += len(c)
            percent = min(100 * downloaded / content, 100)

            _pbhook(downloaded,content,url,dp)

            chunk = None
            error = False

            try:
                chunk  = resp.read(size)
                if not chunk:
                    if percent < 99:
                        error = True
                    else:
                        while len(chunks) > 0:
                            c = chunks.pop(0)
                            f.write(c)
                            del c

                        f.close()
                        print '%s download complete' % (dest)
                        return True

            except Exception, e:
                print str(e)
                error = True
                sleep = 10
                errno = 0

                if hasattr(e, 'errno'):
                    errno = e.errno

                if errno == 10035: # 'A non-blocking socket operation could not be completed immediately'
                    pass

                if errno == 10054: #'An existing connection was forcibly closed by the remote host'
                    errors = 10 #force resume
                    sleep  = 30

                if errno == 11001: # 'getaddrinfo failed'
                    errors = 10 #force resume
                    sleep  = 30

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
                count  += 1
                print '%d Error(s) whilst downloading %s' % (count, dest)
                xbmc.sleep(sleep*1000)

            if (resumable and errors > 0) or errors >= 10:
                if (not resumable and resume >= 50) or resume >= 500:
                    #Give up!
                    print '%s download canceled - too many error whilst downloading' % (dest)
                    return False

                resume += 1
                errors  = 0
                if resumable:
                    chunks  = []
                    #create new response
                    print 'Download resumed (%d) %s' % (resume, dest)
                    resp = getResponse(url, headers, total)
                else:
                    #use existing response
                    pass


    def clean_filename(s):
        if not s:
            return ''
        badchars = '\\/:*?\"<>|\''
        for c in badchars:
            s = s.replace(c, '')
        return s

    download_path = addon.getSetting('download_path')
    if download_path == '':
        try:
            download_path = xbmcgui.Dialog().browse(0, "Download Path", 'myprograms', '', False, False)
            addon.setSetting(id='download_path', value=download_path)
            if not os.path.exists(download_path):
                os.mkdir(download_path)
        except:
            pass
    if download_path != '':
        dp = xbmcgui.DialogProgress()
        name = name.split("[")[0]
        dp.create("Ultimate Whitecream Download",name[:50])
        tmp_file = tempfile.mktemp(dir=download_path, suffix=".mp4")
        tmp_file = xbmc.makeLegalFilename(tmp_file)
        start = time.clock()
        try:
            #urllib.urlretrieve(url,tmp_file,lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,url,dp))
            downloaded = doDownload(url, tmp_file, dp)
            if downloaded:
                vidfile = xbmc.makeLegalFilename(download_path + clean_filename(name) + ".mp4")
                try:
                  os.rename(tmp_file, vidfile)
                  return vidfile
                except:
                  return tmp_file
            else: raise StopDownloading('Stopped Downloading')
        except:
            while os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                    break
                except:
                    pass


def notify(header=None, msg='', duration=5000):
    if header is None: header = 'Ultimate Whitecream X'
    builtin = "XBMC.Notification(%s,%s, %s, %s)" % (header, msg, duration, uwcicon)
    xbmc.executebuiltin(builtin)


def kodilog(logvar):
    xbmc.log(str(logvar), xbmc.LOGNOTICE)


def playvid(videourl, name, download=None):
    if download == 1:
        downloadVideo(videourl, name)
    else:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
        listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        if '.mpd' in videourl:
            listitem.setProperty('inputstreamaddon','inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type','mpd')
        videourl += '|verifypeer=false' if '|' not in videourl else '&verifypeer=false' if 'verifypeer=false' not in videourl.lower() else ''
        if int(sys.argv[1]) == -1:
            xbmc.Player().play(videourl, listitem)
        else:
            listitem.setPath(str(videourl))
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)


def chkmultivids(videomatch):
    videolist = list(set(videomatch))
    if len(videolist) > 1:
        hashlist = []
        for idx, x in enumerate(videolist):
            hashlist.append('Video ' + str(idx + 1))
        mvideo = dialog.select('Multiple videos found', hashlist)
        if mvideo == -1:
            return
        return videolist[mvideo]
    else:
        return videomatch[0]

@url_dispatcher.register('9', ['name', 'url'])
def PlayStream(name, url):
    item = xbmcgui.ListItem(name, path = url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    return


def getHtml(url, referer='', hdr=None, NoCookie=None, data=None):
    try:
        if data:
            data = urllib.urlencode(data)
        if not hdr:
            req = Request(url, data, headers)
        else:
            req = Request(url, data, hdr)
        if len(referer) > 1:
            req.add_header('Referer', referer)
        if data:
            req.add_header('Content-Length', len(data))
        response = urlopen(req, timeout=60)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO( response.read())
            f = gzip.GzipFile(fileobj=buf)
            result = f.read()
            f.close()
        else:
            result = response.read()
        if not NoCookie:
            # Cope with problematic timestamp values on RPi on OpenElec 4.2.1
            try:
                cj.save(cookiePath)
            except:
                pass
        response.close()
    except urllib2.HTTPError as e:
        result = e.read()
        if e.code == 503 and 'cf-browser-verification' in result:
            result = cloudflare.solve(url,cj, USER_AGENT)
        else:
            raise
    except Exception as e:
        if 'SSL23_GET_SERVER_HELLO' in str(e):
            notify('Oh oh','Python version to old - update to Krypton or FTMC')
            raise
        else:
            notify('Oh oh','It looks like this website is down.')
            raise
        return None
    if 'sucuri_cloudproxy_js' in result:
        headers['Cookie'] = get_sucuri_cookie(result)
        result = getHtml(url, referer, hdr=headers)
    return result


def get_sucuri_cookie(html):
    s = re.compile("S\s*=\s*'([^']+)").findall(html)[0]
    s = base64.b64decode(s)
    s = s.replace(' ', '')
    s = re.sub('String\.fromCharCode\(([^)]+)\)', r'chr(\1)', s)
    s = re.sub('\.slice\((\d+),(\d+)\)', r'[\1:\2]', s)
    s = re.sub('\.charAt\(([^)]+)\)', r'[\1]', s)
    s = re.sub('\.substr\((\d+),(\d+)\)', r'[\1:\1+\2]', s)
    s = re.sub(';location.reload\(\);', '', s)
    s = re.sub(r'\n', '', s)
    s = re.sub(r'document\.cookie', 'cookie', s)
    sucuri_cookie = '' ; exec(s)
    sucuri_cookie = re.compile('([^=]+)=(.*)').findall(sucuri_cookie)[0]
    sucuri_cookie = '%s=%s' % (sucuri_cookie[0], sucuri_cookie[1])
    return sucuri_cookie


def postHtml(url, form_data={}, headers={}, compression=True, NoCookie=None):
    try:
        _user_agent = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 ' + \
                      '(KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1'
        req = urllib2.Request(url)
        if form_data:
            form_data = urllib.urlencode(form_data)
            req = urllib2.Request(url, form_data)
        req.add_header('User-Agent', _user_agent)
        for k, v in headers.items():
            req.add_header(k, v)
        if compression:
            req.add_header('Accept-Encoding', 'gzip')
        response = urllib2.urlopen(req)
        data = response.read()
        if not NoCookie:
            try:
                cj.save(cookiePath)
            except: pass
        response.close()
    except Exception as e:
        if 'SSL23_GET_SERVER_HELLO' in str(e):
            notify('Oh oh','Python version to old - update to Krypton or FTMC')
            raise urllib2.HTTPError()
        else:
            notify('Oh oh','It looks like this website is down.')
            raise urllib2.HTTPError()
        return None
    return data


def getHtml2(url):
    req = Request(url)
    response = urlopen(req, timeout=60)
    data = response.read()
    response.close()
    return data

def getHtml3(url):
	headok = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',}
	data = requests.get(url,headers=headok,verify=False).content
	# response = urlopen(req, timeout=60)
	# data = response.read()
	# response.close()
	return data	
def getHtml4(url):
	headok = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
		'Accept': '*/*',
		'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
		'X-Requested-With': 'XMLHttpRequest',}
	data = requests.get(url,headers=headok,verify=False).json()

	return data		

def getHtml5(url):	
	headersy = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
		'Accept': '*/*',
		'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
		'Referer': 'https://beeg.com/',
		'X-Requested-With': 'XMLHttpRequest',
		'DNT': '1',
		'Connection': 'keep-alive',
	}	
	
	sess=requests.session()
	#UA      = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'
	#sess.headers=headersy
	data=sess.get(url,headers=headersy,verify=False).content	
	
	
	
	#data = requests.get(url,headers=headersy,verify=False,timeout=160).content
	# response = urlopen(req, timeout=60)
	# data = response.read()
	# response.close()
	return data		
	
	
def getVideoLink(url, referer, hdr=None, data=None):
    if not hdr:
        req2 = Request(url, data, headers)
    else:
        req2 = Request(url, data, hdr)
    if len(referer) > 1:
        req2.add_header('Referer', referer)
    url2 = urlopen(req2).geturl()
    return url2


def parse_query(query):
    toint = ['page', 'download', 'favmode', 'channel', 'section']
    q = {'mode': '0'}
    if query.startswith('?'): query = query[1:]
    queries = urlparse.parse_qs(query)
    for key in queries:
        if len(queries[key]) == 1:
            if key in toint:
                try: q[key] = int(queries[key][0])
                except: q[key] = queries[key][0]
            else:
                q[key] = queries[key][0]
        else:
            q[key] = queries[key]
    return q


def cleantext(text):
    text = text.replace('&amp;','&')
    text = text.replace('&#8211;','-')
    text = text.replace('&ndash;','-')
    text = text.replace('&#038;','&')
    text = text.replace('&#8217;','\'')
    text = text.replace('&#8216;','\'')
    text = text.replace('&#8220;','"')
    text = text.replace('&#8221;','"')
    text = text.replace('&#8230;','...')
    text = text.replace('&quot;','"')
    text = text.replace('&#039;','`')
    text = text.replace('&ntilde;','ñ')
    text = text.replace('&rsquo;','\'')
    text = text.replace('&#133;','...')
    text = text.replace('&#40;', '(')
    text = text.replace('&#41;', ')')
    text = text.replace('&nbsp;', ' ')
    return text.strip()


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def addDownLink(name, url, mode, iconimage, desc='', stream=None, fav='add', noDownload=False):
    contextMenuItems = []
    favtext = "Remove from" if fav == 'del' else "Add to" # fav == 'add' or 'del'
    u = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&mode=" + str(mode) +
         "&name=" + urllib.quote_plus(name))
    dwnld = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&mode=" + str(mode) +
         "&download=" + str(1) +
         "&name=" + urllib.quote_plus(name))
    favorite = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&fav=" + fav +
         "&favmode=" + str(mode) +
         "&mode=" + str('900') +
         "&img=" + urllib.quote_plus(iconimage) +
         "&name=" + urllib.quote_plus(name))
    ok = True
    if not iconimage:
        iconimage = uwcicon
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setArt({'thumb': iconimage, 'icon': iconimage})
    fanart = os.path.join(rootDir, 'fanart.jpg')
    if addon.getSetting('posterfanart') == 'true':
        fanart = iconimage
        liz.setArt({'poster': iconimage})
    liz.setArt({'fanart': fanart})
    if stream:
        liz.setProperty('IsPlayable', 'true')
    if desc:
        liz.setInfo(type="Video", infoLabels={"Title": name, "plot": desc, "plotoutline": desc})
    else:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    video_streaminfo = {'codec': 'h264'}
    liz.addStreamInfo('video', video_streaminfo)
    contextMenuItems.append(('[COLOR hotpink]' + favtext + ' favorites[/COLOR]', 'xbmc.RunPlugin(' + favorite + ')'))
    if fav == 'del':
        favorite_move_to_end = (sys.argv[0] +
            "?url=" + urllib.quote_plus(url) +
            "&fav=" + 'move_to_end' +
            "&favmode=" + str(mode) +
            "&mode=" + str('900') +
            "&img=" + urllib.quote_plus(iconimage) +
            "&name=" + urllib.quote_plus(name))
        contextMenuItems.append(('[COLOR hotpink]Move favorite to end[/COLOR]', 'xbmc.RunPlugin(' + favorite_move_to_end + ')'))
    if not noDownload:
        contextMenuItems.append(('[COLOR hotpink]Download Video[/COLOR]', 'xbmc.RunPlugin(' + dwnld + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    return ok


def addDir(name, url, mode, iconimage=None, page=None, channel=None, section=None, keyword='', Folder=True):
    u = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&mode=" + str(mode) +
         "&page=" + str(page) +
         "&channel=" + str(channel) +
         "&section=" + str(section) +
         "&keyword=" + urllib.quote_plus(keyword) +
         "&name=" + urllib.quote_plus(name))
    ok = True
    if not iconimage:
        iconimage = uwcicon
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setArt({'thumb': iconimage, 'icon': iconimage})
    fanart = os.path.join(rootDir, 'fanart.jpg')
    if addon.getSetting('posterfanart') == 'true':
        fanart = iconimage
        liz.setArt({'poster': iconimage})
    liz.setArt({'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name})

    if len(keyword) >= 1:
        keyw = (sys.argv[0] +
            "?mode=" + str('904') +
            "&keyword=" + urllib.quote_plus(keyword))
        contextMenuItems = []
        contextMenuItems.append(('[COLOR hotpink]Remove keyword[/COLOR]', 'xbmc.RunPlugin('+keyw+')'))
        liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=Folder)
    return ok

def _get_keyboard(default="", heading="", hidden=False):
    """ shows a keyboard and returns a value """
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return unicode(keyboard.getText(), "utf-8")
    return default



# videowood decode copied from: https://github.com/schleichdi2/OpenNfr_E2_Gui-5.3/blob/4e3b5e967344c3ddc015bc67833a5935fc869fd4/lib/python/Plugins/Extensions/MediaPortal/resources/hosters/videowood.py
def videowood(data):
    parse = re.search('(....ωﾟ.*?);</script>', data)
    if parse:
        todecode = parse.group(1).split(';')
        todecode = todecode[-1].replace(' ','')

        code = {
            "(ﾟДﾟ)[ﾟoﾟ]" : "o",
            "(ﾟДﾟ) [return]" : "\\",
            "(ﾟДﾟ) [ ﾟΘﾟ]" : "_",
            "(ﾟДﾟ) [ ﾟΘﾟﾉ]" : "b",
            "(ﾟДﾟ) [ﾟｰﾟﾉ]" : "d",
            "(ﾟДﾟ)[ﾟεﾟ]": "/",
            "(oﾟｰﾟo)": '(u)',
            "3ﾟｰﾟ3": "u",
            "(c^_^o)": "0",
            "(o^_^o)": "3",
            "ﾟεﾟ": "return",
            "ﾟωﾟﾉ": "undefined",
            "_": "3",
            "(ﾟДﾟ)['0']" : "c",
            "c": "0",
            "(ﾟΘﾟ)": "1",
            "o": "3",
            "(ﾟｰﾟ)": "4",
            }
        cryptnumbers = []
        for searchword,isword in code.iteritems():
            todecode = todecode.replace(searchword,isword)
        for i in range(len(todecode)):
            if todecode[i:i+2] == '/+':
                for j in range(i+2, len(todecode)):
                    if todecode[j:j+2] == '+/':
                        cryptnumbers.append(todecode[i+1:j])
                        i = j
                        break
                        break
        finalstring = ''
        for item in cryptnumbers:
            chrnumber = '\\'
            jcounter = 0
            while jcounter < len(item):
                clipcounter = 0
                if item[jcounter] == '(':
                    jcounter +=1
                    clipcounter += 1
                    for k in range(jcounter, len(item)):
                        if item[k] == '(':
                            clipcounter += 1
                        elif item[k] == ')':
                            clipcounter -= 1
                        if clipcounter == 0:
                            jcounter = 0
                            chrnumber = chrnumber + str(eval(item[:k+1]))
                            item = item[k+1:]
                            break
                else:
                    jcounter +=1
            finalstring = finalstring + chrnumber.decode('unicode-escape')
        stream_url = re.search('=\s*(\'|")(.*?)$', finalstring)
        if stream_url:
            return stream_url.group(2)
    else:
        return



def streamdefence(html):
    if 'iframe src="' in html:
        return html
    match = re.findall(r'(?:=|\()"([^"]+)', html, re.DOTALL | re.IGNORECASE)
    try:
        decoded = ''
        if match:
            for result in match:
                try:
                    decoded += base64.b64decode(result)
                except:
                    pass
        else:
            decoded = base64.b64decode(html)
    except TypeError:
        return html
    return streamdefence(decoded)


def searchDir(url, mode, page=None):
    addDir('[COLOR hotpink]Add Keyword[/COLOR]', url, 902, uwcimage('uwc-search.png'), '', mode, Folder=False)
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    try:
        if addon.getSetting('searchsort') == 'true':
            c.execute("SELECT * FROM keywords order by keyword")
        else:
            c.execute("SELECT * FROM keywords")
        for (keyword,) in c.fetchall():
            name = '[COLOR deeppink]' + urllib.unquote_plus(keyword) + '[/COLOR]'
            addDir(name, url, mode, uwcimage('uwc-search.png'), page=page, keyword=keyword)
    except:
        pass
    xbmcplugin.endOfDirectory(addon_handle)

@url_dispatcher.register('902', ['url', 'channel'])
def newSearch(url, channel):
    vq = _get_keyboard(heading="Searching for...")
    if not vq:
        return False, 0
    title = urllib.quote_plus(vq)
    addKeyword(title)
    xbmc.executebuiltin('Container.Refresh')
    #searchcmd = (sys.argv[0] +
    #     "?url=" + urllib.quote_plus(url) +
    #     "&mode=" + str(mode) +
    #     "&keyword=" + urllib.quote_plus(title))
    #xbmc.executebuiltin('xbmc.RunPlugin('+searchcmd+')')

@url_dispatcher.register('903')
def clearSearch():
    delallKeyword()
    xbmc.executebuiltin('Container.Refresh')


def addKeyword(keyword):
    xbmc.log(keyword)
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO keywords VALUES (?)", (keyword,))
    conn.commit()
    conn.close()


def delallKeyword():
    yes = dialog.yesno('Warning','This will clear all the keywords', 'Continue?', nolabel='No', yeslabel='Yes')
    if yes:
        conn = sqlite3.connect(favoritesdb)
        c = conn.cursor()
        c.execute("DELETE FROM keywords;")
        conn.commit()
        conn.close()

@url_dispatcher.register('904', ['keyword'])
def delKeyword(keyword):
    xbmc.log('keyword: ' + keyword)
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM keywords WHERE keyword = ?", (keyword,))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register('908')
def backup_keywords():
    path = xbmcgui.Dialog().browseSingle(0, 'Select directory to place backup' ,'myprograms')
    progress.create('Backing up', 'Initializing')
    if not path:
        return
    import json
    import gzip
    import datetime
    progress.update(25, "Reading database")
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM keywords")
    keywords = [{"keyword": keyword} for (keyword,) in c.fetchall()]
    if not keywords:
        progress.close()
        notify("Keywords empty", "No keywords to back up")
        return
    conn.close()
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_content = {"meta": {"type": "uwc-keywords", "version": 1, "datetime": time}, "data": keywords}
    if progress.iscanceled():
        progress.close()
        return
    progress.update(75, "Writing backup file")
    filename = "uwc-keywords_" + time + '.bak'
    try:
        with gzip.open(path + filename, "wb") as fav_file:
            json.dump(backup_content, fav_file)
    except IOError:
        progress.close()
        notify("Error: invalid path", "Do you have permission to write to the selected folder?")
        return
    progress.close()
    dialog.ok("Backup complete", "Backup file: {}".format(path + filename))


def check_if_keyword_exists(keyword):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM keywords WHERE keyword = ?", (keyword,))
    row = c.fetchone()
    conn.close()
    if row:
        return True
    return False


@url_dispatcher.register('909')
def restore_keywords():
    path = dialog.browseSingle(1, 'Select backup file' ,'myprograms')
    if not path:
        return
    import json
    import gzip
    try:
        with gzip.open(path, "rb") as fav_file:
            backup_content = json.load(fav_file)
    except (ValueError, IOError):
        notify("Error", "Invalid backup file")
        return
    if not backup_content["meta"]["type"] == "uwc-keywords":
        notify("Error", "Invalid backup file")
        return
    keywords = backup_content["data"]
    if not keywords:
        notify("Error", "Empty backup")
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
    dialog.ok("Restore complete", "Restore skips items that are already present in keywords to avoid duplicates", "Added: {}".format(added), "Skipped: {}".format(skipped))


def textBox(heading,announce):
    class TextBox():
        WINDOW=10147
        CONTROL_LABEL=1
        CONTROL_TEXTBOX=5
        def __init__(self,*args,**kwargs):
            xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW, ))
            self.win=xbmcgui.Window(self.WINDOW)
            xbmc.sleep(500)
            self.setControls()
        def setControls(self):
            self.win.getControl(self.CONTROL_LABEL).setLabel(heading)
            try: f=open(announce); text=f.read()
            except: text=announce
            self.win.getControl(self.CONTROL_TEXTBOX).setText(str(text))
            return
    TextBox()
    while xbmc.getCondVisibility('Window.IsVisible(10147)'):
        xbmc.sleep(500)


def selector(dialog_name, select_from, dont_ask_valid=False, sort_by=None, reverse=False):
    '''
    Shows a dialog where the user can choose from the values provided
    Returns the value of the selected key, or None if no selection was made
    
    Usage:
        dialog_name = title of the dialog shown
        select_from = a list or a dictionary which contains the options

        optional arguments
        dont_ask_valid (False) = sets if dontask addon setting should be considered
                         if True, the dialog won't be shown and the first element
                         will be selected automatically
        sort_by (None) = in case of dictionaries the keys will be sorted according this value
                  in case of a list, the list will be ordered
        reverse (False) = sets if order should be reversed
    '''
    if isinstance(select_from, dict):
        keys = sorted(list(select_from.keys()), key=sort_by, reverse=reverse)
        values = [select_from[x] for x in keys]
    else:
        keys = sorted(select_from, key=sort_by, reverse=reverse)
        values = None
    if not keys:
        return None
    if (dont_ask_valid and addon.getSetting("dontask") == "true") or len(keys) == 1:
        selected = 0
    else:
        selected = dialog.select(dialog_name, keys)
    if selected == -1:
        return None
    return values[selected] if values else keys[selected]


class VideoPlayer():
    def __init__(self, name, download=False, regex='''(?:src|SRC|href|HREF)=\s*["']([^'"]+)''', direct_regex="""<source.*?src=(?:"|')([^"']+)[^>]+>"""):
        self.regex = regex
        self.direct_regex = direct_regex
        self.name = name
        self.download = download
        self.progress = xbmcgui.DialogProgress()
        self.progress.create('Playing video', 'Searching for videofile')

        import resolveurl as resolveurl
        self.resolveurl = resolveurl
        xxx_plugins_path = 'special://home/addons/script.module.resolveurl.xxx/resources/plugins/'
        if xbmcvfs.exists(xxx_plugins_path):
            self.resolveurl.add_plugin_dirs(xbmc.translatePath(xxx_plugins_path))

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
        self.progress.update(25, "", "Loading video page", "")
        html = getHtml(url, referrer)
        self.play_from_html(html, url)

    @_cancellable
    def play_from_html(self, html, url=None):
        self.progress.update(40, "", "Searching for supported hosts", "")
        solved_suburls = self._check_suburls(html, url)
        self.progress.update(60, "", "Searching for supported hosts", "")
        direct_links = None
        if self.direct_regex:
            direct_links = re.compile(self.direct_regex, re.DOTALL | re.IGNORECASE).findall(html)
            if direct_links:
                if 'function/0/' in direct_links[0]:
                    licensecode = re.compile("license_code:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).search(html).group(1)
                    direct_links[0] = decryptHash(direct_links[0], licensecode, '16')           
                selected = 'https:' + direct_links[0] if direct_links[0].startswith('//') else direct_links[0]
                self.progress.update(70, "", "", "Playing from direct link")
                self.play_from_direct_link(selected)
            elif not self.regex:
                notify('Oh oh','Could not find a supported link')
        if self.regex and not direct_links:
            scraped_sources = self.resolveurl.scrape_supported(html, self.regex)
            scraped_sources = scraped_sources if scraped_sources else []
            scraped_sources.extend(solved_suburls)
            self.play_from_link_list(scraped_sources)
        if not self.direct_regex and not self.regex:
            raise ValueError("No regular expression specified")
            

    @_cancellable
    def play_from_link_list(self, links):
        use_universal = True if addon.getSetting("universal_resolvers") == "true" else False
        sources = self._clean_urls([self.resolveurl.HostedMediaFile(x, title=x.split('/')[2], include_universal=use_universal) for x in links])
        if not sources:
            notify('Oh oh','Could not find a supported link')
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
        if type(source) is str:
            self.play_from_link_list([source])
            return
        self.progress.update(80, "", "Passing link to ResolveURL", "Playing from " + source.title)
        try:
            link = source.resolve()
        except self.resolveurl.resolver.ResolverError:
            link = False # ResolveURL returns False in some cases when resolving fails
        if not link:
            notify('Resolve failed', '{} link could not be resolved'.format(source.title))
        else:
            self.play_from_direct_link(link)

    @_cancellable
    def play_from_direct_link(self, direct_link):
        self.progress.update(90, "", "Playing video", "")
        playvid(direct_link, self.name, self.download)

    @_cancellable
    def _check_suburls(self, html, referrer_url):
        sdurl = re.compile(r'streamdefence\.com/view.php\?ref=([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
        sdurl_world = re.compile(r'.strdef\.world/([^"]+)', re.DOTALL | re.IGNORECASE).findall(html)
        fcurl = re.compile(r'filecrypt\.cc/Container/([^\.]+)\.html', re.DOTALL | re.IGNORECASE).findall(html)
        shortixurl = re.compile(r'1155xmv\.com/\?u=(\w+)', re.DOTALL | re.IGNORECASE).findall(html)
        links = []
        if sdurl or sdurl_world or fcurl or shortixurl:
            self.progress.update(50, "", "Found subsites", "")
        if sdurl:
            links.extend(self._solve_streamdefence(sdurl, referrer_url, False))
        elif sdurl_world:
            links.extend(self._solve_streamdefence(sdurl_world, referrer_url, True))
        elif fcurl:
            links.extend(self._solve_filecrypt(fcurl, referrer_url))
        elif shortixurl:
            links.extend(self._solve_shortix(shortixurl, referrer_url))
        return links

    @_cancellable
    def _solve_streamdefence(self, sdurls, url, world=False):
        self.progress.update(55, "", "Loading streamdefence sites", "")
        sdpages = ''
        for sd_url in sdurls:
            if not world:
                sdurl = 'http://www.streamdefence.com/view.php?ref=' + sd_url
            else:
                sdurl = 'https://www.strdef.world/' + sd_url
            sdsrc = getHtml(sdurl, url if url else sdurl)
            sdpage = streamdefence(sdsrc)
            sdpages += sdpage
        sources = set(re.compile('iframe src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(sdpages))
        srcs = set()
        for source in sources:
            if 'strdef.world/player' in source:
                source = getVideoLink(source, url)
            srcs.add(source)
        return srcs

    @_cancellable
    def _solve_filecrypt(self, fc_urls, url):
        self.progress.update(55, "", "Loading filecrypt sites", "")
        sites = set()
        for fc_url in fc_urls:
            fcurl = 'http://filecrypt.cc/Container/' + fc_url + ".html"
            fcsrc = getHtml(fcurl, url if url else fcurl, headers)
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
        self.progress.update(55, "", "Loading streamdefence sites", "")
        sources = set()
        for shortix in shortixurls:
            shortixurl = 'https://1155xmv.com/?u=' + shortix
            shortixsrc = getHtml(shortixurl, url if url else shortixurl)
            sources.add(re.compile('src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(shortixsrc)[0])
        return sources


def playvideo(videosource, name, download=None, url=None, regex='''(?:src|SRC|href|HREF)=\s*["']([^'"]+)'''):
    """Deprecated function, use VideoPlayer class.
    Exists for compatiblity with old site plug-ins."""
    vp = VideoPlayer(name, download, regex)
    vp.play_from_html(videosource)


def PLAYVIDEO(url, name, download=None, regex='''(?:src|SRC|href|HREF)=\s*["']([^'"]+)'''):
    """Deprecated function, use VideoPlayer class.
    Exists for compatiblity with old site plug-ins."""
    vp = VideoPlayer(name, download, regex)
    vp.play_from_site_link(url, url)

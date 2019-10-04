#-*- coding: utf-8 -*-

'''
    Ultimate Whitecream
    Copyright (C) 2018 Whitecream, anton40, holisticdioxide

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

import xbmc
import xbmcplugin
import xbmcgui
import base64
from resources.lib import utils
progress = utils.progress
import urllib2,urllib

@utils.url_dispatcher.register('380')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://hclips.com/search/?p=0&q=', 384, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://hclips.com/categories/', 383, '', '')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]','https://hclips.com/channels/name/', 385, '', '')
    List('https://hclips.com/latest-updates/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('381', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile('href="([^"]+)"[^\/]+?src="([^"]+)"\s*alt="([^"]+)"[^<]+?<span class="dur">([^<]+)<(.+?)div class="info-small"', re.DOTALL).findall(listhtml)
    for videopage, img, name, dur, hd in match:
        if 'hd_video' in hd:
            hd = " [COLOR orange]HD[/COLOR] "
        else:
            hd = " "
        name = utils.cleantext(name)
        name = name + hd + "[COLOR deeppink]" + dur + "[/COLOR]"
        utils.addDownLink(name, videopage, 382, img, '')
    try:
        nextp=re.compile('class="paginator__item paginator__item--next paginator__item--arrow" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', 'http://www.hclips.com' + nextp[0], 381,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('384', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 384)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('383', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="([^"]+)" class="thumb">.*?src="([^"]+)"[^<]+<strong class="title">([^<]+)<.*?<b>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, vids in match:
        name = '%s [COLOR deeppink]%s videos[/COLOR]' %(name, vids)
        utils.addDir(name, catpage, 381, img, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('385', ['url'])
def Channels(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile('<a href="([^"]+)" class="video_thumb" title="([^"]+)">.+?<img height="165" width="285" src="([^"]+)".*?<b>([^<]+)<', re.DOTALL).findall(listhtml)
    for chanpage, name, img, vids in match:
        name = utils.cleantext(name)
        name = '%s [COLOR deeppink]%s videos[/COLOR]' %(name, vids)
        utils.addDir(name, 'https://hclips.com' + chanpage, 381, img, '')
    try:
        nextp=re.compile('class="paginator__item paginator__item--next paginator__item--arrow" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', 'https://www.hclips.com' + nextp[0], 385,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


# @utils.url_dispatcher.register('386', ['url'])
# def ChannelList(url):
    # listhtml = utils.getHtml(url, '')
    # match = re.compile('<a href="([^"]+)" class="thumb" data-rt=".+?">.+?<img  width="220" height="165" src="([^"]+)" alt="([^"]+)"', re.DOTALL).findall(listhtml)
    # for videopage, img, name in match:
        # name = utils.cleantext(name)
        # utils.addDownLink(name, 'http://www.hclips.com' + videopage, 382, img, '')
    # try:
        # nextp=re.compile('<li class="next">.+?<a href="([^"]+)".*?>Next</a>', re.DOTALL | re.IGNORECASE).findall(listhtml)
        # utils.addDir('Next Page', 'http://www.hclips.com' + nextp[0], 386,'')
    # except: pass
    # xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('382', ['url', 'name'], ['download'])    
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download = download)
    vp.progress.update(25, "", "Playing video", "")        
    videolink = GetTxxxVideo(url)
    vp.progress.update(40, "", "Playing video", "")    
    vp.play_from_direct_link(videolink)
    
    
def GetTxxxVideo(vidpage):
    vidpagecontent = utils.getHtml(vidpage)
    posturl = 'https://%s/sn4diyux.php' % vidpage.split('/')[2]

    pC3 = re.search('''pC3:'([^']+)''', vidpagecontent).group(1)
    vidid = re.search('''video_id["|']?:\s?(\d+)''', vidpagecontent).group(1)
    data = '%s,%s' % (vidid, pC3)
    vidcontent = utils.getHtml(posturl, referer=vidpage, data={'param': data})
    vidurl = re.search('video_url":"([^"]+)', vidcontent).group(1)
    replacemap = {'M':'\u041c', 'A':'\u0410', 'B':'\u0412', 'C':'\u0421', 'E':'\u0415', '=':'~', '+':'.', '/':','}
    
    for key in replacemap:
        vidurl = vidurl.replace(replacemap[key], key)

    vidurl = base64.b64decode(vidurl)

    return vidurl + "|Referer=" + vidpage


"""

	vp = utils.VideoPlayer(name, download)
	vp.progress.update(25, "", "Loading video page", "")
	html = utils.getHtml(url, '')
	videourl = re.compile('video_url="([^"]+)"').findall(html)[0]
	videourl += re.compile('video_url\+="([^"]+)"').findall(html)[0]	
	partes = videourl.split('||')
	videourl = decode_url(partes[0])
	videourl = re.sub('/get_file/\d+/[0-9a-z]{32}/', partes[1], videourl)
	videourl += '&' if '?' in videourl else '?'
	videourl += 'lip=' + partes[2] + '&lt=' + partes[3]	
	vp.play_from_direct_link(videourl)

def decode_url(txt):
	_0x52f6x15 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
	reto = ''; n = 0
	# En las dos siguientes líneas, ABCEM ocupan 2 bytes cada letra! El replace lo deja en 1 byte. !!!!: АВСЕМ (10 bytes) ABCEM (5 bytes)
	txt = re.sub('[^АВСЕМA-Za-z0-9\.\,\~]', '', txt)
	txt = txt.replace('А', 'A').replace('В', 'B').replace('С', 'C').replace('Е', 'E').replace('М', 'M')
	
	while n < len(txt):
		a = _0x52f6x15.index(txt[n])
		n += 1
		b = _0x52f6x15.index(txt[n])
		n += 1
		c = _0x52f6x15.index(txt[n])
		n += 1
		d = _0x52f6x15.index(txt[n])
		n += 1
	
		a = a << 2 | b >> 4
		b = (b & 15) << 4 | c >> 2
		e = (c & 3) << 6 | d
		reto += chr(a)
		if c != 64: reto += chr(b)
		if d != 64: reto += chr(e)
	
	return urllib.unquote(reto)
"""
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

import re

import xbmc
import xbmcplugin
import xbmcgui
import base64
from resources.lib import utils
import urllib2,urllib
progress = utils.progress

@utils.url_dispatcher.register('360')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.tubepornclassic.com/categories/', 363, '', '')
    utils.addDir('[COLOR hotpink]Top Rated[/COLOR]','http://www.tubepornclassic.com/top-rated/', 361, '', '')
    utils.addDir('[COLOR hotpink]Most Viewed[/COLOR]','http://www.tubepornclassic.com/most-popular/', 361, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.tubepornclassic.com/search/', 364, '', '')    
    List('http://www.tubepornclassic.com/latest-updates/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('361', ['url'])
def List(url):
	try:
		listhtml = utils.getHtml3(url)
	except:
		return None
	match = re.compile('<div class="item  ">.+?<a href="([^"]+)".+?class.+?src="([^"]+)".+?alt="([^"]+)".+?class="duration">(.+?)<', re.DOTALL | re.IGNORECASE).findall(listhtml)





	for videopage, img, name, duration in match:
		name = utils.cleantext(name)
		name = name + " [COLOR deeppink]" + duration + "[/COLOR]"
		utils.addDownLink(name, videopage, 362, img, '')
	try:
		nextp = re.compile('<a href="([^"]+)"[^>]+>Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
		utils.addDir('Next Page', 'http://www.tubepornclassic.com/' + nextp[0], 361,'')
	except: pass
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('364', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 364)
    else:
        title = keyword.replace(' ','%20')
        searchUrl = searchUrl + title + "/"
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('363', ['url'])
def Cat(url):
	listhtml = utils.getHtml3(url)
	match = re.compile('<a class="list-item__link" href="([^"]+)" title="([^"]+)".*?class="list-item__info">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
	for catpage, name, videos in match:
		videos=videos.replace(' ','')
		name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"		
		utils.addDir(name, catpage, 361)
	xbmcplugin.endOfDirectory(utils.addon_handle)
	
@utils.url_dispatcher.register('362', ['url', 'name'], ['download'])	
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
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



'''


	vp = utils.VideoPlayer(name, download)
	vp.progress.update(25, "", "Loading video page", "")
	html = utils.getHtml3(url)
	videourl = re.compile('video_url="([^"]+)"').findall(html)[0]
	videourl += re.compile('video_url\+="([^"]+)"').findall(html)[0]	
	
	
	videourl1 = re.compile('video_url="([^"]+)"').findall(html)[0]
	videourl2 = re.compile('video_url\+="([^"]+)"').findall(html)[0]		
	
	partes = videourl.split('||')
	videourl = decode_url(partes[0])
	
	videourl3 = decode_url(partes[0])
	
	videourl = re.sub('/get_file/\d+/[0-9a-z]{32}/', partes[1], videourl)
	videourl += '&' if '?' in videourl else '?'
	videourl += 'lip=' + partes[2] + '&lt=' + partes[3]	 + '&f=video.m3u8'
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
'''	
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
import json
import base64
import os


from resources.lib import utils
progress = utils.progress
import urllib2,urllib

@utils.url_dispatcher.register('380')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://hclips.com/api/json/categories/14400/str.all.json', 383, '', '')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]','https://hclips.com/api/json/channels/14400/str/latest-updates/80/..1.json', 385, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://hclips.com/api/videos.php?params=259200/str/relevance/60/search..1.all..day&sort=latest-updates&date=day&type=all&s=', 384, '', '')    
    List('https://hclips.com/api/json/videos/86400/str/latest-updates/60/..1.all..day.json')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('381', ['url'])
def List(url):
    
    m = re.search('\.(\d+)\.', url)
    if m:
        page = int(m.group(1))
    else:
        page = 1

    listjson = utils.getHtml(url, url)
    js = json.loads(listjson)
    
    if "videos" in js.keys():
        for video in js["videos"]:
            videopage = "https://hclips.com/videos/" + video["video_id"] + "/" + video["dir"] + "/"
            img = video["scr"]
            name = video["title"]
            name = name.encode("UTF-8")
            dur = video["duration"]
            hd = " "
            if "props" in video.keys():
                if video["props"]:
                    if "hd" in video["props"].keys():
                        if video["props"]["hd"] == "1":
                            hd = " [COLOR orange]HD[/COLOR] "
                        else:
                            utils.kodilog(name)
                            utils.kodilog(video["props"]["hd"])
            n = hd + "[COLOR deeppink]" + dur + "[/COLOR]"
            name += n.encode("UTF-8")
            utils.addDownLink(name, videopage, 382, img, '')

        npage = page + 1
        url = url.replace('.'+str(page)+'.', '.'+str(npage)+'.')
        utils.addDir('Next Page (' + str(page) + ')', url, 381, '')

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
    listjson = utils.getHtml(url, url)
    js = json.loads(listjson)

    for cat in sorted(js["categories"], key = lambda x: x["title"]):
        catpage = cat["dir"]
        catpage = "https://hclips.com/api/json/videos/86400/str/latest-updates/60/categories.{}.1.all..day.json".format(catpage)
        name = cat["title"]
        vids = cat["total_videos"]
        vids = ' [COLOR deeppink]{} videos[/COLOR]'.format(vids).encode("UTF-8") 
        name = name.encode("UTF-8")
        name += vids
        utils.addDir(name, catpage, 381, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('385', ['url'])
def Channels(url):
    m = re.search('\.(\d+)\.', url)
    if m:
        page = int(m.group(1))
    else:
        page = 1

    listjson = utils.getHtml(url, url)
    js = json.loads(listjson)

    if "channels" in js.keys():
        for chan in js["channels"]:
            catpage = chan["dir"]
            catpage = "https://hclips.com/api/json/videos/3600/str/latest-updates/20/channel.{}.1.all...json".format(catpage)
            name = chan["title"]
            name = name.encode("UTF-8")
            img = chan["img"]
            utils.addDir(name, catpage, 381, img, '')
            
        npage = page + 1
        url = url.replace('.'+str(page)+'.', '.'+str(npage)+'.')
        utils.addDir('Next Page (' + str(page) + ')', url, 385, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)
    



@utils.url_dispatcher.register('382', ['url', 'name'], ['download'])    
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download = download)
    vp.progress.update(25, "", "Playing video", "")        
    videolink = GetTxxxVideo(url)
    if videolink.startswith('/'):
        videolink = 'https://hclips.com' + videolink
    vp.progress.update(40, "", "Playing video", "")    
    vp.play_from_direct_link(videolink)
    
def GetTxxxVideo(videopage):
    id = videopage.split('/')[-3]
    vidpage = "https://hclips.com/api/videofile.php?video_id={}&lifetime=8640000".format(id)
    vidcontent = utils.getHtml(vidpage, videopage)
    vidurl = re.search('video_url":"([^"]+)', vidcontent).group(1)
    replacemap = {'M':'\u041c', 'A':'\u0410', 'B':'\u0412', 'C':'\u0421', 'E':'\u0415', '=':'~', '+':'.', '/':','}
    for key in replacemap:
        vidurl = vidurl.replace(replacemap[key], key)
    vidurl = base64.b64decode(vidurl)
    return vidurl + "|Referer=" + vidpage    


# def GetTxxxVideo(vidpage):
    # vidpagecontent = utils.getHtml(vidpage)
    # posturl = 'https://%s/sn4diyux.php' % vidpage.split('/')[2]

    # pC3 = re.search('''pC3:'([^']+)''', vidpagecontent).group(1)
    # vidid = re.search('''video_id["|']?:\s?(\d+)''', vidpagecontent).group(1)
    # data = '%s,%s' % (vidid, pC3)
    # vidcontent = utils.getHtml(posturl, referer=vidpage, data={'param': data})
    # vidurl = re.search('video_url":"([^"]+)', vidcontent).group(1)
    # replacemap = {'M':'\u041c', 'A':'\u0410', 'B':'\u0412', 'C':'\u0421', 'E':'\u0415', '=':'~', '+':'.', '/':','}
    
    # for key in replacemap:
        # vidurl = vidurl.replace(replacemap[key], key)

    # vidurl = base64.b64decode(vidurl)

    # return vidurl + "|Referer=" + vidpage


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
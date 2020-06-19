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

import xbmcplugin
import xbmcgui
from resources.lib import utils
 

@utils.url_dispatcher.register('150')
def HQMAIN():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://hqporner.com/porn-categories.php',153,'','')
    utils.addDir('[COLOR hotpink]Studios[/COLOR]','https://hqporner.com/porn-studios.php',153,'','')
    utils.addDir('[COLOR hotpink]Girls[/COLOR]','https://hqporner.com/porn-actress.php',153,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://hqporner.com/?s=',154,'','')
    HQLIST('https://hqporner.com/hdporn/1')


@utils.url_dispatcher.register('151', ['url'])
def HQLIST(url):
	
    try:
        link = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="box feature">\s*<a href="([^"]+)".+?src="([^"]+)" alt="([^"]+)".+?class="icon fa-clock-o meta-data">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(link)  
    for url, img, name, duration in match:
        name = utils.cleantext(name).capitalize() + " [COLOR deeppink]" + duration + "[/COLOR]"
        videourl = "https://www.hqporner.com" + url
        if img.startswith('//'):
            img = 'https:' + img + '|verifypeer=false'
        utils.addDownLink(name, videourl, 152, img, '')
    try:
        nextp=re.compile('<a href="([^"]+)" class="button mobile-pagi pagi-btn">Next</a>', re.DOTALL | re.IGNORECASE).findall(link)
        nextp = "https://www.hqporner.com" + nextp[0]
        page_nr = re.findall('\d+', nextp)[-1]
        utils.addDir('Next Page (' + page_nr + ')', nextp, 151, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('153', ['url'])
def HQCAT(url):
    link = utils.getHtml(url, '')
    tags = re.compile('<a href="([^"]+)"[^<]+<img src="([^"]+)" alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(link)
    tags = sorted(tags, key=lambda x: x[2])
    for caturl, catimg, catname in tags:
        caturl = "https://www.hqporner.com" + caturl
        #catimg = "https://www.hqporner.com" + catimg
        if catimg.startswith('//'):
            catimg = 'https:' + catimg + '|verifypeer=false'        
        utils.addDir(catname,caturl,151,catimg)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('154', ['url'], ['keyword'])
def HQSEARCH(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 154)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        HQLIST(searchUrl)


@utils.url_dispatcher.register('152', ['url', 'name'], ['download'])
def HQPLAY(url, name, download=None):
	videopage = utils.getHtml(url, url)
	iframeurl = re.compile(r"nativeplayer\.php\?i=([^']+)", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
	if iframeurl.startswith('//'):
		iframeurl = 'https:' + iframeurl
	if re.search('bemywife', iframeurl, re.DOTALL | re.IGNORECASE):
		videourl = getBMW(iframeurl)
	elif re.search('mydaddy', iframeurl, re.DOTALL | re.IGNORECASE):
		videourl = getBMW(iframeurl)        
	elif re.search('5\.79', iframeurl, re.DOTALL | re.IGNORECASE):
		videourl = getIP(iframeurl)
	elif re.search('flyflv', iframeurl, re.DOTALL | re.IGNORECASE):
		videourl = getFly(iframeurl)
	elif re.search('hqwo', iframeurl, re.DOTALL | re.IGNORECASE):
		videourl = getHQWO(iframeurl)
	else:
		utils.notify('Oh oh','Couldn\'t find a supported videohost')
		return
	#play_item = xbmcgui.ListItem(path=videourl)
	#xbmcplugin.setResolvedUrl(utils.addon_handle, True, listitem=play_item)
        if not videourl:
                return
	utils.playvid(videourl, name, download)


def getBMW(url):
    videopage = utils.getHtml(url, '')
    #redirecturl = utils.getVideoLink(url, '')
    #videodomain = re.compile("http://([^/]+)/", re.DOTALL | re.IGNORECASE).findall(redirecturl)[0]
    videos = re.compile(r"<a href='([^']+)' style='color:#ddd'>(.+?)</a>", re.DOTALL | re.IGNORECASE).findall(videopage)
    list = {}
    for video_link, quality in videos:
        quality = quality.replace('4K', '2160p')
        list[quality] = video_link
    videourl = utils.selector('Select quality', list, dont_ask_valid=True, sort_by=lambda x: int(re.findall(r'\d+', x)[0]), reverse=True)
    if not videourl:
        return
    if videourl.startswith('//'):
        videourl = 'https:' + videourl
    return videourl


def getIP(url):
    videopage = utils.getHtml(url, '')
    videos = re.compile('file": "([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    videourl = videos[-1]
    if videourl.startswith('//'):
        videourl = 'https:' + videourl
    return videourl

def getFly(url):
    videopage = utils.getHtml(url, '')
#    videos = re.compile('fileUrl="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    videos = re.compile(r"<source src='([^']+)'.*?label='([^']+)'", re.DOTALL | re.IGNORECASE).findall(videopage)
    list = {}
    for video_link, quality in videos:
        quality = quality.replace('4K', '2160p')
        list[quality] = video_link
    videourl = utils.selector('Select quality', list, dont_ask_valid=True, sort_by=lambda x: int(re.findall(r'\d+', x)[0]), reverse=True)
    if not videourl:
        return
    if videourl.startswith('//'):
        videourl = 'https:' + videourl
    return videourl

def getHQWO(url):
    videopage1 = utils.getHtml(url, '')
    videos1 = re.compile("<script type='text/javascript' src='([^']+)'></script>", re.DOTALL | re.IGNORECASE).findall(videopage1)
    url = videos1[-1]
    videopage2 = utils.getHtml(url, '')
    videos = re.compile('"file": "([^"]+)".*?"label": "([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage2)
    list = {}
    for video_link, quality in videos:
        quality = quality.replace('4K', '2160p')
        list[quality] = video_link
    videourl = utils.selector('Select quality', list, dont_ask_valid=True, sort_by=lambda x: int(re.findall(r'\d+', x)[0]), reverse=True)
    if not videourl:
        return
    if videourl.startswith('//'):
        videourl = 'https:' + videourl
    return videourl

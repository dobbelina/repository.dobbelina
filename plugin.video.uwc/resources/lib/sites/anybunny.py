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
from resources.lib import utils
    

@utils.url_dispatcher.register('320')
def Main():
    utils.addDir('[COLOR hotpink]Top videos[/COLOR]','http://anybunny.com/top/',321,'','')
    utils.addDir('[COLOR hotpink]Categories - images[/COLOR]','http://anybunny.com/',323,'','')
    utils.addDir('[COLOR hotpink]Categories - all[/COLOR]','http://anybunny.com/',325,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://anybunny.com/new/',324,'','')
    List('http://anybunny.com/new/?p=1')
    xbmcplugin.endOfDirectory(utils.addon_handle)

    
@utils.url_dispatcher.register('321', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        
        return None
    match = re.compile(r"<a class='nuyrfe' href='([^']+).*?src='([^']+)' id=\d+ alt='([^']+)'", re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 322, img, '')
    try:
        nextp = re.compile('href="([^"]+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', nextp[0], 321,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('322', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    #vp = utils.VideoPlayer(name, download, "video_url: '([^']+)'")
    #vp.progress.update(25, "", "Loading video page", "")
    #listhtml = utils.getHtml(url)
    #videourl = re.compile('iframe width="\d+" height="\d+" src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    #vp.progress.update(45, "", "Loading video page", "")
    #videohtml = utils.getHtml(videourl)
    #ktplayer = re.compile("<script type=\"text/javascript\" src='([^']+)'>", re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
    #ktplayer = 'https://azblowjobtube.com' + ktplayer
    #vp.progress.update(65, "", "Loading video page", "")
    #kthtml = utils.getHtml(ktplayer)
    #vars = re.compile(',([a-z]+)="([^"]*)"', re.DOTALL | re.IGNORECASE).findall(kthtml)
    #videolink = re.compile('video_url:([^,]+),', re.DOTALL | re.IGNORECASE).findall(kthtml)[0]
    #for (var, value) in vars:
    #    videolink = videolink.replace(var, value)
    #videolink = videolink.replace('"','')
    #videolink = videolink.replace('+','')
    #vp.progress.update(85, "", "Loading video page", "")
    #vp.play_from_direct_link(videolink)
    vp = utils.VideoPlayer(name, download, 'src=["]([^"]+)')
    vp.play_from_site_link(url)

@utils.url_dispatcher.register('323', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("<a href='/top/([^']+)'>.*?src='([^']+)' alt='([^']+)'", re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catid, img, name in match:
        catpage = "http://anybunny.com/new/"+ catid
        utils.addDir(name, catpage, 321, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('325', ['url'])
def Categories2(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r"href='/top/([^']+)'>([^<]+)</a> <a>([^)]+\))", re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catid, name, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"
        catpage = "http://anybunny.com/new/"+ catid
        utils.addDir(name, catpage, 321, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('324', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 324)
    else:
        title = keyword.replace(' ','_')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)

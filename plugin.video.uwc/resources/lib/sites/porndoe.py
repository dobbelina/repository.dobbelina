'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream

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
from resources.lib import utils

siteurl = 'https://porndoe.com'
    
@utils.url_dispatcher.register('720')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl+'/categories?sort=alpha',723,'','')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]',siteurl+'/channels?sort=ranking&page=1',725,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/search?keywords=',724,'','')
    List(siteurl+'/videos?page=1')



@utils.url_dispatcher.register('721', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('img  data-src="([^"]+)".+?alt="([^"]+)".+?<span class="txt">([^<]+)</span>.+?<span class="-mm-icon (.+?)"></span>.+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, duration, ico, videopage in match:
	if not videopage.startswith('http'): videopage = siteurl + videopage
        name = utils.cleantext(name)
        if ico == 'mm_icon-hd':
            ico = " [COLOR orange]HD[/COLOR] "
	else:
            if ico == 'mm_icon-vr' > 0:
                ico = " [COLOR green]VR[/COLOR] "
	    else:
	        ico = " "
        name = name + ico + "[COLOR deeppink]" + utils.cleantext(duration) + "[/COLOR]"
        utils.addDownLink(name, videopage, 722, img, '')
    try:
        next_page = re.compile('"page next">.+? href="([^"]+)"><span><span class="pager-next-label">Next<', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', siteurl + next_page, 721,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('722', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    videopage = utils.getHtml(url, '')
    embeded = re.compile('<link itemprop="embedURL" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    embededpage = utils.getHtml(embeded, url)
    videos = re.compile('<source[^=]+src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(embededpage)
    videourl = videos[-1].split('?')[0]
    if not videourl:
        return
    utils.playvid(videourl, name, download)




@utils.url_dispatcher.register('723', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('data-src="([^"]+)".+?href="([^"]+)">.+?class="txt">([^<]+)<.+?class="count">(\(\d+\))</span>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for img, catpage, name, count in match:
        name = utils.cleantext(name.strip()) + " [COLOR deeppink]" + utils.cleantext(count) + "[/COLOR]"
	catpage = siteurl + catpage
        utils.addDir(name, catpage, 721, img, 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('725', ['url'])
def Channels(url):
    utils.addDir('[COLOR hotpink]Channel Search[/COLOR]',siteurl+'/channels?name=',726,'','')
    cathtml = utils.getHtml(url, '')
    match = re.compile('a data-under href="([^"]+)".+?data-src="([^"]+)".+?title="([^"]+)">.+?class="number">([^<]+)</span>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, img, name, rank in match:
        name = utils.cleantext(name.strip())
	catpage = siteurl + catpage
        utils.addDir(name, catpage, 721, img, 2)    
    try:
        next_page = re.compile('"page next">.+? href="([^"]+)"><span><span class="pager-next-label">Next<', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', siteurl + next_page.replace('&amp;','&'), 725,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('724', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 724)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

@utils.url_dispatcher.register('726', ['url'], ['keyword'])
def SearchChannel(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 726)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        Channels(searchUrl)


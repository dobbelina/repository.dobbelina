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

siteurl = 'https://www.cliphunter.com'
    
@utils.url_dispatcher.register('730')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl + '/categories/',733,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl + '/search/',734,'','')
    List(siteurl + '/categories/All')



@utils.url_dispatcher.register('731', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('<a class="t.+?href="([^"]+)" >\s+<img class="i.+?src="([^"]+)".+?class="tr.+?>([^<]+)</div>(.+?)class="vttl.+?>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, duration, hd, name in match:
	if '>HD<' in hd:
	    hd = 'HD'
	else:
  	    hd = ' '
	videopage = siteurl + videopage
        name = utils.cleantext(name)
        name = name + " [COLOR orange]" + hd + "[/COLOR] " + "[COLOR deeppink]" + utils.cleantext(duration) + "[/COLOR]"
        utils.addDownLink(name, videopage, 732, img, '')
    try:
        next_page = re.compile('rel="next" href="([^"]+)">&raquo;', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', siteurl + next_page, 731,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('732', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    regex = ',"url":"(http[^"]+)"'
    vp = utils.VideoPlayer(name, download, '', regex)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url, '')
    vp.progress.update(50, "", "", "Playing from direct link")
    link = re.compile(regex, re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    link = link.replace('\/','/')
    vp.progress.update(75, "", "", "Playing from direct link")
    vp.play_from_direct_link(link)



@utils.url_dispatcher.register('733', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a href="([^"]+)" title="([^"]+)">[^<]+?<img src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in match:
	catpage = catpage.replace(' ','%20')
        name = utils.cleantext(name.strip())
        utils.addDir(name, siteurl + catpage, 731, img, 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('734', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 734)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

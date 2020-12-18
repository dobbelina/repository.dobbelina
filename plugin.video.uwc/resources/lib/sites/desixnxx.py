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
import xbmc, xbmcplugin
import xbmcgui
from resources.lib import utils

@utils.url_dispatcher.register('850')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://desixnxx2.net/?paged=1&s=', 853, '', '')
    utils.addDir('[COLOR hotpink]Myanmar[/COLOR]','http://desixnxx2.net/series/myanmar/page/1/', 851, '', '')
    utils.addDir('[COLOR hotpink]Nepal[/COLOR]','http://desixnxx2.net/series/nepal/page/1/', 851, '', '')
    utils.addDir('[COLOR hotpink]Sri-Lankan[/COLOR]','http://desixnxx2.net/series/sri-lankan/page/1/', 851, '', '')
    List('http://desixnxx2.net/last-added/page/1/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('851', ['url'])
def List(url):
    baseUrl = 'http://desixnxx2.net' if 'desixnxx2' in url else ''
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('<li class="thumi".+?duration2">([^"]+)<.+?href="([^"]+)" title="([^"]+)".+?src="([^"]+)"',
                       re.DOTALL | re.IGNORECASE).findall(listhtml)
    if 'masalaseen' in url:
        match = re.compile('<li class="thumi".+?duration">([^"]+)<.+?href="([^"]+)" title="([^"]+)".+?src="([^"]+)"',
                           re.DOTALL | re.IGNORECASE).findall(listhtml)
    for duration, videopage, name, img in match:
        utils.addDownLink('[COLOR hotpink]' + duration.replace('</div>', '').strip() + '[/COLOR] ' + utils.cleantext(name),
                          baseUrl + videopage, 852, img, '')
    try:
        nextp = re.compile('current".+?href=[\"\'](.+?)[\"\']').findall(listhtml)
        utils.addDir('Next Page', baseUrl + nextp[0], 851, '')
    except: pass        
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('852', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    videourl = re.compile("<source src=[\'\"](.+?)[\'\"]", re.DOTALL | re.IGNORECASE).findall(listhtml)[0].strip()
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)

    listitem.setInfo('video', {'Title': name, 'Genre': 'desixnxx'})
    xbmc.Player().play(videourl, listitem)



@utils.url_dispatcher.register('853', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 853)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


@utils.url_dispatcher.register('855')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://masalaseen.com/page/1/?paged=1&s=', 853, '', '')
    List('https://masalaseen.com/page/1/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

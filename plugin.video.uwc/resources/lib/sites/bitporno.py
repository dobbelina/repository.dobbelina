'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 anton40

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
import urllib2
import xbmc, xbmcplugin
import xbmcgui
from resources.lib import utils

@utils.url_dispatcher.register('860')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.bitporno.com/?q=', 863, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://www.bitporno.com/search/all/sort-mostviewed/time-today/page-0', 864, '', '')
    List('https://www.bitporno.com/search/all/sort-mostviewed/time-today/page-0')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('861', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('class="entry.+?href="([^"]+)".+?src="([^"]+)".+?color:#343434;">([^"]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        if '?q=' in url:
            utils.notify(url.split('=')[-1], 'No results!')
        else:
            utils.notify('No results!')
        return
    for videopage, img, name in match:
        if not '/v/' in videopage: continue 
        utils.addDownLink(name.replace('</div>', '').strip(), 'https://www.bitporno.com' + videopage, 862, img, '')
    try:
        nextp = re.compile('class="pages-active".+?href="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        utils.addDir('Next Page', 'https://www.bitporno.com' + nextp[0], 861, '')
    except: pass            
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('862', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    try:
        listhtml = utils.getHtml(url, '')
    except urllib2.HTTPError as e:
        utils.notify(name, e)
        return None
    except: 
        return None
    videourl = re.compile('file: "(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'bitporno'})
    xbmc.Player().play(videourl, listitem)


@utils.url_dispatcher.register('863', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 863)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

@utils.url_dispatcher.register('864', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('Categories(.+?)</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    categ = re.compile('href="(.+?)">(.+?)<', re.DOTALL | re.IGNORECASE).findall(match)
    for catpage, name in categ:
        utils.addDir(name, 'https://www.bitporno.com' + catpage, 861, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

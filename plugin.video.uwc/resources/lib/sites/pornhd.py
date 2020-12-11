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
import base64
import json
from resources.lib import utils

@utils.url_dispatcher.register('870')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.pornhd.com/search?search=', 873, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'https://www.pornhd.com/category', 874, '', '')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]', 'https://www.pornhd.com/channel', 875, '', '')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]', 'https://www.pornhd.com/pornstars', 876, '', '')

    List('https://www.pornhd.com/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('871', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except urllib2.HTTPError as e:
        if '?search' in url:
            utils.notify(url.split('=')[-1], 'No results!')
        else:
            utils.notify('No results!')
        return None

    match = re.compile('div class="video-item.+?href="(.+?)".+?alt="(.+?)".+?src="(.+?)".+?duration">(.+?)</span>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        if '/cnnct/' in videopage: continue
        videopage = 'https://www.pornhd.com' + videopage if not videopage.startswith('https') else videopage
        utils.addDownLink('[COLOR hotpink]' + duration.strip() + '[/COLOR] ' + utils.cleantext(name), videopage, 872, img, '')
    try:
        nextp = re.compile('<span class="pagination-link is-current".+?href="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0].replace('&amp;', '&')
        utils.addDir('Next Page (' + nextp.split('page=')[1] + ')', nextp, 871, '')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('872', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    try:
        listhtml = utils.getHtml(url, '')
    except urllib2.HTTPError as e:
        utils.notify(name, e)
        return None
    except:
        return None
    videoArray = re.compile('source src="(.+?)".+?label=\'(.+?)\'', re.DOTALL | re.IGNORECASE).findall(listhtml)
    choice = xbmcgui.Dialog().select('Select resolution', [item[1] for item in videoArray])
    if choice==-1: return
    video1 = videoArray[choice][0]
    if 'pornhdprime' in url:
        videourl = video1.replace('&amp;', '&')
    else:
        videourl = json.loads(base64.b64decode(video1.split('/gvf/')[-1].split('.')[1]))['url']
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'PornHD'})
    if download == 1:
	utils.downloadVideo(videourl, name)
    else:
        xbmc.Player().play(videourl, listitem)


@utils.url_dispatcher.register('873', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 873)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

@utils.url_dispatcher.register('874', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    categ = re.compile('<a href="(/category/.+?)".+?alt="(.+?)".+?src="(.+?)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in categ:
        utils.addDir(name, 'https://www.pornhd.com' + catpage, 871, 'https:' + img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('875', ['url'])
def Channels(url):
    cathtml = utils.getHtml(url, '')
    categ = re.compile('<a href="(https://www\.pornhd\.com/channel/.+?)".+?alt="(.+?)".+?src="(.+?)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in categ:
        utils.addDir(name, catpage, 871, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('876', ['url'])
def Pornstars(url):
    cathtml = utils.getHtml(url, '')
    categ = re.compile('<a href="(/pornstars/.+?)".+?alt="(.+?)".+?src="(.+?)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in categ:
        utils.addDir(name, 'https://www.pornhd.com' + catpage, 871, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)

'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream, hdgdl
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

import urllib2
import re

import xbmc
import xbmcplugin
import xbmcgui
import base64
from resources.lib import utils

@utils.url_dispatcher.register('610')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://daftsex.com/categories',614,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://daftsex.com/video/',613,'','')
    utils.addDir('[COLOR red]Random TV[/COLOR]','https://daftsex.com/',615,'','')
    List('https://daftsex.com/hot')


@utils.url_dispatcher.register('611', ['url'], ['page'])
def List(url, page=0):
    try:
        postRequest = {'page' : str(page)}
        response = utils.postHtml(url, form_data=postRequest,headers={},compression=False)
    except:
        return None
    match = re.compile('<div class="video-item">.*?a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)".*?<span class="video-time">([^<]+)', re.DOTALL | re.IGNORECASE).findall(response)
    for video, img, name, length in match:
        video = 'https://daftsex.com' + video
        name = '[COLOR hotpink]' + length + '[/COLOR] ' + utils.cleantext(name)
        utils.addDownLink(name, video, 612, img, '')
    npage = page + 1
    utils.addDir('Next Page (' + str(npage) + ')', url, 611, '', npage)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('612', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download = download)
    vp.progress.update(25, "", "Loading video page", "")
    vidsite = utils.getHtml(url, 'https://daftsex.com/')

    videourl = re.compile('<iframe.+?src="(https://da{0,1}xa{0,1}b\.[ct]om{0,1}/[^"]+)"', re.DOTALL | re.IGNORECASE).findall(vidsite)[0]
    videopage = utils.getHtml(videourl, 'https://daftsex.com/')
    if utils.addon.getSetting('daftsexresolver') == '0':
        server =''
        try:	
            match = re.compile('id: "([^"]+)_([^"]+)".+:"(\d+)\.([^"]+)"}.+?server:\s*?"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
            (id1, id2, res, extra, server) =  match
            s = list(server)
            s.reverse()
            server = base64.b64decode(str(''.join(s)))
            video =  'https://' + server + '/videos/' + id1 + '/' + id2 + '/' + res + '.mp4?extra=' + extra
            vp.play_from_direct_link(video)
            return
        except:
            pass
    video = 'https://vk.com/video' + re.compile("Fav.Toggle\(this, '([^']+)'", re.DOTALL | re.IGNORECASE).findall(vidsite)[0]
    vp.play_from_link_to_resolve(video)

@utils.url_dispatcher.register('613', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    xbmc.log("Search: " + searchUrl)
    if not keyword:
        utils.searchDir(url, 613)
    else:
        title = keyword.replace(' ','_')
        searchUrl = searchUrl + title
        xbmc.log("Search: " + searchUrl)
        List(searchUrl)

@utils.url_dispatcher.register('614', ['url'])
def Categories(url):
    response = utils.getHtml(url, 'https://daftsex.com/')
    match = re.compile('<div class="video-item">.*?a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(response)
    for caturl, img, name in sorted(match, key=lambda x: x[2]):
        caturl = 'https://daftsex.com' + caturl
        img = 'https://daftsex.com' + img
        utils.addDir(name, caturl, 611, img, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('615', ['url'])
def Random(url):
    response = utils.getHtml(url, 'https://daftsex.com/')
    match = re.compile('title="RandomTV" href="([^"]+)" class="randomQuery"', re.DOTALL | re.IGNORECASE).findall(response)
    title = match[0].replace('/video/','')
    utils.addDir('[COLOR red]' + title + '[/COLOR]', url, 615,'','')
    List('https://daftsex.com' + match[0])
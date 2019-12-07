'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream
    Copyright (C) 2016 anton40

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
  

@utils.url_dispatcher.register('410')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://xxxstreams.eu/',413,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://xxxstreams.eu/?s=',414,'','')
    List('http://xxxstreams.eu/page/1')


@utils.url_dispatcher.register('411', ['url'])
def List(url):
    try:
        html = utils.getHtml(url, '')
    except:
       
        return None
    match = re.compile(r'data-id="\d+" title="([^"]+)" href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for name, videopage, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 412, img, '')
    try:
        next_page = re.compile('rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 411,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('412', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    utils.PLAYVIDEO(url, name, download)


@utils.url_dispatcher.register('413', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<li.+?class=".+?menu-item-object-post_tag.+?"><a href="(.+?)">(.+?)</a></li>').findall(cathtml)
    for catpage, name in match:
        utils.addDir(name, catpage, 411, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('414', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 414)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


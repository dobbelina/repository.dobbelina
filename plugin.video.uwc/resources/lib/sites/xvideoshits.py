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
import xbmc
from resources.lib import utils

    
@utils.url_dispatcher.register('700')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://www.xvideoshits.com/networks/',703,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.xvideoshits.com/search/',704,'','')
    List('https://www.xvideoshits.com/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('701', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="thumb.*?href="([^"]+)".*?title="([^"]+)".*?" data-original="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)

    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 702, img, '')
    try:
#        nextp = re.compile('link rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
#        utils.addDir('Next Page', nextp[0], 701,'')             #[^']+\bmiddle\b|\bnext\b
	match = re.compile("a href='([^']+)' class='page-numbers [^']+'>([^<]+)<", re.DOTALL | re.IGNORECASE).findall(listhtml)
        for pageurl, page in match:
            utils.addDir('[COLOR deeppink]Page ' + str(page) + '[/COLOR]', pageurl, 701, '')

    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('702', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, '<iframe src="([^"]+)"')
    vp.progress.update(25, "", "Loading video page", "")
    html = utils.getHtml(url, url)
    html = html.replace('oload.website', 'oload.stream')
    vp.play_from_html(html)  


@utils.url_dispatcher.register('703', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('class="thumbInside".*?href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?alt="([^"]+)".*?>(\d+) Videos<', re.DOTALL | re.IGNORECASE).findall(cathtml)
 

    for catpage, name, img, alt, count in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip()) + " [COLOR deeppink]" + count.strip() + " videos[/COLOR]   "
        utils.addDir(name, catpage, 701, img, 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('704', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 704)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


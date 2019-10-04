'''
    Ultimate Whitecream
    Copyright (C) 2018 Whitecream, Fr33m1nd, holisticdioxide

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

import urllib
import re
import os.path

import xbmcplugin
from resources.lib import utils
progress = utils.progress

siteurl = 'http://www.viralvideosx.com/'


@utils.url_dispatcher.register('760')
def EXMain():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl, 763,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', siteurl + 'buscar-', 764,'','')
    EXList(siteurl)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('761', ['url'])
def EXList(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
        
    match = re.compile('<img src="([^"]+)" class="imagenes">.+?title="([^"]+)".*?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, videopage in match:
        img = 'http:'+img if img.startswith('//') else img
        videopage = 'http:'+videopage if videopage.startswith('//') else videopage
        utils.addDownLink(utils.cleantext(name), videopage, 762, img, '')
    try:
	(next_page, page_nr)  = re.compile("<li class=.float-xs-right.><a href='([^']+)' title='Pagina (\d+)'><span class", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        if not next_page.startswith('http'):
            next_page = 'http:' + next_page
        utils.addDir('Page #' + page_nr, next_page, 761,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('764', ['url'], ['keyword'])      
def EXSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 764)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title + ".html"
        EXList(searchUrl)


@utils.url_dispatcher.register('763', ['url'])
def EXCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="([^"]+\/categoria\/[^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        catpage = 'https:' + catpage
        utils.addDir(utils.cleantext(name), catpage, 761, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('762', ['url', 'name'], ['download'])
def EXPlayvid(url, name, download=None):
    regex = '''(?:iframe|IFRAME).*?(?:src|SRC)=['"](http[^"']+)'''
    url = 'http:'+url if url.startswith('//') else url
    #
    vp = utils.VideoPlayer(name, download, regex=regex)
    vp.progress.update(25, "", "Loading video page", "")
    
    videopage = utils.getHtml(url, '')
    links = re.compile(regex, re.DOTALL | re.IGNORECASE).findall(videopage)
    utils.kodilog(links)
    for link in links:
        if link.endswith('.jpg'):
            continue
        if link.endswith('.png'):
            continue
        if link.endswith('.js'):
            continue
        try:
            videopage += utils.getHtml(link, url)
        except:
            pass
    vp.play_from_html(videopage)

@utils.url_dispatcher.register('767', ['url'])
def EXMoviesList(url):
    url = 'https:'+url if url.startswith('//') else url
    listhtml = utils.getHtml(url, '')
    match = re.compile('<div class="container_neus">(.*?)<div id="pagination">', re.DOTALL | re.IGNORECASE).findall(listhtml)
    match1 = re.compile('<a title="([^"]+)" href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(match[0])
    for name, videopage, img in match1:  
        img = 'https:'+img if img.startswith('//') else img
        utils.addDownLink(name, videopage, 762, img, '')
    try:
        nextp=re.compile("<a href='([^']+)' title='([^']+)'>&raquo;</a>", re.DOTALL | re.IGNORECASE).findall(listhtml)
        next = urllib.quote_plus(nextp[0][0])
        next = next.replace(' ','+')
        utils.addDir('Next Page', os.path.split(url)[0] + '/' + next, 767,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

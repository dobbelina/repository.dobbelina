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

siteurl = 'http://www.viralvideosporno.com/'


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
    match = re.compile('class="notice".+?href="([^"]+)">([^<]+).+?img src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        for videopage, name, img in match:
            img = 'http:'+img if img.startswith('//') else img
            videopage = 'http:'+videopage if videopage.startswith('//') else videopage
            name = utils.cleantext(name)
            name = re.sub(r'(HD .+)$', r'[COLOR orange]\1[/COLOR]', name)
            utils.addDownLink(name, videopage, 762, img, '')
    else:
        match = re.compile('class="portada.+?href="([^"]+)".+?img src="([^"]+)".+?class="titles">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
        for videopage, img, name in match:
            img = 'http:'+img if img.startswith('//') else img
            videopage = 'http:'+videopage if videopage.startswith('//') else videopage
            name = utils.cleantext(name)
            utils.addDownLink(name, videopage, 762, img, '')
    try:
	(next_page, page_nr)  = re.compile("a href='([^']+/(\d+)/??)'[^<]+<span class=\"visible-xs-inline\">Siguiente<", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        next_page = 'http:' + next_page if next_page.startswith('//') else next_page
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
    match = re.compile('href="([^"]+\/categoria\/[^"]+)"[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        catpage = 'http:' + catpage
        utils.addDir(utils.cleantext(name), catpage, 761, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('762', ['url', 'name'], ['download'])
def EXPlayvid(url, name, download=None):
    url = 'http:'+url if url.startswith('//') else url
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url, '')
    regex = '''(?:iframe|IFRAME).*?(?:src|SRC)=['"](http[^"']+)'''
    links = re.compile(regex, re.DOTALL | re.IGNORECASE).findall(videopage)
    links1 = re.compile('<b>([^<]+)...</b>', re.DOTALL | re.IGNORECASE).findall(videopage)
    links += links1
    select = {}
    for link in links:
        if vp.resolveurl.HostedMediaFile(link):
            select[link.split('/')[2]] = link
    videourl = utils.selector('Select link', select)
    vp.play_from_link_to_resolve(videourl)


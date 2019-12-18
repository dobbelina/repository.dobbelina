'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 Fr33m1nd

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


@utils.url_dispatcher.register('170')
def Main():
#    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://streamxxx.tv/', 177, '', '')
    utils.addDir('[COLOR hotpink]Tags[/COLOR]','http://streamxxx.tv/top-tags/', 173, '', '')
    utils.addDir('[COLOR hotpink]Movies[/COLOR]','http://streamxxx.tv/category/movies-xxx/', 175, '', '')
    utils.addDir('[COLOR hotpink]International Movies[/COLOR]','http://streamxxx.tv/category/movies-xxx/international-movies/', 176, '', '')
    utils.addDir('[COLOR hotpink]Search Overall[/COLOR]','http://streamxxx.tv/?s=', 174, '', '')
    utils.addDir('[COLOR hotpink]Search Scenes[/COLOR]','http://streamxxx.tv/?cat=5562&s=', 174, '', '')
    List('http://streamxxx.tv/category/clips/')


@utils.url_dispatcher.register('175')
def MainMovies():
    List('http://streamxxx.tv/category/movies-xxx/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('176')
def MainInternationalMovies():
    List('http://streamxxx.tv/category/movies/international-movies/')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('171', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, url)
    except:
        return None
    listhtml = listhtml.split('>Next<')[0] + '>Next<'
    match = re.compile('href=(https://streamxxx\S+)\s+title="([^"]+)".+?img src=(\S+)\s', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 172, img, '')
    try:
        next_page = re.compile('class="next page-numbers" href=([\S]+)\s*>Next', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        next_page = next_page.replace('&#038;','&')
        next_page = next_page.replace('"','')
        page_nr = re.findall('\d+', next_page.replace('cat=5562',''))[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 171,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('174', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 174)
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('177', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile("Clips</a>(.*)</ul>", re.DOTALL | re.IGNORECASE).findall(cathtml)
    match1 = re.compile('href="(/[^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
    for catpage, name in match1:
        catpage = 'http://streamxxx.tv' + catpage
        utils.addDir(name, catpage, 171, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('173', ['url'])
def Tags(url):
    html = utils.getHtml(url, '')
    html = html.replace('><','')
    match1 = re.compile('href=(\S+tv/tag/\S+)\s[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(html)
    for catpage, name in match1:
        utils.addDir(name, catpage, 171, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('172', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    videourls = re.compile('a href=(\S+)\s[^>]+>[^<]+</a>', re.DOTALL | re.IGNORECASE).findall(videopage)
    links = {}
    for link in videourls:
        if vp.resolveurl.HostedMediaFile(link):
            links[link.split('/')[2]] = link
    videourl = utils.selector('Select link', links, dont_ask_valid=False)
    vp.play_from_link_to_resolve(videourl)



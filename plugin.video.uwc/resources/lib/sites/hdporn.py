'''
    Ultimate Whitecream
    Copyright (C) 2018 Whitecream, holisticdioxide

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

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils
 
progress = utils.progress


@utils.url_dispatcher.register('60')
def PAQMain():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.pornaq.net/categories/',63,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.pornaq.net/s/',68,'','')
    PAQList('http://www.pornaq.net',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('64')
def P00Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.porn00.org/categories/',63,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.porn00.org/page/1/?s=',68,'','')
    PAQList('http://www.porn00.org/page/1/',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)    


@utils.url_dispatcher.register('61', ['url'], ['page'])
def PAQList(url, page=1, onelist=None):
    if onelist:
        url = url.replace('page/1/','page/'+str(page)+'/')
    try:
        listhtml = utils.getHtml(url, '')
    except:
        pass
        return None
    match = re.compile('class="post-con">.*?<a title="([^"]+)".*?href="([^"]+)".*?src="([^"]+)" class="attachment', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, videopage, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 62, img, '')    
    if not onelist:
        try:
            nextp=re.compile("title='Next page' href='([^']+)'", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
            page_nr = re.findall('\d+', nextp)[-1]
            utils.addDir('Next Page (' + page_nr + ')', nextp, 61,'')
        except:
            pass
        xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('62', ['url', 'name'], ['download'])
def PPlayvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    if 'porn00' in url:
        alternatives = re.compile('div id="alternatives".+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
        for alternative in alternatives:
            videopage += utils.getHtml(alternative)
        links = {}    
        videolinks = re.compile('iframe.+?src="([^"]+)" width', re.DOTALL | re.IGNORECASE).findall(videopage)
        for link in videolinks:
            if vp.resolveurl.HostedMediaFile(link) and 'www.porn00.org' not in link:
                links[link.split('/')[2]] = link
            if 'www.porn00.org/player/' in link:
                html = utils.getHtml(link)
                srcs = re.compile('''<source src='([^']+)' title="([^"]+)"''', re.DOTALL | re.IGNORECASE).findall(html)
                for (vlink, title) in srcs:
                    links['direct ' + title] = vlink + '|Referer=' + link
        videourl = utils.selector('Select link', links, dont_ask_valid=False, reverse=True)
        vp.progress.update(75, "", "Loading video page", "")    
        if '|Referer' in videourl:
            vp.play_from_direct_link(videourl)
        else:
            vp.play_from_link_to_resolve(videourl)
    if 'pornaq' in url:
        videourl = re.compile("<source src='([^']+)' title", re.DOTALL | re.IGNORECASE).findall(videopage)[0]
        vp.play_from_direct_link(videourl + '|Referer=' + url)


@utils.url_dispatcher.register('63', ['url'])
def PCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a title="([^"]+)" href="([^"]+)".+?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for name, videolist, img in match:
        name = name.replace(' Porn Videos','').title()
        if 'pornaq' in url:
            videolist = "http://www.pornaq.net" + videolist + "videos/1/"
            utils.addDir(name, videolist, 61, img, 1)
        elif 'porn00' in url:
            videolist = "http://www.porn00.org" + videolist + "page/1/"
            utils.addDir(name, videolist, 61, img, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('68', ['url'], ['keyword'])
def PSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 68)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        PAQList(searchUrl, 1)

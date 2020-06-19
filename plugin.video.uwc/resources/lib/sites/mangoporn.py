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
import base64
from resources.lib import utils
import xbmc
import xbmcplugin
import xbmcgui
import sys
import urllib2,urllib
@utils.url_dispatcher.register('800')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'https://mangoporn.net/', 803, '', '')
    utils.addDir('[COLOR hotpink]Years[/COLOR]', 'https://mangoporn.net/', 804, '', '')
    utils.addDir('[COLOR hotpink]Studios[/COLOR]', 'https://mangoporn.net/', 805, '', '')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]', 'https://mangoporn.net/', 806, '', '')    
    utils.addDir('[COLOR hotpink]Search[/COLOR]', 'https://mangoporn.net/?s=', 807, '', '') 
    List('https://mangoporn.net/genres/featured-movies/')


@utils.url_dispatcher.register('801', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('<article.+?img src="([^"]+)" alt="([^"]+)".+?a href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, name, videopage in match:
        name = utils.cleantext(name) #+ "[COLOR hotpink] (" + str(year) + ")[/COLOR]"
        utils.addDownLink(name, videopage, 802, img, '')
    try:
        next_page = re.compile('link rel="next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + str(page_nr) + ')', next_page, 801, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


def url_decode(str):
    if '/goto/' not in str:
        result = str
    else:
        try:
            result = url_decode(base64.b64decode(re.search('/goto/(.+)', str).group(1)))
        except:
            result = str
    return result 

@utils.url_dispatcher.register('802', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    html = utils.getHtml(url)
#    html = re.compile('<center><!-- Display player -->(.+?)<center>', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    srcs = re.compile('<a title="([^"]+)" href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for title, src in srcs:
        title = title.replace(name.split("[",1)[0],'').replace(' on','')
        if '/goto/' in src:
            src = url_decode(src)
        if vp.resolveurl.HostedMediaFile(src):
            links[title] = src
        if 'mangovideo' in src:
            title = title.replace(' - ','')
            html = utils.getHtml(src)
            match = re.compile("video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)[0]
            links[title] = match
    videourl = utils.selector('Select server', links, dont_ask_valid=False, reverse=True)
    if not videourl:
        return
    vp.progress.update(90, "", "Loading video page", "")
    if 'mango' in videourl:
        vp.direct_regex = '(' + re.escape(videourl) + ')'
        vp.play_from_html(html)
    else:
        vp.play_from_link_to_resolve(videourl)



@utils.url_dispatcher.register('803', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="(https://mangoporn.net/genres/[^"]+)">([^<]+)</a> <i>([^<]+)</i>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, count in match:
        name = utils.cleantext(name) + "[COLOR hotpink] (" + count + ")[/COLOR]"
        utils.addDir(name, catpage, 801, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('804', ['url'])
def Years(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="(https://mangoporn.net/year/[^"]+)">(\d+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 801, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)    

@utils.url_dispatcher.register('805', ['url'])
def Studio(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('a href="(https://mangoporn.net/adult/studios/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 801, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)    
    
@utils.url_dispatcher.register('806', ['url'])
def Pornstars(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('a href="(https://mangoporn.net/adult/pornstar/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        name = utils.cleantext(name)
        utils.addDir(name, catpage, 801, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)    
    
@utils.url_dispatcher.register('807', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 807)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

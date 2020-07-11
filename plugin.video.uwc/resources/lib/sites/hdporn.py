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


@utils.url_dispatcher.register('64')
def P00Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://www.porn00.org/categories/',63,'','')
    utils.addDir('[COLOR hotpink]Top Rated[/COLOR]','https://www.porn00.org/top-rated/',61,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://www.porn00.org/search/',68,'','')
    PAQList('https://www.porn00.org/page/1/',1)
    xbmcplugin.endOfDirectory(utils.addon_handle)    


@utils.url_dispatcher.register('61', ['url'], ['page'])
def PAQList(url, page=1, onelist=None):
    listhtml = utils.getHtml(url, '')
    match = re.compile('<div class="item  ".*?href="([^"]+)" title="([^"]+)".+?data-original="([^"]+)".+?class="duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, duration in match:
        duration = duration.strip()
        name = utils.cleantext(name) + " [COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, videopage, 62, img, '')    
    if not onelist:
        try:
            nextp=re.compile('class="next"><a href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml).group(1)
            if nextp.startswith('/'): nextp = 'https://www.porn00.org' + nextp
            page_nr = re.findall('\d+', nextp)[-1]
            utils.addDir('Next Page (' + page_nr + ')', nextp, 61,'')
        except:
            pass
        xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('62', ['url', 'name'], ['download'])
def PPlayvid(url, name, download=None):
 #   vp = utils.VideoPlayer(name, download)
 #   vp.progress.update(25, "", "Loading video page", "")
 #   videopage = utils.getHtml(url)
 #   if 'porn00' in url:
 #       alternatives = re.compile('div id="alternatives".+?href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
 #       for alternative in alternatives:
 #           videopage += utils.getHtml(alternative)
 #       links = {}    
 #       videolinks = re.compile('iframe.+?src="([^"]+)" width', re.DOTALL | re.IGNORECASE).findall(videopage)
 #       for link in videolinks:
 #           if vp.resolveurl.HostedMediaFile(link) and 'www.porn00.org' not in link:
 #               links[link.split('/')[2]] = link
 #           if 'www.porn00.org/get_file/' in link:
 #               html = utils.getHtml(link)
 #               srcs = re.compile('''<src='([^']+)' title="([^"]+)"''', re.DOTALL | re.IGNORECASE).findall(html)
 #               for (vlink, title) in srcs:
 #                   links['direct ' + title] = vlink + '|Referer=' + link
 #       videourl = utils.selector('Select link', links, dont_ask_valid=False, reverse=True)
 #      vp.progress.update(75, "", "Loading video page", "")    
    vp = utils.VideoPlayer(name, download,'', "video_alt_url: '([^']+)'")
    videohtml = utils.getHtml(url)
    vp.play_from_html(videohtml)


@utils.url_dispatcher.register('63', ['url'])
def PCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a class="item".*?href="([^"]+)" title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for videolist, name, in match:
        videolist = videolist + "/1/"
        utils.addDir(name, videolist, 61, '', 1)
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

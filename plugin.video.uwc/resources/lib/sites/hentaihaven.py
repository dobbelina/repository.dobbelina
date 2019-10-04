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
@utils.url_dispatcher.register('460')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'http://hentaihaven.org/pick-your-poison/', 463, '', '')
    utils.addDir('[COLOR hotpink]A to Z[/COLOR]', 'http://hentaihaven.org/pick-your-series/', 464, '', '')
    utils.addDir('[COLOR hotpink]Uncensored[/COLOR]', 'http://hentaihaven.org/ajax.php?action=pukka_infinite_scroll&page_no=1&grid_params=infinite_scroll=on&infinite_page=2&infinite_more=true&current_page=taxonomy&front_page_cats=&inner_grid%5Buse_inner_grid%5D=on&inner_grid%5Btax%5D=post_tag&inner_grid%5Bterm_id%5D=53&inner_grid%5Bdate%5D=&search_query=&tdo_tag=uncensored&sort=date', 461, '', '')
    List('http://hentaihaven.org/ajax.php?action=pukka_infinite_scroll&page_no=1&grid_params=infinite_scroll=on')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('461', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    listhtml = listhtml.replace('\\','')
    match1 = re.compile('<a\s+class="thumbnail-image" href="([^"]+)".*?data-src="([^"]+)"(.*?)<h3>[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, other, name in match1:
        name = utils.cleantext(name)
        if 'uncensored' in other:
            name = name + " [COLOR orange]Uncensored[/COLOR]"        
        utils.addDownLink(name, videopage, 462, img, '')
    try:
        page = re.compile('page_no=(\d+)', re.DOTALL | re.IGNORECASE).findall(url)[0]
        page = int(page)
        npage = page + 1
        maxpages = re.compile(r'max_num_pages":(\d+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        if int(maxpages) > page:
            nextp = url.replace("no="+str(page),"no="+str(npage))
            utils.addDir('Next Page ('+str(npage)+')', nextp,461,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('462', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    links = {}
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    iframes = re.compile('<iframe.+?src="([^"]+)"[^>]+>.*?</iframe', re.DOTALL | re.IGNORECASE).findall(videopage)
    if iframes:
        for link in iframes:
            if vp.resolveurl.HostedMediaFile(link):
                links[link.split('/')[2]] = link
    srcs = re.compile('label="([^"]+)" src="([^"]+)" type=', re.DOTALL | re.IGNORECASE).findall(videopage)
    if srcs:
        for quality, videourl in srcs:
            links['Direct ' + quality] = videourl + '|Referer=%s&User-Agent=%s' % (url, utils.USER_AGENT)

    videourl = utils.selector('Select link', links, dont_ask_valid=False)
    if '|Referer' in videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)


@utils.url_dispatcher.register('463', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('/tag/([^/]+)/" cla[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        catpage = "http://hentaihaven.org/ajax.php?action=pukka_infinite_scroll&page_no=1&grid_params=infinite_scroll=on&infinite_page=2&infinite_more=true&current_page=taxonomy&front_page_cats=&inner_grid%5Buse_inner_grid%5D=on&inner_grid%5Btax%5D=post_tag&inner_grid%5Bterm_id%5D=53&inner_grid%5Bdate%5D=&search_query=&tdo_tag=" + catpage + "&sort=date" 
        utils.addDir(name, catpage, 461, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('464', ['url'])
def A2Z(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile(r'class="cat_section"><a\s+href="([^"]+)"[^>]+>([^<]+)<.*?src="([^"]+)"(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, other in match:
        if 'uncensored' in other:
            name = name + " [COLOR hotpink]Uncensored[/COLOR]"
        utils.addDir(name, catpage, 461, img)    
    xbmcplugin.endOfDirectory(utils.addon_handle)

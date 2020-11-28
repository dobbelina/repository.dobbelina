'''
    Ultimate Whitecream
    Copyright (C) 2020 Whitecream, m-incognito

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
from random import randint

import xbmc
import xbmcplugin
import xbmcgui
import requests
from resources.lib import utils

def get_content(url):
    if(url.startswith('/')):
        url = 'https://freevideo.cz' + url

    if(url.startswith('https://freevideo.cz')):
        page_content = utils.getHtml(url)

        # The page is only available from the Czech Republic. Use a free czech proxy if page is not displayed correctly
        if(re.compile('item--external-button', re.DOTALL | re.IGNORECASE).search(page_content)):
            katedrala_page = requests.get('https://www.katedrala.cz/').text

            match = re.compile('<form name="URLform" action="(.*?)"', re.DOTALL | re.IGNORECASE).search(katedrala_page)

            if(match):
                post_action = match.group(1)

                return utils.getHtml(post_action, data={ "URL": url })
        else:
            return page_content
    else:
        return utils.getHtml(url)

@utils.url_dispatcher.register('960')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'https://freevideo.cz/vase-videa/kategorie/', 963, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', 'https://freevideo.cz/vase-videa/vyhledavani/', 964, '', '')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]', 'https://www.adultempire.com/hottest-pornstars.html?pageSize=300&fq=ag_cast_gender%3aF', 965, '', '')
    List('https://freevideo.cz/vase-videa/nejnovejsi/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('961', ['url'])
def List(url):
    listhtml = get_content(url)

    if(re.search('<div class="no-search-results">', listhtml, re.DOTALL | re.IGNORECASE)):
        xbmcplugin.endOfDirectory(utils.addon_handle)
        return

    match = re.compile('class="video video-preview".*?'
    '<a href="([^"]+)".*?'
    'image_ultra_2x="([^"]+)".*?'
    'duration">.*?([\w:]+).*?'
    '(?:quality">.*?(\w+).*?)?'
    '<h5 class="video__description">([^<]+)', 
    re.DOTALL | re.IGNORECASE).findall(listhtml)

    for videopage, img, duration, quality, name in match:
        name = utils.cleantext(name)

        if(quality):
            quality = "[COLOR orange]" + quality + "[/COLOR] "

        name = name + " " + quality + "[COLOR deeppink]" + duration + "[/COLOR]"

        utils.addDownLink(name, videopage, 962, img, '')
    
    match = re.compile('<a href="([^"]+)" class="pagination__next">', re.DOTALL | re.IGNORECASE).search(listhtml)
    if(match):
        utils.addDir('Next Page', match.group(1), 961, '', 1)
    
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('962', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    vp.progress.update(33, "", "Loading video page", "")

    videopage = get_content(url)
    match = re.compile('<source src="([^"]+)".*?label="(\w+)"', re.DOTALL | re.IGNORECASE).findall(videopage)

    sources = {}
    for src, quality in match:
        sources[quality] = src
        print(src)

    videourl = utils.selector('Select quality', sources, dont_ask_valid=True, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)

    if not videourl:
        return

    vp.progress.update(66, "", "Starting the video", "")
    vp.play_from_direct_link(videourl)

@utils.url_dispatcher.register('963', ['url'])
def Cat(url):
    cathtml = get_content(url)

    match = re.compile('<a href="([^"]+)" class="category">.*?'
    'data-original="([^"]+)".*?'
    'category__description">(.*?)</h5>', 
    re.DOTALL | re.IGNORECASE).findall(cathtml)
    
    for videopage, img, name in match:
        utils.addDir(name, videopage, 961, img, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('964', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 964)
    else:
        searchUrl = searchUrl + '?q=' + keyword + '/'
        List(searchUrl)

@utils.url_dispatcher.register('965', ['url'])
def Pornstars(url):
    listhtml = get_content(url)

    match = re.compile('Label="([^"]+)"><picture>.*?min-width: 1600px.*?srcset="([^"]+)"', 
    re.DOTALL | re.IGNORECASE).findall(listhtml)
    
    for name, img in match:
        formattedName = name.lower().replace(' ', '-')
        utils.addDir(name, 'https://freevideo.cz/vase-videa/kategorie/' + formattedName, 961, img, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)
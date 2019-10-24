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
from resources.lib import utils

siteurl = 'https://herexxx.com'

@utils.url_dispatcher.register('530')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl,533,'','')
    utils.addDir('[COLOR hotpink]Lists[/COLOR]',siteurl,534,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/search/video/?s=',535,'','')
    List(siteurl + '/videos/')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('531', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
        
    match = re.compile('class="video".+?href="([^"]+)"\s*title="([^"]+)".+?src="([^"]+)".+?class="duration"><strong>([^<]+)<\/strong>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img, hd, duration in match:
        name = utils.cleantext(name) + "[COLOR orange] " + hd + "[COLOR deeppink] " +  duration + "[/COLOR]"
        if not img.startswith("http"): img = siteurl + img
        if not videopage.startswith("http"): videopage = siteurl + videopage
        utils.addDownLink(name, videopage, 532, img, '')
    try:
        nextp, page = re.compile('href="([^"]+\D(\d+)/??)" class="prevnext" title="Go to next page!"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Next Page (' + page +')', siteurl + nextp, 531,'')
        
#        <a href="/search/video/?s=dance&page=2" class="prevnext" title="Go to next page!">
        
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('532', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, 'source src="([^"]+)"')
    vp.play_from_site_link(url)


@utils.url_dispatcher.register('533', ['url'])
def SelectCat(url):
    cats = {}
    cats['Categories - Recent'] = siteurl + '/categories/'
    cats['Categories - Most Popular'] = siteurl + '/categories/?order=popular'
    cats['Categories - No. of Videos'] = siteurl + '/categories/?order=videos'
    cats['Categories - Featured'] = siteurl + '/categories/?order=featured'
    cats['Categories - Alphabetical'] = siteurl + '/categories/?order=alphabetical'
    cats['Playlists - Recent'] = siteurl + '/playlists/recent/'
    cats['Playlists - Most Viewed'] = siteurl + '/playlists/'
    cats['Playlists - Top Rated'] = siteurl + '/playlists/rated/'
    cats['Playlists - Most Favorited'] = siteurl + '/playlists/favorited/'
    cats['Models - Recent'] = siteurl + '/models/recent/'
    cats['Models - Most Viewed'] = siteurl + '/models/viewed/'
    cats['Models - Most Popular'] = siteurl + '/models/'
    cats['Models - Alphabetical'] = siteurl + '/models/alphabetical/'
    cats['Models - Most Subscribed'] = siteurl + '/models/subscribed/'
    cats['Models - No. of Videos'] = siteurl + '/models/videos/'
    url = utils.selector('Select', cats)
    if not url:
        return
    Cat(url)

@utils.url_dispatcher.register('536', ['url'])
def Cat(url):
    try:
        cathtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('li id=".+?href="([^"]+)" title="([^"]+)".+?src="([^"]+)".+?class="fa fa-video-camera"><\/i>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] " +  count + "[/COLOR]"
        if not img.startswith("http"): img = siteurl + img
        if not catpage.startswith("http"): catpage = siteurl + catpage
        utils.addDir(name, catpage, 531, img)
    try:
        nextp, page = re.compile('href="([^"]+/(\d+)/)" class="prevnext" title="Go to next page!"', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        utils.addDir('Next Page (' + page +')', siteurl + nextp, 536,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('534', ['url'])
def Lists(url):
    lists = {}
    lists['Videos - Recent'] = siteurl + '/videos/'
    lists['Videos - Most Popular'] = siteurl + '/videos/popular/'
    lists['Videos - Most Viewed'] = siteurl + '/videos/viewed/'
    lists['Videos - Top Rated'] = siteurl + '/videos/rated/'
    lists['Videos - Most Favorited'] = siteurl + '/videos/favorited/'
    lists['Chinese - China'] = siteurl + '/videos/china/'
    lists['Chinese - Singapore'] = siteurl + '/videos/singapore/'
    lists['Chinese - Malaysia'] = siteurl + '/videos/malaysia/'
    lists['Chinese - Taiwan'] = siteurl + '/videos/taiwan/'
    lists['Chinese - Hong Kong'] = siteurl + '/videos/hong-kong/'
    lists['Korean - Korean'] = siteurl + '/videos/korean/'
    lists['Korean - Korean Porn'] = siteurl + '/videos/korean-porn/'
    lists['Korean - Korean BJ'] = siteurl + '/videos/korean-bj/'
    lists['Korean - Korean BJ Couple'] = siteurl + '/videos/korean-bj-couple/'
    lists['Korean - Korean BJ Lesbian'] = siteurl + '/videos/korean-bj-lesbian/'
    lists['Korean - Korean BJ Uncensored'] = siteurl + '/videos/korean-bj-uncensored/'
    lists['Japanese - Japanese'] = siteurl + '/videos/japanese/'
    lists['Japanese - JAV Censored'] = siteurl + '/videos/jav-censored/'
    lists['Japanese - JAV Uncensored'] = siteurl + '/videos/jav-uncensored/'
    lists['Japanese - JAV Amateur'] = siteurl + '/videos/jav-amateur/'
    lists['Western'] = siteurl + '/videos/western/'
    lists['Movies - Recent'] = siteurl + '/videos/porn-movies/'
    lists['Movies - Top Rated'] = siteurl + '/videos/porn-movies/rated/'
    lists['Movies - Longest'] = siteurl + '/videos/porn-movies/longest/'
    lists['Professional - Recent'] = siteurl + '/videos/professional/'
    lists['Professional - Top Rated'] = siteurl + '/videos/professional/rated/'
    lists['Professional - Longest'] = siteurl + '/videos/professional/longest/'
    lists['Homemade - Recent'] = siteurl + '/videos/homemade/'
    lists['Homemade - Top Rated'] = siteurl + '/videos/homemade/rated/'
    lists['Homemade - Longest'] = siteurl + '/videos/homemade/longest/'
    url = utils.selector('Select', lists)
    if not url:
        return
    List(url)

@utils.url_dispatcher.register('535', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 535)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


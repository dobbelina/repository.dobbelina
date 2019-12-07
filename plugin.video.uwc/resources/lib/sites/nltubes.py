'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream

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
import sys

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils
import requests

sitelist = ['https://www.poldertube.nl/', 'https://www.12milf.com/', 'https://www.sextube.nl/']


@utils.url_dispatcher.register('100', ['url'], ['page'])
def NLTUBES(url, page=1):
    siteurl = sitelist[page]
    if page == 1:
        utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories/',103,'', page)    
    else:
        utils.addDir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categorieen/',103,'', page)
    utils.addDir('[COLOR hotpink]Search[/COLOR]', siteurl + '?s=',104,'', page)
    NLVIDEOLIST(siteurl + '?filter=latest', page)


@utils.url_dispatcher.register('101', ['url'], ['page'])
def NLVIDEOLIST(url, page=1):
    siteurl = sitelist[page]
    try:
        link = utils.getHtml3(url)
    except:
        return None
    match = re.compile('<article[^"]+"([^"]+)".+?href="([^"]+)".*?src="([^"]+jpg)".*?alt="([^"]+).*?duration">\D*?([\d:]+)\D*?<', re.DOTALL | re.IGNORECASE).findall(link)
    for hd, videourl, img, name, duration in match:
        if 'high_' in hd:
            hd = " [COLOR orange]HD[/COLOR] "
        else:
            hd = " "
        if siteurl not in videourl:
            videourl = siteurl + videourl
        duration2 = "[COLOR deeppink]" +  duration + "[/COLOR]"
        if duration != '1"':
            utils.addDownLink(name + hd + duration2, videourl, 102, img, '')
    try:
        next_page = re.compile('<a href="([^"]+)"[^>]*?>(?:Next|Volgende|VOLGENDE)<', re.DOTALL | re.IGNORECASE).findall(link)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        if siteurl not in next_page: next_pagep = siteurl + next_page
        utils.addDir('Next Page (' + page_nr + ')', next_page, 101,'', page)
    except: pass
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


@utils.url_dispatcher.register('102', ['url', 'name'], ['download'])
def NLPLAYVID(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    headers = dict(utils.headers)
    headers['Cookie'] = 'pageviews=1; postviews=1'
    videopage = utils.getHtml(url, 'https://www.sextube.nl/', hdr=headers)
    videourl = re.compile('<source src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    videourl = videourl[0] + '|Referer=' + url
    vp.progress.update(75, "", "Loading video page", "")
    vp.play_from_direct_link(videourl)


@utils.url_dispatcher.register('104', ['url'], ['page', 'keyword'])
def NLSEARCH(url, page=1, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 104, page)
    else:
        title = keyword.replace(' ','%20')
        searchUrl = searchUrl + title
        NLVIDEOLIST(searchUrl, page)


@utils.url_dispatcher.register('103', ['url'], ['page'])
def NLCAT(url, page=1):
    siteurl = sitelist[page]
    link = utils.getHtml3(url)

    if page == 1:    
        tags = re.compile('href="(https://www.12milf.com/c/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(link)
        for caturl, catname in tags:
            if siteurl not in caturl: caturl = siteurl + caturl
            utils.addDir(catname,caturl,101,'',page)
    else:
        tags = re.compile('<article id=.*?href="([^"]+)" title="([^"]+)">.+?src="([^"]+)" class', re.DOTALL | re.IGNORECASE).findall(link)
        for caturl, catname, catimg in tags:
            if siteurl not in catimg: catimg = siteurl + catimg
            if siteurl not in caturl: caturl = siteurl + caturl
            utils.addDir(catname,caturl,101,catimg,page)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

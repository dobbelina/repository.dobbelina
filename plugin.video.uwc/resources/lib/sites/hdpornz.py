'''
    Ultimate Whitecream
    Copyright (C) 2016-2019 Whitecream and others

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

siteurl = 'https://hdpornz.biz'
    
@utils.url_dispatcher.register('950')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]',siteurl,953,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]',siteurl+'/search/',954,'','')
    List(siteurl)
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('951', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    listhtml = re.compile('<div class="panel panel-default"(.*?)<footer>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile('id=\'media-.*?=.*?<a href=\'([^\']+)\' title=\'([^\']+)\'.*?image:url\((.*?)\)\'', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 952, img, '')
    try:
        nextp = re.compile('<a href="([^"]+)">N.*?chste </a>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        utils.addDir('Next Page', nextp, 951,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('952', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp  = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    vidlink = re.compile('"video-player".*?<iframe src=\'(.*?)\'', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    vp.play_from_site_link(vidlink)


@utils.url_dispatcher.register('953', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    cathtml = re.compile('<ul class=\'categories\'>(.*?)</ul>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    print "CatHTML: " + cathtml
    match = re.compile('href=\'(.*?)\'>(.*?)</a>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in sorted(match, key=lambda x: x[1]):
        name = utils.cleantext(name) 
        utils.addDir(name, catpage, 951, '', 2)    
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('954', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 954)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


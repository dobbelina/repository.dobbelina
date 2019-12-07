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

import re
import urlparse
import xbmcplugin
from resources.lib import utils

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

@utils.url_dispatcher.register('130')
def Main():
#    utils.addDir('[COLOR grey]Tags[/COLOR]','https://www.xn--xvideos-espaol-1nb.com/tags/',133,'','')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.xvideospanish.net/videos-pornos-por-productora-gratis/page/1/',135,'','')
    utils.addDir('[COLOR hotpink]Actors[/COLOR]','https://www.xn--xvideos-espaol-1nb.com/actors/',136,'','')
    utils.addDir('[COLOR hotpink]Longest videos[/COLOR]','https://www.xn--xvideos-espaol-1nb.com/?filter=longest',131)
    utils.addDir('[COLOR hotpink]Most viewed videos[/COLOR]','https://www.xn--xvideos-espaol-1nb.com/?filter=most-viewed',131)
    utils.addDir('[COLOR hotpink]Popular videos[/COLOR]','https://www.xn--xvideos-espaol-1nb.com/?filter=popular',131)
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.xvideospanish.net/?s=',134,'','')
    List('https://www.xn--xvideos-espaol-1nb.com/?filter=latest')



@utils.url_dispatcher.register('131', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    main = re.compile('<main.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    match = re.compile('article id.+?a href="([^"]+)" title="([^"]+)".+?(?:data-src|poster)="([^"]+)"(.+?)</article>', re.DOTALL | re.IGNORECASE).findall(main)
    for videopage, name, img, duration in match:
        if 'fa fa-clock-o' in duration:
            duration = re.compile('fa fa-clock-o"></i> ([^<]+)<', re.DOTALL | re.IGNORECASE).findall(duration)[0]
        else:
            duration = ''
        name = "[COLOR deeppink]" + duration + "[/COLOR] " + utils.cleantext(name)
        uvideopage = unicode(videopage, encoding='utf-8')
        videopage = iriToUri(uvideopage)
        uimg = unicode(img, encoding='utf-8')
        img = iriToUri(uimg)
        utils.addDownLink(name, videopage, 132, img, '')
    try:
        nextp=re.compile('class="current">\d+</a></li><li><a href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        unextp = unicode(nextp, encoding='utf-8')
        nextp = iriToUri(unextp)
        utils.addDir('Next Page', nextp, 131,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('134', ['url'], ['keyword'])    
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 134)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('133', ['url'])
def Tags(url):
    cathtml = utils.getHtml(url, '')
    cathtml = re.compile('<main.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<a href="([^"]+)" class="tag-cloud-link.*?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        ucatpage = unicode(catpage, encoding='utf-8')
        catpage = iriToUri(ucatpage)
        utils.addDir(name, catpage, 131)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('135', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    cathtml = re.compile('<main.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img in match:
        ucatpage = unicode(catpage, encoding='utf-8')
        catpage = iriToUri(ucatpage)
        uimg = unicode(img, encoding='utf-8')
        img = iriToUri(uimg)
        utils.addDir(name, catpage, 131, img,1)
    try:
        nextp=re.compile('<a class="current">.*?<a href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        unextp = unicode(nextp, encoding='utf-8')
        nextp = iriToUri(unextp)
        utils.addDir('Next Page', nextp, 135,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle) 


@utils.url_dispatcher.register('136', ['url'])
def Actors(url):
    cathtml = utils.getHtml(url, '')
    cathtml = re.compile('<main.*?>(.*?)</main>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
    match = re.compile('<a href="([^"]+)" title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        ucatpage = unicode(catpage, encoding='utf-8')
        catpage = iriToUri(ucatpage)
        utils.addDir(name, catpage.strip(), 131,'',1)
    try:
        nextp=re.compile('<a href="([^"]+)">Next</a>', re.DOTALL | re.IGNORECASE).findall(cathtml)[0]
        unextp = unicode(nextp, encoding='utf-8')
        nextp = iriToUri(unextp)
        utils.addDir('Next Page', nextp, 136,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('132', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download = download)
    vp.progress.update(25, "", "Loading video page", "")
    html = utils.getHtml(url)   
    videourl = re.compile('<iframe src="([^"]+)" ', re.DOTALL | re.IGNORECASE).findall(html)[0]
    if '/player/' in videourl:
        videourl = videourl.replace('/player/?data=','')
        videourl = 'https://www.xn--xvideos-espaol-1nb.com/player/getVideo.php?data=' + videourl
     	listjson = utils.getHtml(videourl,'')
        listjson = listjson.replace('\/','/')          
        videourl = re.compile('"videoUrl":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listjson)[0]
        vp.play_from_direct_link(videourl)
    else: 
        if vp.resolveurl.HostedMediaFile(videourl):
            vp.play_from_link_to_resolve(videourl)
        else:
            if 'pornhub' in videourl:
                from resources.lib.sites import pornhub
                videourl = videourl.replace('embed/','view_video.php?viewkey=')
                pornhub.Playvid(videourl,name)
            else:
                utils.kodilog(' ???: ' + videourl)
'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream
    Copyright (C) 2015 Fr40m1nd

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


@utils.url_dispatcher.register('400')
def Main():
    utils.addDir('[COLOR hotpink]Classiques[/COLOR]','http://www.mrsexe.com/classiques/', 401, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.mrsexe.com/?search=', 404, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://www.mrsexe.com/', 403, '', '')
    utils.addDir('[COLOR hotpink]Stars[/COLOR]','http://www.mrsexe.com/filles/', 405, '', '')
    List('http://www.mrsexe.com/')


@utils.url_dispatcher.register('401', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:

        return None
    match = re.compile('thumb-list(.*?)<ul class="right pagination">', re.DOTALL | re.IGNORECASE).findall(listhtml)
    match1 = re.compile(r'<li class="[^"]*">\s<a class="thumbnail" href="([^"]+)">\n<script.+?</script>\n<figure>\n<img  id=".+?" src="([^"]+)".+?/>\n<figcaption>\n<span class="video-icon"><i class="fa fa-play"></i></span>\n<span class="duration"><i class="fa fa-clock-o"></i>([^<]+)</span>\n(.+?)\n', re.DOTALL | re.IGNORECASE).findall(match[0])
    for videopage, img, duration, name in match1:
        if img.startswith('//'): img = 'http:' + img
        name = utils.cleantext(name) + ' [COLOR deeppink]' + duration + '[/COLOR]'
        utils.addDownLink(name, 'http://www.mrsexe.com' + videopage, 402, img, '')
    try:
        next_page=re.compile(r'<li class="arrow"><a href="(.+?)">suivant').findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', 'http://www.mrsexe.com/' + next_page, 401,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('404', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 404)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        print "Searching URL: " + searchUrl
        List(searchUrl)


@utils.url_dispatcher.register('403', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('value="(/cat[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        utils.addDir(name, 'http://www.mrsexe.com' + catpage, 401, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('405', ['url'])
def Stars(url):
    print "mrsexe::Stars " + url
    starhtml = utils.getHtml(url, '')
    match = re.compile(r'<h3 class="filles">Les filles de MrSexe</h3>(.*?)<ul class="right pagination">', re.DOTALL | re.IGNORECASE).findall(starhtml)
    match1 = re.compile(r'<figure>\s*<a href="(.+?)"><img src="(.+?)" alt="".+?</figure>.+?class="infos".+?a href=".+?">([^<]+)</a></h5>\s*([0-9]+) vid', re.DOTALL | re.IGNORECASE).findall(match[0])
    for starpage, img, name, vidcount in match1:
        img = 'https:' + img
        name = name + " (" + vidcount + " Videos)"
        utils.addDir(name, 'http://www.mrsexe.com/' + starpage, 401, img)
    try:
        next_page=re.compile(r'<li class="arrow"><a href="(.+?)">suivant').findall(starhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', 'http://www.mrsexe.com/' + next_page, 405,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('402', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    html = utils.getHtml(url, '')
    videourl = re.compile(r"src='(/inc/clic\.php\?video=.+?&cat=mrsex.+?)'").findall(html)
    html = utils.getHtml('http://www.mrsexe.com/' + videourl[0], '')
    videourls = re.compile(r"""['"](htt.+?.mp4)['"]""").findall(html)
    output = []
    for videourl in videourls:
        link='Link'
        output.append([videourl, link])
    videourls = sorted(output, key=lambda tup: tup[1], reverse=True)
    videourl = videourls[0][0]
    if videourl.startswith('//'): videourl = 'http:' + videourl
    if download == 1:
        utils.downloadVideo(videourl, name)
    else:
        iconimage = xbmc.getInfoImage("ListItem.Thumb")
        listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        listitem.setInfo('video', {'Title': name, 'Genre': 'Porn'})
        xbmc.Player().play(videourl, listitem)
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
import requests
import json

import xbmc, xbmcplugin, xbmcgui
from resources.lib import utils
progress = utils.progress


@utils.url_dispatcher.register('310')
def Main():
    utils.addDir('[COLOR hotpink]JAV Uncensored[/COLOR]','https://javhoho.com/category/free-jav-uncensored/',311,'','')
    utils.addDir('[COLOR hotpink]JAV Censored[/COLOR]','https://javhoho.com/category/free-jav-censored/',311,'','')
    utils.addDir('[COLOR hotpink]Chinese Porn[/COLOR]','https://javhoho.com/category/free-chinese-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Korean Porn[/COLOR]','https://javhoho.com/category/free-korean-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Asian Porn[/COLOR]','https://javhoho.com/category/free-asian-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Thailand Porn[/COLOR]','https://javhoho.com/category/free-thailand-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Philippines Porn[/COLOR]','https://javhoho.com/category/free-philippines-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Malaysian Porn[/COLOR]','https://javhoho.com/category/free-malaysian-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Vietnamese Porn[/COLOR]','https://javhoho.com/category/free-vietnamese-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Cambodia Porn[/COLOR]','https://javhoho.com/category/free-cambodia-porn/',311,'','')
    utils.addDir('[COLOR hotpink]HongKong Porn[/COLOR]','https://javhoho.com/category/free-hongkong-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Indian Porn[/COLOR]','https://javhoho.com/category/free-indian-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Indonesian Porn[/COLOR]','https://javhoho.com/category/free-indonesian-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Laos Porn[/COLOR]','https://javhoho.com/category/free-laos-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Myanmar Porn[/COLOR]','https://javhoho.com/category/free-myanmar-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Taiwan Porn[/COLOR]','https://javhoho.com/category/free-taiwan-porn/',311,'','')
    utils.addDir('[COLOR hotpink]Virtual Reality Porn[/COLOR]','https://javhoho.com/category/free-jav-vr-virtual-reality/',311,'','')    
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://javhoho.com/search/',314,'','')
    #List('https://javhoho.com/all-movies-free-jav-uncensored-censored-asian-porn-korean/')
    List('https://javhoho.com/')


@utils.url_dispatcher.register('311', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        utils.kodilog('site error')
        return None
    match = re.compile('class="item-thumbnail".+?href="([^"]+)".+?src="([^"]+)".+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)       
    for videopage, img, name in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 312, img, '')
    try:
        next_page = re.compile('href="([^"]+)">&raquo;<').findall(listhtml)[0]
        last_page = re.compile('class="last" href="([^"]+)"').findall(listhtml)
        if last_page:
            last = last_page[0].split('/')[-2]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ('/' + last if last_page else '') + ')', next_page, 311, '')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('314', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 314)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


@utils.url_dispatcher.register('313', ['url'])
def Cat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<a class="item" href="([^"]+)" title="([^"]+)">.+?src="([^"]+)".+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in match:
        name = name + " [COLOR deeppink]" + videos + "[/COLOR]"    
        utils.addDir(name, catpage, 311, img)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('312', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    listhtml = utils.getHtml(url)
    match = re.compile('data-lazy-type="iframe" data-src="([^"]+)"',).findall(listhtml)
    videoArray = []
    for item in match:
        if 'javhoho.com' in item:
            try:
                listhtml = utils.getHtml(item)
                videourl = 'https://www.bitporno.com' + re.compile('file: "(.+?)"', re.DOTALL).findall(listhtml)[0]
                videoArray.append(['Bitporno', videourl])
            except: continue
        if 'streamz.cc' in item:
            try:
                listhtml = utils.getHtml(item)
                packed = re.compile('(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
                unpacked = utils.unpack(packed)
                videourl = re.compile("'(http.+?)\\\\'", re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
                videoArray.append(['Streamz.cc', videourl])
            except: continue
        if 'gdriveplayer.to' in item:
            try:
                listhtml = utils.getHtml('https:' + item)
                packed = re.compile('(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
                unpacked = utils.unpack(packed)
                videourl = re.compile("'(http.+?)'", re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
                videoArray.append(['Gdriveplayer.to', videourl])
            except: continue
        if 'youvideos.ru' in item:
            try:
                r = requests.post(item.replace('/v/', '/api/source/'), data='').text
                movieJson = json.loads(r)['data']
                videoRU = [[str(item['label']), item['file']] for item in movieJson]
                videoArray.append(['YouVideos.ru', videourl])
            except: pass
    if not videoArray:
        utils.notify('Oh oh','Couldn\'t find a video')
        return
    choice = xbmcgui.Dialog().select('Select server', [item[0] for item in videoArray])
    videourl = videoArray[choice][1]
    if 'YouVideos.ru' in videoArray[choice][0]:
        videoRUs = sorted(videoRU, key = lambda x: int(x[0][:-1]), reverse = True)
        choice = xbmcgui.Dialog().select('Select resolution', [str(item[0]) for item in videoRUs])
        videourl = videoRUs[choice][1]
    
    iconimage = xbmc.getInfoImage("ListItem.Thumb")
    listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    listitem.setInfo('video', {'Title': name, 'Genre': 'JAVhoho'})
    xbmc.Player().play(videourl, listitem)
    return


    vp = utils.VideoPlayer(name, download)
    vp.progress.update(20, "", "Loading video page", "")
    videohtml = utils.getHtml(url)
    match = re.compile('target="_blank"\s+href=(\S+)\s+[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(videohtml)
    links = []
    for l in match:
        if l[1] not in ('FE', 'PT'):
            continue
        u = utils.getVideoLink(l[0], l[0])
        if 's=http' in u:
            u = 'http' + u.split('s=http')[-1]
        u = u.replace('youvideos.ru/f','feurl.com/v')
        links.insert(0,u)
    vp.play_from_link_list(links)
    return
    
    # hqplayer = re.compile('<iframe src="(https://javhoho.com/[^"]+)"', re.DOTALL | re.IGNORECASE).findall(videohtml)[0]
# #    hqplayer = links[0]
    # utils.kodilog(hqplayer)
    # link = utils.getVideoLink(hqplayer, hqplayer)
    # utils.kodilog(link)

    # playerhtml = utils.getHtml(link)
# #    utils.kodilog(playerhtml)

    # vp.progress.update(40, "", "Loading video page", "")    
    # packed = re.compile('(eval\(function\(p,a,c,k,e,d\).+?)\s*</script>', re.DOTALL | re.IGNORECASE).findall(playerhtml)[0]
    # utils.kodilog("packed: " + packed)
    # unpacked = utils.unpack(packed)
    # utils.kodilog("unpacked: " + unpacked)
# #    unpacked = unpacked.replace('\\','')
    # videolink = re.compile('file:"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
    # vp.progress.update(60, "", "Loading video page", "")
    # vp.play_from_direct_link(videolink) # + '|Referer=' + videolink)
    

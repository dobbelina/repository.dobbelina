#-*- coding: utf-8 -*-

import re

import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils
import json

progress = utils.progress


@utils.url_dispatcher.register('600')
def Main():
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://pandamovies.pw/search/', 604, '', '')
    utils.addDir('[COLOR hotpink]XXX Scenes[/COLOR]','https://pandamovies.pw/xxxscenes/movies/page/1', 601, '', '')
    utils.addDir('[COLOR hotpink]HD Movies[/COLOR]', 'https://pandamovies.pw/watch-hd-movies-online-free/page/1', 601, '', '')
    utils.addDir('[COLOR hotpink]Studios[/COLOR]', 'https://pandamovies.pw/adult/movies/page/1', 603, '', '')
    utils.addDir('[COLOR hotpink]Year[/COLOR]', 'https://pandamovies.pw/adult/movies/page/1', 605, '', '')

    List('https://pandamovies.pw/adult/movies/page/1')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('601', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="ml-item">.+?href="(.+?)".+?oldtitle="(.+?)".+?<img data-original="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)

    for url1, title, img in match:
        #utils.addDownLink(title.replace("&#8217;", "'").replace('&#8211;', '-'), url1, 602, img, '')
        utils.addDownLink(utils.cleantext(title), url1, 602, img, '')
    #try:
    #match=re.compile('''/page/(.+?)''', re.DOTALL | re.IGNORECASE).findall(url)
    #if match:
    thisP = url.split('/')[-1]
    match = re.compile('rel=\'nofollow\' href=\'(.+?)\'', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match:
        baseUrl = match[-1].split('/')
        totalPages = baseUrl[-1]
    else:
        baseUrl = url.split('/')
        totalPages = '1'
    if int(thisP) + 1<=int(totalPages):
        nextP = int(thisP) + 1
        nextUrl = '/'.join(baseUrl[:-1]) + '/' + str(nextP)
    else:
        nextP = int(thisP) + 1
        nextUrl = '/'.join(url.split('/')[:-1]) + '/' + str(nextP)
    utils.addDir('Next Page (' + str(nextP) + '/' + totalPages + ')', nextUrl, 601,'', '')
    #except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('604', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 604)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title + '/page/1'
        print "Searching URL: " + searchUrl
        List(searchUrl)



@utils.url_dispatcher.register('603', ['url'])
def ListStudios(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('menu-item-object-directors.+?href="(.+?)">(.+?)<', re.DOTALL).findall(listhtml)
    for url, name in match:
        utils.addDir(name, url  + '/page/1', 601, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('605', ['url'])
def ListYear(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('menu-item-object-page.+?href="(.+?)">(.+?)<', re.DOTALL).findall(listhtml)
    for url, name in match[1:]:
        utils.addDir(name, url + '/page/1', 601, '', '')
    xbmcplugin.endOfDirectory(utils.addon_handle)



@utils.url_dispatcher.register('602', ['url', 'name'], ['download'])
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
        vp.direct_regex ='(' + re.escape(videourl) + ')'
        vp.play_from_html(html)
    else:
        vp.play_from_link_to_resolve(videourl)


@utils.url_dispatcher.register('606', ['url'])
def ListHD(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None
    match = re.compile('class="ml-item">.+?href="(.+?)".+?oldtitle="(.+?)".+?<img data-original="(.+?)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    xbmcgui.Dialog().textviewer(url, str(match[0]))
    utils.kodilog(str(match[0]))
    for url1, title, img in match:
        #utils.addDownLink(title.replace("&#8217;", "'").replace('&#8211;', '-'), url1, 602, img, '')
        utils.addDownLink(utils.cleantext(title), url1.strip(), 602, img, '')
    #try:
    match=re.compile('/page/(.+?)', re.DOTALL | re.IGNORECASE).findall(url)
    if match:
        thisP = match[0]
        match = re.compile('rel=\'nofollow\' href=\'(.+?)\'', re.DOTALL | re.IGNORECASE).findall(listhtml)
        if match:
            baseUrl = match[0].split('/')
            totalPages = baseUrl[-1]
        else:
            baseUrl = url.split('/')
            totalPages = '1'
        if int(thisP) + 1<=int(totalPages):
            nextP = int(thisP) + 1
            nextUrl = '/'.join(baseUrl[:-1]) + '/' + str(nextP)
        else:
            nextP = int(thisP) + 1
            nextUrl = '/'.join(url.split('/')[:-1]) + '/' + str(nextP)
        utils.addDir('Next Page (' + str(nextP) + '/' + totalPages + ')', nextUrl, 601,'', '')
    #except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


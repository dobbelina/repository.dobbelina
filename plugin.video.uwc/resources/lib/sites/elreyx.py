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

import urllib
import re
import os.path

import xbmcplugin
from resources.lib import utils
progress = utils.progress


@utils.url_dispatcher.register('110')
def EXMain():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://elreyx.com/index1.html',113,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://elreyx.com/search-',114,'','')
    utils.addDir('[COLOR hotpink]Pornstars[/COLOR]','http://elreyx.com/index1.html',115,'','')
    utils.addDir('[COLOR hotpink]Movies[/COLOR]','http://elreyx.com/index1.html',116,'','')
    EXList('http://elreyx.com/index1.html')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('111', ['url'])
def EXList(url):
	url = 'https:'+url if url.startswith('//') else url
	try:
		listhtml = utils.getHtml(url, '')
	except:
		
		return None
	match = re.compile('notice_image">.*?<a title="([^"]+)" href="([^"]+)".*?src="([^"]+)".*?"notice_description">(.*?)</div', re.DOTALL | re.IGNORECASE).findall(listhtml)
	for name, videopage, img, desc in match:
		img = 'https:'+img if img.startswith('//') else img
		desc = utils.cleanhtml(desc).strip()
		utils.addDownLink(name, videopage, 112, img, desc)
	try:
		nextp=re.compile("""class="current".*?<a href='([^']+)' title='([^']+)'""", re.DOTALL | re.IGNORECASE).search(listhtml)
		next_page = urllib.quote_plus(nextp.group(1)).replace('%3A', ':').replace('%2F', '/')
		if not next_page.startswith('http'):
			next_page = os.path.split(url)[0] + '/' + next_page
		text = nextp.group(2).split(' ')[1] if ' ' in nextp.group(2) else nextp.group(2)
		utils.addDir('Next Page ({})'.format(text), next_page, 111,'')
	except:
		pass
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('114', ['url'], ['keyword'])      
def EXSearch(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 114)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title + ".html"
        EXList(searchUrl)


@utils.url_dispatcher.register('113', ['url'])
def EXCat(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('<div id="categories" class="hidden-xs"(?:>| style="display:none;">)(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    match1 = re.compile('href="([^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
    for catpage, name in match1:
        utils.addDir(name, catpage, 111, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)   


@utils.url_dispatcher.register('112', ['url', 'name'], ['download'])
def EXPlayvid(url, name, download=None):
	regex = '''(?:iframe|IFRAME).*?(?:src|SRC)=['"]([^"']+)'''
	url = 'https:'+url if url.startswith('//') else url
	#
	vp = utils.VideoPlayer(name, download, regex=regex)
	vp.progress.update(25, "", "Loading video page", "")
	
	videopage = utils.getHtml(url, '')
	links = re.compile(regex, re.DOTALL | re.IGNORECASE).findall(videopage)

	for link in links:
		if '.jpg' in link:
			continue
		try:
			videopage += utils.getHtml(link, url)
		except:
			pass
	vp.play_from_html(videopage)


@utils.url_dispatcher.register('115', ['url'])
def EXPornstars(url):
	url = 'https:'+url if url.startswith('//') else url
	cathtml = utils.getHtml(url, '')
	match = re.compile('<div id="pornstars" class="hidden-xs">(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)
	match1 = re.compile('href="([^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
	for catpage, name in match1:
		utils.addDir(name, catpage, 111, '')
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('116', ['url'])
def EXMovies(url):
	url = 'https:'+url if url.startswith('//') else url
	cathtml = utils.getHtml(url, '')
	match = re.compile('<div id="movies" class="hidden-xs">(.*?)</div>', re.DOTALL | re.IGNORECASE).findall(cathtml)
	match1 = re.compile('href="([^"]+)[^>]+>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(match[0])
	for catpage, name in match1:
		utils.addDir(name, catpage, 117, '')
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('117', ['url'])
def EXMoviesList(url):
	url = 'https:'+url if url.startswith('//') else url
	listhtml = utils.getHtml(url, '')
	match = re.compile('<div class="container_neus">(.*?)<div id="pagination">', re.DOTALL | re.IGNORECASE).findall(listhtml)
	match1 = re.compile('<a title="([^"]+)" href="([^"]+)".*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(match[0])
	for name, videopage, img in match1:  
		img = 'https:'+img if img.startswith('//') else img
		utils.addDownLink(name, videopage, 112, img, '')
	try:
		nextp=re.compile("<a href='([^']+)' title='([^']+)'>&raquo;</a>", re.DOTALL | re.IGNORECASE).findall(listhtml)
		next = urllib.quote_plus(nextp[0][0])
		next = next.replace(' ','+')
		utils.addDir('Next Page', os.path.split(url)[0] + '/' + next, 117,'')
	except: pass
	xbmcplugin.endOfDirectory(utils.addon_handle)

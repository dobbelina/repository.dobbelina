'''
    Ultimate Whitecream
    Copyright (C) 2018 Whitecream

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

@utils.url_dispatcher.register('680')
def pornvibe_main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://pornvibe.org/categories/', 683, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://pornvibe.org/?s=', 684, '', '')
    pornvibe_list('https://pornvibe.org/all-videos/')


@utils.url_dispatcher.register('681', ['url'])
def pornvibe_list(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as e:
        return None
    matchsection = re.search('''<section class="category-content">(.*?)<!--row list-group-->''', listhtml, re.DOTALL | re.IGNORECASE).group(1)
    match = re.compile('''<img width="\d+" height="\d+" src="([^"]+)"[^<]+(.*?)<a href="([^"]+)">([^<]+)<''', re.DOTALL | re.IGNORECASE).findall(matchsection)
    for img, duration, video, name in match:
        if 'pull-right' in duration:
            duration = re.search('''pull-right">\s*<span>([^<]+)<''', duration, re.DOTALL | re.IGNORECASE).group(1)
            duration = " [COLOR deeppink]" + duration + "[/COLOR]"
        else:
            duration = ''
        name = utils.cleantext(name) + duration
        utils.addDownLink(name, video, 682, img, '')
    try:
        next_page = re.compile('''<a class="next page-numbers" href="([^"]+)">Next''', re.DOTALL | re.IGNORECASE).search(listhtml).group(1)
        page_number = ''.join([nr for nr in next_page.split('/')[-2] if nr.isdigit()])
        utils.addDir('Next Page (' + page_number + ')', next_page, 681, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('683', ['url']) 
def pornvibe_cat(url):
	listhtml = utils.getHtml(url)
	match = re.compile('''<img src="([^"]+)" alt="([^"]+)">.+?href="([^"]+)".*?<p>([^&]+)&''', re.DOTALL | re.IGNORECASE).findall(listhtml)
	for img, name, catpage, count in sorted(match, key=lambda x: x[1].strip().lower()):
		name = utils.cleantext(name.strip()) + " [COLOR deeppink]" + count.strip() + " videos[/COLOR]"
		utils.addDir(name, catpage, 681, img, 1)
	xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('684', ['url'], ['keyword'])
def pornvibe_search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 684)
    else:
        title = keyword.replace(' ','+')
        url += title
        pornvibe_list(url)


@utils.url_dispatcher.register('682', ['url', 'name'], ['download'])
def pornvibe_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='''<iframe src="([^"]+)''', direct_regex=None)
    vp.play_from_site_link(url, url)

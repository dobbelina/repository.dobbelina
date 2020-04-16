'''
    Ultimate Whitecream
    Copyright (C) 2018 holisticdioxide

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


@utils.url_dispatcher.register('670')
def datoporn_main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','http://dato.porn/categories/', 673, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://dato.porn/search/', 674, '', '')
    datoporn_list('http://dato.porn')


@utils.url_dispatcher.register('671', ['url'])
def datoporn_list(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as e:
        return None
    match = re.compile('class="item.+?href="([^"]+)" title="([^"]+)".+?data-original="([^"]+)".+?class="duration">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, name, img, duration in match:
        duration = duration.strip()
        name = utils.cleantext(name) + " [COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, video, 672, img, '')
    try:
        next_page = re.compile('class="next"><a href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml).group(1)
        if next_page.startswith('/'): next_page = 'https://dato.porn' + next_page
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 671, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('673', ['url']) 
def datoporn_cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile('class="item" href="([^"]+)" title="([^"]+)">.+?class="thumb" src="([^"]+)".+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, img, count in sorted(match, key=lambda x: x[1].strip().lower()):
        name = utils.cleantext(name.strip()) + " [COLOR deeppink]" + count.strip() + "[/COLOR]"
        utils.addDir(name, catpage, 671, img, 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('674', ['url'], ['keyword'])
def datoporn_search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 674)
    else:
        title = keyword.replace(' ','-')
        url += title
        datoporn_list(url)


@utils.url_dispatcher.register('672', ['url', 'name'], ['download'])
def datoporn_play(url, name, download=None):
    url = url.split('/')
    url = url[:-2]
    url = '/'.join(url)
    url = url.replace('videos','embed')
    vp = utils.VideoPlayer(name, download,'', "video_url: '([^']+)'")
    videohtml = utils.getHtml(url)
    vp.play_from_html(videohtml)
#    vp.play_from_link_to_resolve(url)

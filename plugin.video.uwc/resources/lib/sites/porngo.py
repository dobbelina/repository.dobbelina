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

BASE_URL = 'https://porngo.com'

sortlistwxf = [utils.addon.getLocalizedString(30012), utils.addon.getLocalizedString(30013), utils.addon.getLocalizedString(30014)]

def make_url(link):
    return link if link.startswith('http') else 'https:' + link if link.startswith('//') else BASE_URL + link


@utils.url_dispatcher.register('690')
def ypp_main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://porngo.com/categories/', 693, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://porngo.com/search/', 694, '', '')
    Sort = '[COLOR hotpink]Current sort:[/COLOR] ' + sortlistwxf[int(utils.addon.getSetting("sortwxf"))]
    utils.addDir(Sort, '', 695, '', '')
    ypp_list('https://porngo.com')


@utils.url_dispatcher.register('695')
def ypp_sort():
    utils.addon.openSettings()
    ypp_main()

@utils.url_dispatcher.register('691', ['url'])
def ypp_list(url):
    utils.kodilog('RAW URL: ' + url)
#    sort = ('&s={}'.format(get_ypp_sort(True)) if get_ypp_sort(True) else '') if len(url.split('/')) >= 4 and url.split('/')[3].startswith('search') or url.endswith('date') else '/?s={}'.format(get_ypp_sort())
    sort = ''
#    utils.kodilog('SORT: ' + sort)
    url = url + sort if sort not in url else url
#    utils.kodilog(url.split('/')[2])
#    utils.kodilog(url)
    try:
        listhtml = utils.getHtml(url)
#        utils.kodilog(listhtml)
    except Exception as e:
        return None
    match = re.compile('''div class="thumb item ".*?href="([^"]+)".*?<img src="([^"]+)".*?alt="([^"]+)".*?duration">([^<]+)<.*?thumb__bage">([^<]+)<''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name, duration, hd in match:
#        utils.kodilog('Vid Quality: ' + hd)
        duration = duration.strip()
#        hd_text = ' [COLOR orange]HD[/COLOR] ' if 'HD' in hd else ''
#       Changed labelling adding Video quality
	hd = utils.cleantext(hd)
        hd_text = " [COLOR orange]" + hd + "[/COLOR] "
#        utils.kodilog('Vid Quality Printed: ' + hd_text)
        name = utils.cleantext(name) + hd_text + " [COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, make_url(video), 692, make_url(img), '')
    try:
        next_page = re.compile('pagination__link" href="([^"]+)">Next<', re.DOTALL | re.IGNORECASE).findall(listhtml)[-1]
        utils.addDir('Next Page' , make_url(next_page), 691, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('693', ['url']) 
def ypp_cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile('"letter-block__item".*?<a href="([^"]+)" class="letter-block__link">.*?<span>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name in match:
        utils.addDir(name, make_url(catpage), 691, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('694', ['url'], ['keyword'])
def ypp_search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 694)
    else:
        url = url + keyword.replace(' ','-') + '/'
        utils.kodilog('SEARCH URL: ' + url)
        ypp_list(url)

@utils.url_dispatcher.register('692', ['url', 'name'], ['download'])
def ypp_play(url, name, download=None):
    videopage = utils.getHtml(url, '')
    videos = re.compile(r'video-links__link" href="([^"]+)" .*?no-load-content>([^<]+)<', re.DOTALL | re.IGNORECASE).findall(videopage)
    list = {}
    for video_link, quality in videos:
        quality = quality.replace('4K', '2160p')
        list[quality] = video_link
    videourl = utils.selector('Select quality', list, dont_ask_valid=True, sort_by=lambda x: int(re.findall(r'\d+', x)[0]), reverse=True)
    if not videourl:
        return
    utils.playvid(videourl, name, download)


def get_ypp_sort(search=False):
    sortoptions = {0: 'date', 1: None, 2: None} if search else {0: 'date', 1: 'votes', 2: 'views&m=3days'}
    sortvalue = utils.addon.getSetting("sortwxf")
    return sortoptions[int(sortvalue)]

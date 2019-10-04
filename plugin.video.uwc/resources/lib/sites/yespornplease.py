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

BASE_URL = 'https://yespornplease.com'

sortlistwxf = [utils.addon.getLocalizedString(30012), utils.addon.getLocalizedString(30013), utils.addon.getLocalizedString(30014)]

def make_url(link):
    return link if link.startswith('http') else 'https:' + link if link.startswith('//') else BASE_URL + link


@utils.url_dispatcher.register('690')
def ypp_main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://yespornplease.com/categories', 693, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://yespornplease.com/search?q=', 694, '', '')
    Sort = '[COLOR hotpink]Current sort:[/COLOR] ' + sortlistwxf[int(utils.addon.getSetting("sortwxf"))]
    utils.addDir(Sort, '', 695, '', '')
    ypp_list('https://yespornplease.com')


@utils.url_dispatcher.register('695')
def ypp_sort():
    utils.addon.openSettings()
    ypp_main()


@utils.url_dispatcher.register('691', ['url'])
def ypp_list(url):
#    utils.kodilog('RAW URL: ' + url)
    sort = ('&s={}'.format(get_ypp_sort(True)) if get_ypp_sort(True) else '') if len(url.split('/')) >= 4 and url.split('/')[3].startswith('search') or url.endswith('date') else '/?s={}'.format(get_ypp_sort())
#    utils.kodilog('SORT: ' + sort)
    url = url + sort if sort not in url else url
    utils.kodilog(url.split('/')[2])
    utils.kodilog(url)
    try:
        listhtml = utils.getHtml(url)
    except Exception as e:
        return None
    match = re.compile('''div class="well well-sm".*?href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)"(.*?)duration">([^<]+)<''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name, hd, duration in match:
        duration = duration.strip()
        hd_text = ' [COLOR orange]HD[/COLOR] ' if 'HD' in hd else ''
        name = utils.cleantext(name) + hd_text + " [COLOR deeppink]" + duration + "[/COLOR]"
        utils.addDownLink(name, make_url(video), 692, make_url(img), '')
    try:
#Test
        next_page = re.compile('''a href="([^"]+)" class="prevnext"''', re.DOTALL | re.IGNORECASE).findall(listhtml)[-1]
        utils.addDir('Next Page' , make_url(next_page), 691, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('693', ['url']) 
def ypp_cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile('<div class="col-sm-4 col-md-3 col-lg-3 m-b-20">.*?href="([^"]+)".*?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name in match:
        utils.addDir(name, make_url(catpage), 691, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('694', ['url'], ['keyword'])
def ypp_search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 694)
    else:
        url += keyword.replace(' ','+')
        ypp_list(url)


@utils.url_dispatcher.register('692', ['url', 'name'], ['download'])
def ypp_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download, regex='iframe src="([^"]+)"', direct_regex=None)
    vp.play_from_site_link(url)

def get_ypp_sort(search=False):
    sortoptions = {0: 'date', 1: None, 2: None} if search else {0: 'date', 1: 'votes', 2: 'views&m=3days'}
    sortvalue = utils.addon.getSetting("sortwxf")
    return sortoptions[int(sortvalue)]

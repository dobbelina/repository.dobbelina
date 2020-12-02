'''
    Ultimate Whitecream
    Copyright (C) 2020

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

SITE_URL = 'https://www.peekvids.com'
sortlistwxf = [utils.addon.getLocalizedString(30012),
               utils.addon.getLocalizedString(30013),
               utils.addon.getLocalizedString(30014)]


def make_url(url, options=None):
    if options:
        sortoption = Get_Sort()
        if sortoption:
            url += '&sort_by=' + sortoption
        filteroptions = Get_Filters()
        if filteroptions['uploaded']:
            url += '&uploaded=' + filteroptions['uploaded']
        if filteroptions['duration']:
            url += '&duration=' + filteroptions['duration']
        if filteroptions['quality']:
            url += '&hd=' + filteroptions['quality']
    return url if url.startswith('http') else 'https:' + url if url.startswith('//') else SITE_URL + url


@utils.url_dispatcher.register('890')
def Main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', SITE_URL + '/categories', 893, '', '')
    utils.addDir('[COLOR hotpink]Models[/COLOR]', SITE_URL + '/pornstars', 896, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', SITE_URL + '/sq?q=', 894, '', '')
    utils.addDir('[COLOR hotpink]Current sort:[/COLOR] ' + sortlistwxf[int(utils.addon.getSetting("sortwxf"))], '', 895, '', '')
    activefilters = int(int(utils.addon.getSetting("filteruploaded")) > 0)
    activefilters += int(int(utils.addon.getSetting("filterduration")) > 0)
    activefilters += int(int(utils.addon.getSetting("filterquality")) > 0)
    utils.addDir('[COLOR hotpink]Current filters: [/COLOR] ' + str(activefilters), '', 895, '', '')
    utils.addDir('[COLOR hotpink]Channels[/COLOR]', SITE_URL + '/channels', 897, '', '')
    List(SITE_URL)


@utils.url_dispatcher.register('891', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, SITE_URL + '/')
    except:
        pass
    try:
        match = re.compile(r'video-item-.*?href="([^"]+)".*?<img[\s]+class="card-img-top"[\s]+src="([^"]+)"[\s]+alt="([^"]+)".*?duration[^>]+>([^<]+)<',
                           re.DOTALL | re.IGNORECASE).findall(listhtml)
        for video, img, name, duration in match:
            name = utils.cleantext(name + " [COLOR deeppink]" + duration.strip() + "[/COLOR]")
            utils.addDownLink(name, make_url(video), 892, make_url(img), '')
    except:
        return None
    try:
        next_page = re.search(r'"next"[\s]+href="([^"]+)"', listhtml).group(1)
        utils.addDir('Next Page', make_url(next_page, True), 891, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('892', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    videopage = utils.getHtml(url, SITE_URL + '/')
    videos = re.compile('data-hls-src([^=]+)="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videopage)
    list = {}
    for quality, video_link in videos:
        list[quality + 'p'] = video_link.replace('&amp;', '&')
    videourl = utils.selector('Select quality', list, dont_ask_valid=True, sort_by=lambda x: int(re.findall(r'\d+', x)[0]), reverse=True)
    if not videourl:
        return
    utils.playvid(videourl, name, download)


@utils.url_dispatcher.register('893', ['url'])
def Categories(url):
    listhtml = utils.getHtml(url, SITE_URL + '/')
    try:
        match = re.compile(r'<li>[\s]*<a href="(/category/[^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE | re.UNICODE).findall(listhtml)
        for catpage, name in match:
            utils.addDir(name, make_url(catpage), 891, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('894', ['url'], ['keyword'])
def Search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 894)
    else:
        List(make_url(url+keyword.replace(' ', '+'), True))


@utils.url_dispatcher.register('895')
def Change_Settings():
    utils.addon.openSettings()
    Main()


def Get_Sort():
    sortoptions = {0: 'time', 1: 'relevance', 2: 'rating'}
    return sortoptions[int(utils.addon.getSetting("sortwxf"))]


def Get_Filters():
    filteroption_uploaded = {0: None, 1: 'today', 2: 'week', 3: 'month', 4: 'year'}
    filteroption_duration = {0: None, 1: 'long', 2: 'short'}
    filteroption_quality = {0: None, 1: '1', 2: '2'}
    uploadedvalue = int(utils.addon.getSetting("filteruploaded"))
    durationvalue = int(utils.addon.getSetting("filterduration"))
    qualityvalue = int(utils.addon.getSetting("filterquality"))
    filteroptions = {'uploaded': filteroption_uploaded[uploadedvalue],
                     'duration': filteroption_duration[durationvalue], 'quality': filteroption_quality[qualityvalue]}
    return filteroptions


@utils.url_dispatcher.register('896', ['url'])
def Models(url):
    listhtml = utils.getHtml(url, SITE_URL + '/')
    try:
        match = re.compile('<li class="overflow-visible">.*?href="/pornstar/([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
        for model in match:
            utils.addDir(model.replace('-', ' '), make_url('/pornstar/' + model), 891, '')
    except:
        return None
    try:
        next_page = re.search(r'"next"[\s]+href="([^"]+)"', listhtml).group(1)
        utils.addDir('Next Page', make_url(next_page), 896, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('897', ['url'])
def Channels(url):
    listhtml = utils.getHtml(url, SITE_URL + '/')
    try:
        match = re.compile('class="card-img".*?href="(/[^"]+)".*?<img class="card-img-top".*?src="[^"]+".*?alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml[listhtml.find('popular_channels'):])
        for channel, name in match:
            utils.addDir(name.strip(), make_url(channel), 891, '')
    except:
        return None
    try:
        next_page = re.search(r'"next"[\s]+href="([^"]+)"', listhtml).group(1)
        utils.addDir('Next Page', make_url(next_page), 897, '')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)

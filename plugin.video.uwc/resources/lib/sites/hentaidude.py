'''
    Ultimate Whitecream
    Copyright (C) 2020 Whitecream

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
from resources.lib import utils
import xbmcplugin
import xbmcgui
import json

@utils.url_dispatcher.register('920')
def Main():
    utils.addDir('[COLOR hotpink]Uncensored[/COLOR]', 'https://hentaidude.com/page/1/?vidtype=uncensored', 921, '', '')
    utils.addDir('[COLOR hotpink]3D Hentai[/COLOR]', 'https://hentaidude.com/tag/3d-hentai-0/page/1/', 921, '', '')
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'https://hentaidude.com/page/1/', 924, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', 'https://hentaidude.com/page/1/?s=', 923, '', '')
    List('https://hentaidude.com/page/1/')


@utils.url_dispatcher.register('921', ['url'])
def List(url):
    try:
        listhtml = utils.getHtml(url, '')
    except:
        return None

    match = re.compile('class="videoPost".+?title="([^"]+)".+?href="([^"]+)".+?data-src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for name, videopage, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 922, img, '')
    try:
        pagination = re.compile('class="active"(.+?)class="styled-button"', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        nextlink = re.compile('href="(.+?)"', re.DOTALL | re.IGNORECASE).findall(pagination)[-1]
        utils.addDir('Next Page (%s)'%str(nextlink.split('/')[-2]), nextlink, 921,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('922', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    try:
        html = utils.getHtml(url, '')
    except:
        return None
    match = re.compile("action: 'msv-get-sources'.+?id: '(.+?)'.+?nonce: '(.+?)'", re.DOTALL | re.IGNORECASE).findall(html)[0]
    payload = {'action':'msv-get-sources', 'id':match[0], 'nonce':match[1]}
    sources = utils.postHtml('https://hentaidude.com/wp-admin/admin-ajax.php', form_data=payload, compression=False, NoCookie=None)
    if not sources: return
    sJson = json.loads(sources)
    if not sJson['success']: return
    videourl = sJson['sources']['video-source-0']
    vp.play_from_direct_link(videourl)


@utils.url_dispatcher.register('924', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('data-tag="(.+?)" class="btn.+?>([^"]+)<span.+?>(.+?)</span', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for cat, name, count in match:
        catpage = 'https://hentaidude.com/page/1/?tid=' + cat
        name = utils.cleantext(name) + "[COLOR hotpink] (" + count + ")[/COLOR]"
        utils.addDir(name, catpage, 921, '')
    xbmcplugin.endOfDirectory(utils.addon_handle)

@utils.url_dispatcher.register('923', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 923)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)

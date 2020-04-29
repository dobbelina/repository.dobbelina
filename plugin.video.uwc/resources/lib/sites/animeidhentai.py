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


@utils.url_dispatcher.register('660')
def animeidhentai_main():
    utils.addDir('[COLOR hotpink]Uncensored[/COLOR]','https://animeidhentai.com/hentai/uncensored-hentai/', 661, '', '')
    utils.addDir('[COLOR hotpink]3D[/COLOR]','https://animeidhentai.com/genre/3d/', 661, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://animeidhentai.com/?s=', 664, '', '')
    animeidhentai_list('https://animeidhentai.com/genre/2020/')


@utils.url_dispatcher.register('661', ['url'])
def animeidhentai_list(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as e:
        return None
    match = re.compile(r'article class=.+?entry-title">([^<]+)<(.+?)/header.+?src="??([^"\s]+jpg)"??\s.+?href="??([^"\s]+)"??\s', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if match: 
        for name, other, img, video in match:
            if 'uncensored' in name.lower():
                name = re.sub('Uncensored', ' [COLOR hotpink]Uncensored[/COLOR]', name, flags=re.IGNORECASE)
            else:
                if 'uncensored' in other.lower():
                    name = name + " [COLOR hotpink]Uncensored[/COLOR]" 
            utils.addDownLink(utils.cleantext(name), video, 662, img, '')
    else:
        match = re.compile('div class="result-item".*?<a href="([^"]+)">.*?<img\s*src="([^"]+)"\s*alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)       
        for video, img, name in match:
            if 'uncensored' in name.lower():
                name = name.replace('Uncensored',' [COLOR hotpink]Uncensored[/COLOR]')
            utils.addDownLink(utils.cleantext(name), video, 662, img, '')
    try:
        next_page = re.compile(r'href="??([^"\s]+)"??\s*class="??next', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        page_nr = re.findall('\d+', next_page)[-1]
        utils.addDir('Next Page (' + page_nr + ')', next_page, 661,'')
    except:
        pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('664', ['url'], ['keyword'])
def animeidhentai_search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 664)
    else:
        title = keyword.replace(' ','+')
        url += title
        animeidhentai_list(url)


@utils.url_dispatcher.register('662', ['url', 'name'], ['download'])
def animeidhentai_play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    html = utils.getHtml(url)
#    video_url = re.compile('data-lazy-src="([^"]+ksplayer[^"]+)"></iframe>', re.DOTALL | re.IGNORECASE).findall(html)
    video_url = re.compile('data-lazy-src="([^"]+embed[^"]+)"></iframe>', re.DOTALL | re.IGNORECASE).findall(html)[0]
#    video_url  = video_url[0].replace('embed','download')
    videopage = utils.getHtml(video_url, url)
    packed = re.compile('>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    unpacked = utils.unpack(packed)
    video = re.compile('"file":"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(unpacked)[0]
#    match = re.compile('''href=["']?(?P<url>[^"']+)["']?>DOWNLOAD <span>(?P<label>[^<]+)''', re.DOTALL | re.IGNORECASE).findall(videopage)
    vp.progress.update(50, "", "Loading video page", "")
#    list = {}
#    for video_link, quality in match:
#        list[quality] = video_link
#    selected = utils.selector('Select quality', list, dont_ask_valid=True,  sort_by=lambda x: int(x[:-1]), reverse=True)
#    if not selected: return
    vp.play_from_direct_link(video)

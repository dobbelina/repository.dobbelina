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
    utils.addDir('[COLOR hotpink]Uncensored[/COLOR]','https://animeidhentai.com/genre/hentai-uncensored/', 661, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://animeidhentai.com/?s=', 664, '', '')
    animeidhentai_list('https://animeidhentai.com/genre/2019/')


@utils.url_dispatcher.register('661', ['url'])
def animeidhentai_list(url):
    try:
        listhtml = utils.getHtml(url)
    except Exception as e:
        return None
#    match = re.compile(r'<article id="??[^"\s]+(.*?)src="??([^"\s]+)"?? alt="([^"]+)".*?href="??([^"\s>]+)"??', re.DOTALL | re.IGNORECASE).findall(listhtml)
#    match = re.compile(r'article class=.+?entry-title">([^<]+)<(.+?)src=(\S+)\s.+?href=(\S+)\s', re.DOTALL | re.IGNORECASE).findall(listhtml)
    match = re.compile(r'article class=.+?entry-title">([^<]+)<(.+?)src="??([^"\s]+jpg)"??\s.+?href="??([^"\s]+)"??\s', re.DOTALL | re.IGNORECASE).findall(listhtml)
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
        utils.addDir('Next Page', next_page, 661, '')
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
    vp = utils.VideoPlayer(name, download=download, regex=r"""<iframe.*?src=["']??([^"'\s]+)""", direct_regex=None)
    vp.play_from_site_link(url)
    

    

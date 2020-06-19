'''
    Ultimate Whitecream
    Copyright (C) 2016 Whitecream

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
import json


@utils.url_dispatcher.register('430')
def Main():
    utils.addDir('[COLOR hotpink]Tags[/COLOR]','http://www.eroticage.net/',433,'','')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','http://www.eroticage.net/?s=',434,'','')
    List('http://www.eroticage.net/?filter=latest')


@utils.url_dispatcher.register('431', ['url'])
def List(url):
    try:
        html = utils.getHtml(url, '')
    except:
        return None
    html = html.split(">RANDOM<")[0]
    match = re.compile('<article.+?href="([^"]+)"\s*title="([^"]+)".+?img data-src="([^"]+)".+?</article>', re.DOTALL | re.IGNORECASE).findall(html)
    
    for videopage, name, img in match:
        name = utils.cleantext(name)
        utils.addDownLink(name, videopage, 432, img, '')
    try:
        nextp = re.compile('href="([^"]+)">Next<', re.DOTALL | re.IGNORECASE).findall(html)[0]
        page_nr = re.findall('\d+', nextp)[-1]
        utils.addDir('Next Page (' + page_nr + ')', nextp, 431,'')
    except: pass
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('432', ['url', 'name'], ['download'])
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "", "Loading video page", "")
    videopage = utils.getHtml(url)
    videolink = re.compile('<iframe src="([^"]+)" ', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    if videolink.startswith('https://cine-matik.com/'):
        page = utils.getHtml(videolink, url)
        alternative = re.compile('input type="hidden" id="alternative" value="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(page)[0]
        video = videolink.replace('https://cine-matik.com/player/play.php?vid=','')
        posturl = 'https://cine-matik.com/player/ajax_sources.php'
        postRequest = {'vid' : video, 'alternative' : alternative}
        response = utils.postHtml(posturl, form_data=postRequest, headers={'X-Requested-With' : 'XMLHttpRequest'}, compression=False)
        js = json.loads(response)
        sources = js["source"]
        alternative1 = js["alternative"] if len(sources) == 0 else alternative
        if len(sources) == 1 and not sources[0]["file"]: alternative1 = js["alternative"] 
        if alternative1 != alternative:
            postRequest = {'vid' : video, 'alternative' : 'mp4'}
            response = utils.postHtml(posturl, form_data=postRequest, headers={'X-Requested-With' : 'XMLHttpRequest'}, compression=False)
            js = json.loads(response)
            sources = js["source"]
        videolink = sources[0]["file"] if len(sources) !=0 else ''
        if not videolink:
            utils.notify('Oh oh','Couldn\'t find a video')
            return
        vp.play_from_direct_link(videolink)
    else:
        videolink = videolink.replace('https://www.pornhub.com/embed/','https://www.pornhub.com/view_video.php?viewkey=')
        videolink = videolink.replace('woof.tube','verystream.com')
        vp.play_from_link_to_resolve(videolink)


@utils.url_dispatcher.register('433', ['url'])
def Categories(url):
    cathtml = utils.getHtml(url, '')
    match = re.compile('href="([^"]+)" class="tag[^>]+>([^<]+)<').findall(cathtml)
    for catpage, name in match:
        utils.addDir(name, catpage, 431, '')    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('434', ['url'], ['keyword'])
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        utils.searchDir(url, 434)
    else:
        title = keyword.replace(' ','+')
        searchUrl = searchUrl + title
        List(searchUrl)


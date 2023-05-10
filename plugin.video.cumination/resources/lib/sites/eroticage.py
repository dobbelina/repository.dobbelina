'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
from resources.lib.adultsite import AdultSite
import json

site = AdultSite('eroticage', '[COLOR hotpink]EroticAge[/COLOR]', 'https://www.eroticage.net/', 'https://www.eroticage.net/wp-content/uploads/2021/08/eroticage-logo.jpg', 'eroticage')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + '?filter=latest')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    if '>Nothing found<' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return
    html = html.split('class="site-footer"')
    match = re.compile(r'<article id="post.+?a href="([^"]+)"\s*title="([^"]+)".+?(?:poster|data-src|img src)="([^"]+)".+?class="fa fa-clock-o"></i>([\s\d:]+)<', re.DOTALL | re.IGNORECASE).findall(html[0])
    for videopage, name, img, duration in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)
    nextp = re.compile(r'href="([^"]+)">Next<', re.DOTALL | re.IGNORECASE).findall(html[0])
    if nextp:
        np = nextp[0]
        npage = re.findall(r'/\d+/', np)[-1].replace('/', '')
        lp = re.compile(r'/(\d+)/\D*?>Last<', re.DOTALL | re.IGNORECASE).findall(html[0])
        lp = '/' + lp[-1] if lp else ''
        site.add_dir('Next Page ({}{})'.format(npage, lp), np, 'List', site.img_next)
    else:
        nextp = re.compile(r'class="current">.+?href="([^"]+)"[^>]+>(\d+)<', re.DOTALL | re.IGNORECASE).findall(html[0])
        if nextp:
            np, npage = nextp[0]
            site.add_dir('Next Page ({})'.format(npage), np, 'List', site.img_next)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<article id=.+?href="([^"]+)".+?src="([^"]+)".+?class="cat-title">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex='<iframe src="([^"]+)"', direct_regex=None)
    videohtml = utils.getHtml(url)
    if '<iframe src="' in videohtml:
        vp.progress.update(25, "[CR]Loading video page[CR]")
        vp.play_from_site_link(url)
    else:
        match = re.compile(r'itemprop="embedURL" content="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
        if match:
            iframehtml = utils.getHtml(match[0])
            match = re.compile(r"iframeElement.src\s*=\s*'([^']+)'", re.IGNORECASE | re.DOTALL).findall(iframehtml)
            if match:
                playerurl = 'https:' + match[0] if match[0].startswith('//') else match[0]
                playerhtml = utils.getHtml(playerurl)
                match = re.compile(r'"contentProviderUrl":"([^"]+)"', re.IGNORECASE | re.DOTALL).findall(playerhtml)
                if match:
                    contenturl = match[0].replace(r'\/', '/')
                    headers = {'User-Agent': utils.USER_AGENT, 'X-Requested-With': 'XMLHttpRequest'}
                    contenthtml = utils.getHtml(contenturl, playerurl, headers)
                    jsondata = json.loads(contenthtml)
                    videourl = jsondata['data']['contentUrl']
                    if videourl.startswith('//'):
                        videourl = 'https:' + videourl
                    vp.progress.update(75, "[CR]Loading video page[CR]")
                    vp.play_from_direct_link(videourl)

"""
    Cumination
    Copyright (C) 2020 Team Cumination

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
"""

import re
from resources.lib import utils
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite
from random import randint

site = AdultSite('vipporns', '[COLOR hotpink]VIP Porns[/COLOR]', 'https://www.vipporns.com/', 'vipporns.png', 'vipporns')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'new-porn-video/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    r = re.compile(r'<title>.+?(?:"list-albums"|"box\stag)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if r:
        listhtml = r.group(0)
    match = re.compile(r'class="item.+?href="([^"]+).+?nal="([^"]+).+?le">\s*([^<]+).+?on">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name, duration in match:
        name = utils.cleantext(name.strip())
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    match = re.search(r'class="load-more".+?data-block-id="([^"]+)".+?data-parameters="([^"]+)">Load', listhtml, re.DOTALL | re.IGNORECASE)
    if match:
        block_id = match.group(1)
        params = match.group(2).replace(';', '&').replace(':', '=')
        npage = params.split('=')[-1]
        rnd = 1000000000000 + randint(0, 999999999999)
        nurl = url.split('?')[0] + '?mode=async&function=get_block&block_id={0}&{1}&_={2}'.format(block_id, params, str(rnd))

        nurl = nurl.replace('+from_albums', '')
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] (' + npage + ')', nurl, 'List', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = "{0}{1}/".format(searchUrl, title)
        List(searchUrl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, '')
    items = re.compile('class="item.+?</a>', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for item in sorted(items):
        catpage = re.compile('href="([^"]+)').findall(item)[0]
        name = re.compile('title">([^<]+)').findall(item)[0]
        videos = re.compile('videos">([^<]+)').findall(item)[0]
        name = "{0} [COLOR deeppink][I]({1})[/I][/COLOR]".format(utils.cleantext(name.strip()), videos)
        img = '' if 'no image' in item else re.compile('src="([^"]+)').findall(item)[0]
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    surl = re.search(r"video(?:_alt)?_url:\s*'([^']+)", html)
    if surl:
        vp.progress.update(50, "[CR]Video found[CR]")
        surl = surl.group(1)
        if surl.startswith('function/'):
            lcode = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, lcode)
        if 'get_file' in surl:
            surl = utils.getVideoLink(surl, site.url)
        surl = '{0}|User-Agent=iPad&Referer={1}'.format(surl, site.url)
        vp.play_from_direct_link(surl)
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')
        return

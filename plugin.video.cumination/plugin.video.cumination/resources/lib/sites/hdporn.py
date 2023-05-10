"""
    Cumination
    Copyright (C) 2018 Whitecream, holisticdioxide
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

site = AdultSite('porn00', '[COLOR hotpink]Porn00[/COLOR]', 'https://www.porn00.org', 'p00.png', 'porn00')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', '{0}/tags/'.format(site.url), 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', '{0}/search'.format(site.url), 'Search', site.img_search)
    List('{0}/porn-page/1/'.format(site.url))
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    match = re.compile(r'class="item.+?href="([^"]+).+?original="([^"]+)(.+?)le">\s*([^<]+).+?on">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, hd, name, duration in match:
        hd = 'HD' if 'class="is-hd"' in hd else ''
        name = utils.cleantext(name.strip())
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    npage = re.search(r'class="next.+?href="([^"]+)', listhtml, re.DOTALL | re.IGNORECASE)
    if npage:
        purl = site.url + npage.group(1)
        site.add_dir('Next Page ({0})'.format(purl.split('/')[-2]), purl, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url)
    sources = re.findall(r"video(?:_alt)?_url:\s*'([^']+).+?text:\s*'([^']+)", html)
    if sources:
        sources = {label: url for url, label in sources}
        surl = utils.prefquality(sources, sort_by=lambda x: int(''.join([y for y in x if y.isdigit()])), reverse=True)
        if surl.startswith('function/'):
            lcode = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = '{0}|User-Agent=iPad&Referer={1}/'.format(kvs_decode(surl, lcode), site.url)
    if not surl:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.progress.close()
    if download == 1:
        utils.downloadVideo(surl, name)
    else:
        vp.play_from_direct_link(surl)


@site.register()
def Cat(url):
    caturl = utils.getHtml(url)
    cathtml = re.compile('class="box"(.+?)"footer', re.DOTALL | re.IGNORECASE).findall(caturl)
    match = re.compile("""<li.*?href=['"]([^'"]+).*?>([^<]+)""", re.DOTALL | re.IGNORECASE).findall(cathtml[0])
    for videolist, name in match:
        site.add_dir(name, videolist, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = '{0}/{1}/'.format(url, title)
        List(searchUrl)

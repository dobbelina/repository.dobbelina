'''
    Cumination
    Copyright (C) 2022 Team Cumination

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

site = AdultSite('supjav', '[COLOR hotpink]SupJav[/COLOR]', 'https://supjav.com/', 'https://supjav.com/img/logo.png', 'supjav')
surl = 'https://lk1.supremejav.com/supjav.php'
enames = {'VV': 'VideoVard',
          'TV': 'TurboVIPlay',
          'JPA': 'JAPOPAV',
          'ST': 'StreamTape',
          'DS': 'DoodStream',
          'JS': 'JAVStream',
          'SSB': 'StreamSB',
          'NS': 'NinjaStream'}


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url + 'popular?sort=week')


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url)
    except:
        return None
    match = re.compile(r'class="post">.+?data-original="([^"]+).+?href="([^"]+).+?>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, videopage, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)
    p = re.compile(r'class="pagination"><ul>(.+?)</ul>').search(listhtml)
    if p:
        li = re.compile(r'(<li.+?</li>)').findall(p.group(1))
        next_page = ''
        if 'href' in li[-1]:
            next_page, np = re.findall(r'href="([^"]+(\d+)[^"]*)', li[-1])[0]
        else:
            for page in li:
                if 'active' in page:
                    active = li.index(page)
                    break
            if active + 2 < len(li):
                next_page, np = re.findall(r"href='([^']+)'>(\d+)", li[active + 1])[0]
        if next_page:
            lp = re.findall(r"href='[^']+'>(\d+)", li[-2])[0]
            site.add_dir('Next Page ({0}/{1})'.format(np, lp), next_page, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'menu-item-object-category.+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url, site.url)
    videourl = ''

    ediv = re.compile(r'<div\s*class="btns(?:\sactive)?">(.+?)(?:<div\s*class="downs">|<script)', re.DOTALL | re.IGNORECASE).findall(videopage)[0]
    if 'cd-server' in ediv:
        parts = re.compile(r'class="cd-server.+?(<a.+?)</div', re.DOTALL | re.IGNORECASE).findall(ediv)
        pno = 1
        sources = {}
        for part in parts:
            embeds = re.compile(r'class="btn-server.+?data-link="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(part)
            sources.update({'{0} [COLOR hotpink]Part {1}[/COLOR]'.format(enames[hoster] if hoster in enames.keys() else hoster, pno): embed for embed, hoster in embeds})
            pno += 1
    else:
        embeds = re.compile(r'class="btn-server.+?data-link="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(ediv)
        sources = {enames[hoster] if hoster in enames.keys() else hoster: embed for embed, hoster in embeds}

    olid = utils.selector('Select Hoster', sources)
    if olid:
        vurl = '{0}?c={1}'.format(surl, olid[::-1])
        videourl = utils.getVideoLink(vurl, surl)

    if not videourl:
        vp.progress.close()
        return

    vp.play_from_link_to_resolve(videourl)

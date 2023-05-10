'''
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
'''

import re
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('porngo', '[COLOR hotpink]PornGO[/COLOR]', 'https://www.porngo.com/', 'https://www.porngo.com/img/logo.png', 'porngo')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'latest-updates/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'''thumb\s*item.+?href="([^"]+).+?src="([^"]+)"\s*alt="([^"]+).+?tion">([^<]+).+?ge">([^<]+)''', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name, duration, qual in match:
        if qual == '720p':
            hd_text = 'HD '
        elif qual == '1080p':
            hd_text = 'FHD '
        elif qual == '2160p':
            hd_text = '4K '
        else:
            hd_text = ''
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'Play', img, name, duration=duration, quality=hd_text)

    next_page = re.compile(r'''class="pagination.+?href="([^"]+)">Next''').search(listhtml)
    if next_page:
        next_page = site.url[:-1] + next_page.group(1)
        lp = re.compile(r'''/(\d+)/\D+>Last''').search(listhtml)
        lp = '/' + lp.group(1) if lp else ''
        site.add_dir('Next Page... ({0}{1})'.format(next_page.split('/')[-2], lp), next_page, 'List', site.img_next)

    utils.eod()


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'"letter-block__item".+?<a\s*href="([^"]+)"\s*class="letter-block__link">.*?<span>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url, site.url)
    sources = re.compile(r'<a\s*class="video-links__link"\s*href="([^"]+)"\s*no-load-content>([^\s]+)').findall(html)
    if sources:
        sources = {key: value for value, key in sources}
        videourl = utils.prefquality(sources, reverse=True)
    if not videourl:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.progress.close()
    if download == 1:
        utils.downloadVideo(videourl, name)
    else:
        vp.play_from_direct_link(videourl)

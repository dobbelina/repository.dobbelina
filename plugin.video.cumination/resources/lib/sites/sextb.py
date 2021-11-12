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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('sextb', '[COLOR hotpink]SEXTB[/COLOR]', 'https://sextb.net/', 'https://sextb.net/images/logo.png?v=123', 'sextb')



@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Censored[/COLOR]', site.url + 'censored/pg-1', 'List', site.img_cat)
    #site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_cat)
    List(site.url + 'uncensored/pg-1')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    match = re.compile('<div class="tray-item .*?href="([^"]+)".*?data-src="([^"]+)" alt="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, name)

    nextp = re.compile('href="([^"]+)"><[^>]+>Next', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    videos = []
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    video_page = utils.getHtml(url, site.url)

    ajaxurl = 'https://sextb.net/ajax/player'
    ajaxvideos = re.compile('data-source="([^"]+)" data-id="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(video_page)
    for source, id in ajaxvideos:
        formdata = {'episode': id, 'filmId': source}
        data = utils.postHtml(ajaxurl, form_data=formdata)
        data = data.replace('\\', '')
        videos.append(data)
    
    downloadvideos = re.compile('href="([^"]+)" target="_blank"><button class="btn-download', re.IGNORECASE | re.DOTALL).findall(video_page)
    for downurl in downloadvideos:
        videos.append('src="{0}"'.format(downurl))
        
    videos = '\n'.join(videos)
    vp.play_from_html(videos)


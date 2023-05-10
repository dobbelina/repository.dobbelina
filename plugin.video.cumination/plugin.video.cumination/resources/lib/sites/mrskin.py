"""
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
"""

import re
import json
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite("mrskin", "[COLOR hotpink]Mr Skin[/COLOR]", "https://www.mrskin.com/", "mrskin.png", 'mrskin')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Playlists[/COLOR]', site.url + 'playlist', 'List', site.img_cat)
    # ListScenes(site.url + 'search/clips?sort=most_recent')
    List(site.url + 'video')

    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    items = re.compile(r'<div\s*class="col-md-4.+?data-src="([^"\?]+).+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, videopage, name in items:
        name = utils.cleantext(name)
        videopage = site.url[:-1] + videopage
        if '/playlist' in url:
            site.add_download_link(name, videopage, 'PlayPL', img, name, noDownload=True)
        else:
            site.add_download_link(name, videopage, 'Playvid', img, name, noDownload=True)
    nextp = re.search(r'''class='next'>\s*<a\s*href="([^"]+)">Next''', listhtml, re.DOTALL)
    if nextp:
        nextp = site.url[:-1] + nextp.group(1)
        cp = re.compile(r'''class='page\s*current'>\s*([\d,]*)''').findall(listhtml)[0]
        lp = re.compile(r'''class='last'>\s*[^\d]+(\d+).+?>Last''').findall(listhtml)[0]
        site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(cp, lp), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def ListPL(url):
    purl = site.url + 'playlist/' + url.split('-')[-1][1:]
    headers = {'X-Requested-With': 'XMLHttpRequest',
               'X-MOD-SBB-CTYPE': 'xhr',
               'Accept': 'application/json'}
    items = utils.getHtml(purl, site.url, headers=headers)
    items = json.loads(items).get('config').get('playlist')
    for item in items:
        name = utils.cleantext(item.get('title'))
        img = item.get('image')
        desc = item.get('description')
        if desc is None:
            desc = ''
        tags = ', '.join(item.get('tags'))
        if tags is None:
            tags = ''
        desc = desc + '\n\n[COLOR hotpink]Tags: [/COLOR]' + tags
        videopage = item.get('sources')[0].get('file') + '|Referer={0}&User-Agent=iPad'.format(site.url)
        site.add_download_link(name, videopage, 'Playvid', img, desc, noDownload=True)

    utils.eod()


@site.register()
def PlayPL(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    purl = site.url + 'playlist/' + url.split('-')[-1][1:]
    headers = {'X-Requested-With': 'XMLHttpRequest',
               'X-MOD-SBB-CTYPE': 'xhr',
               'Accept': 'application/json'}
    vp.progress.update(25, "[CR]Loading video page[CR]")
    items = utils.getHtml(purl, site.url, headers=headers)
    item = json.loads(items).get('config').get('playlist')[0]
    videopage = item.get('sources')[0].get('file') + '|Referer={0}&User-Agent=iPad'.format(site.url)
    vp.play_from_direct_link(videopage)


@site.register()
def ListScenes(url):
    listhtml = utils.getHtml(url, site.url)
    items = re.compile(r'<div\s*class="col-md-4.+?data-src="([^"\?]+).+?title">(.+?)/small>.+?scene-keywords">(.+?)\s*<span\s*class="scene-description">.+?clock-o"[^\d]+([^<]+)</span>([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for img, title, tags, duration, desc in items:
        name = re.compile(r'>([^<\n]+)').findall(title)
        name = ' '.join(name)
        name = utils.cleantext(name)
        if '|' in duration:
            duration = duration.split('|')[-1].strip()
        info = desc + '\n\n[COLOR hotpink]Tags: [/COLOR]' + ''.join(re.compile(r'>([^<\n]+)').findall(tags))
        info = utils.cleantext(info)
        videopage = site.url[:-1] + re.compile(r'href="([^"]+)').findall(title)[-1]
        site.add_download_link(name, videopage, 'Playvid', img, info, noDownload=True, duration=duration)
    nextp = re.search(r'''class='next'>\s*<a\s*href="([^"]+)">Next''', listhtml, re.DOTALL)
    if nextp:
        nextp = site.url[:-1] + nextp.group(1)
        cp = re.compile(r'''class='page\s*current'>\s*([\d,]*)''').findall(listhtml)[0]
        lp = re.compile(r'''class='last'>\s*[^\d]+(\d+).+?>Last''').findall(listhtml)[0]
        site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(cp, lp), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url)
    match = re.compile(r'<div\s*id="video_container"[^>]+?data-config="([^"]+)', re.IGNORECASE | re.DOTALL).search(videohtml)
    if match:
        match = match.group(1).replace('&quot;', '"')
        vidurl = re.compile(r'"file"\s*:\s*"([^"]+)', re.IGNORECASE | re.DOTALL).search(match)
        if vidurl:
            vp.play_from_direct_link(vidurl.group(1))
    else:
        vp.progress.close()
        utils.notify('Oh oh', 'No video found')

'''
    Cumination
    Copyright (C) 2023 Team Cumination

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
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite
import json

site = AdultSite('drtuber', '[COLOR hotpink]DrTuber[/COLOR]', 'https://www.drtuber.com/', 'drtuber.png', 'drtuber')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/videos/', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]HD[/COLOR]', site.url + 'hd/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]4k[/COLOR]', site.url + '4k/', 'List', site.img_cat)

    List(site.url)


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Find all video items
    video_items = soup.select('div.video-item, div.thumb, div.video')

    for item in video_items:
        try:
            # Get the video link
            link = item.select_one('a[href*="/video"]')
            if not link:
                continue

            videopage = utils.safe_get_attr(link, 'href')
            if not videopage:
                continue

            # Make absolute URL if needed
            if videopage.startswith('/'):
                videopage = site.url[:-1] + videopage
            elif not videopage.startswith('http'):
                videopage = site.url + videopage

            # Get image
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original'])

            # Get title from alt attribute or other sources
            name = utils.safe_get_attr(img_tag, 'alt')
            if not name:
                name_tag = item.select_one('h3, .title, a[title]')
                name = utils.safe_get_text(name_tag) if name_tag else utils.safe_get_attr(link, 'title', default='Video')
            name = utils.cleantext(name)

            # Get duration
            duration_tag = item.select_one('.time_thumb em, .duration, .video-duration, [class*="time"]')
            duration = utils.safe_get_text(duration_tag)

            # Get quality
            quality_tag = item.select_one('[class*="quality"], .hd-icon, .video-quality')
            quality = utils.safe_get_text(quality_tag)

            # Add video to list
            site.add_download_link(name, videopage, 'Play', img, name, duration=duration, quality=quality)

        except Exception as e:
            # Log error but continue processing other videos
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one('a[href]:has-text("Next"), a.next, li.next a')
    if not next_link:
        # Try alternate pagination patterns
        pagination = soup.select('div.pagination a, ul.pagination a')
        for link in pagination:
            if 'next' in utils.safe_get_text(link).lower():
                next_link = link
                break

    if next_link:
        next_url = utils.safe_get_attr(next_link, 'href')
        if next_url:
            # Make absolute URL
            if next_url.startswith('/'):
                next_url = site.url[:-1] + next_url
            elif not next_url.startswith('http'):
                next_url = site.url + next_url

            # Extract page numbers for display
            page_match = re.search(r'/(\d+)(?:/|$|\?)', next_url)
            np = page_match.group(1) if page_match else ''

            # Try to find last page number
            lp = ''
            last_page_links = soup.select('div.pagination a, ul.pagination a')
            page_numbers = []
            for link in last_page_links:
                text = utils.safe_get_text(link)
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                lp = str(max(page_numbers))

            # Create context menu for goto page
            cm_page = (utils.addon_sys + "?mode=drtuber.GotoPage&list_mode=drtuber.List&url="
                      + urllib_parse.quote_plus(next_url) + "&np=" + str(np) + "&lp=" + str(lp))
            cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

            page_label = 'Next Page'
            if np:
                page_label += ' (' + np
                if lp:
                    page_label += '/' + lp
                page_label += ')'

            site.add_dir(page_label, next_url, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/{}'.format(np), '/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # Find all category items
    category_items = soup.select('li.item')

    categories = []
    for item in category_items:
        try:
            # Get category link
            link = item.select_one('a')
            if not link:
                continue

            caturl = utils.safe_get_attr(link, 'href')
            if not caturl:
                continue

            # Make absolute URL if needed
            if caturl.startswith('/'):
                caturl = site.url[:-1] + caturl
            elif not caturl.startswith('http'):
                caturl = site.url + caturl

            # Get category name
            name_tag = item.select_one('span')
            name = utils.safe_get_text(name_tag)

            # Get video count
            count_tag = item.select_one('b')
            count = utils.safe_get_text(count_tag)

            # Combine name and count
            full_name = utils.cleantext(name + ' ' + count) if count else utils.cleantext(name)

            categories.append((full_name, caturl))

        except Exception as e:
            utils.kodilog("Error parsing category item: " + str(e))
            continue

    # Add categories in sorted order
    for name, caturl in sorted(categories, key=lambda x: x[0].lower()):
        site.add_dir(name, caturl, 'List', '')

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Play(url, name, download=None):
    vp = utils.VideoPlayer(name, download=download)
    videoid = url.replace(site.url, '').split('/')[0]
    jsonurl = site.url + 'player_config_json/?vid={}&aid=0&domain_id=0&embed=0&ref=null&check_speed=0'.format(videoid)
    hdr = utils.base_hdrs.copy()
    hdr['accept'] = 'application/json, text/javascript, */*; q=0.01'
    jsondata = utils.getHtml(jsonurl, url, headers=hdr)
    data = json.loads(jsondata)
    videos = data["files"]
    srcs = {}
    for v in videos:
        if videos[v]:
            if v == 'lq':
                srcs['480p'] = videos[v]
            elif v == 'hq':
                srcs['720p'] = videos[v]
            elif v == '4k':
                srcs['2160p'] = videos[v]

    video = utils.prefquality(srcs, sort_by=lambda x: int(x[:-1]), reverse=True)
    if video:
        vp.play_from_direct_link(video)

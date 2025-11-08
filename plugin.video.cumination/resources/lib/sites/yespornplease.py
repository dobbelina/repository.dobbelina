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
import xbmc
import xbmcgui
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('yespornplease', "[COLOR hotpink]YesPornPlease[/COLOR]", 'https://www.yespornplease.sexy/', 'yespornplease.png', 'yespornplease')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'channels/', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'most-recent/')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if 'Sorry, no results were found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    # Parse HTML with BeautifulSoup
    soup = utils.parse_html(html)

    # Find all video items
    video_items = soup.select('div.well.well-sm')

    for item in video_items:
        try:
            # Extract video link
            link = item.select_one('a.video-link')
            if not link:
                continue

            video_url = utils.safe_get_attr(link, 'href')
            if not video_url or '=modelfeed' in video_url:
                # Skip model feed items
                continue

            # Make absolute URL if needed
            if video_url.startswith('/'):
                video_url = site.url[:-1] + video_url

            # Extract title
            title = utils.safe_get_attr(link, 'title')
            if not title:
                continue

            # Extract thumbnail image
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'src'])

            # Extract duration
            duration_tag = item.select_one('div.duration')
            duration = utils.safe_get_text(duration_tag, '00:00')

            # Check for HD quality
            quality = 'HD' if item.select_one('div.hd, span.hd, .quality') else ''

            # Add video to list
            site.add_download_link(title, video_url, 'Playvid', img, '', duration=duration, quality=quality, contextm='yespornplease.Related')

        except Exception as e:
            # Log error but continue processing other videos
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Extract pagination (Next Page link)
    next_links = soup.select('a.prevnext')
    next_page = None
    for link in next_links:
        if 'Next' in utils.safe_get_text(link):
            next_page = link
            break

    if next_page:
        next_url = utils.safe_get_attr(next_page, 'href')
        if next_url:
            # Make absolute URL if needed
            if next_url.startswith('/'):
                next_url = site.url[:-1] + next_url

            # Extract page number for GotoPage context
            page_match = re.search(r'page(\d+)\.html', next_url)
            page_num = page_match.group(1) if page_match else ''

            # Extract last page number from pagination if available
            page_links = soup.select('a[href*="page"]')
            last_page = 0
            for pg_link in page_links:
                pg_href = utils.safe_get_attr(pg_link, 'href')
                pg_match = re.search(r'page(\d+)\.html', pg_href)
                if pg_match:
                    pg_num = int(pg_match.group(1))
                    if pg_num > last_page:
                        last_page = pg_num

            # Add Next Page directory with GotoPage context menu
            base_url = url.split('page')[0]
            site.add_dir('Next Page' + (' ({})'.format(page_num) if page_num else ''), next_url, 'List', site.img_next,
                        contextm={'title': 'Goto Page', 'mode': 'yespornplease.GotoPage',
                                 'list_mode': 'yespornplease.List', 'url': base_url + 'page{}.html'.format(page_num if page_num else '1'),
                                 'np': page_num if page_num else '1', 'lp': str(last_page)})

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page{}.html'.format(np), 'page{}.html'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('yespornplease.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)

    # Parse HTML with BeautifulSoup
    soup = utils.parse_html(cathtml)

    # Find all category links with title attributes
    category_links = soup.select('a[href][title]')

    for link in category_links:
        try:
            caturl = utils.safe_get_attr(link, 'href')
            if not caturl:
                continue

            # Make absolute URL if needed
            if caturl.startswith('/'):
                caturl = site.url[:-1] + caturl

            # Extract category name
            name = utils.safe_get_attr(link, 'title')
            if not name:
                continue

            name = utils.cleantext(name)

            # Extract thumbnail if available
            img_tag = link.select_one('img')
            img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original']) if img_tag else ''

            site.add_dir(name, caturl, 'List', img)

        except Exception as e:
            # Log error but continue processing other categories
            utils.kodilog("Error parsing category item: " + str(e))
            continue

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r'(?:src:|source src=)\s*"([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'iframe scrolling="no" src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    embedlink = None
    if match:
        embedlink = match[0]
    else:
        match = re.compile(r"iframe src='([^']+)'", re.IGNORECASE | re.DOTALL).findall(videohtml)
        if match:
            embedlink = match[0]

    if embedlink:
        embedhtml = utils.getHtml(embedlink, url)
        vp.play_from_html(embedhtml)

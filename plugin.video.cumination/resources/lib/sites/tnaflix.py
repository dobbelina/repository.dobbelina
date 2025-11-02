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

site = AdultSite('tnaflix', "[COLOR hotpink]T'nAflix[/COLOR]", 'https://www.tnaflix.com/', 'tnaflix.png', 'tnaflix')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars?filters[sorting]=2&filter_set=true', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels?page=1', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search.php?what=', 'Search', site.img_search)
    List(site.url + 'new/1')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)
    if 'No results found matching your criteria.' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    soup = utils.parse_html(html)

    # Find all video items
    video_items = soup.select('[data-vid], .video-item, .video')

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
            videopage = utils.fix_url(videopage, site.url)

            # Get image
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'data-src', ['src', 'data-original'])
            if img:
                img = utils.fix_url(img, site.url)

            # Get title from alt attribute
            name = utils.safe_get_attr(img_tag, 'alt')
            if not name:
                name_tag = item.select_one('.thumb-title, .title, h3')
                name = utils.safe_get_text(name_tag) if name_tag else 'Video'
            name = utils.cleantext(name)

            # Get quality
            quality_tag = item.select_one('[class*="quality"]')
            quality = utils.safe_get_text(quality_tag)
            # Fix 4p to 4K
            if quality == '4p':
                quality = '4K'

            # Get duration
            duration_tag = item.select_one('.video-duration, [class*="duration"]')
            duration = utils.safe_get_text(duration_tag)

            # Create context menu for related videos
            cm_related = (utils.addon_sys + "?mode=tnaflix.Related&url=" + urllib_parse.quote_plus(videopage))
            cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]

            # Add video to list
            site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=quality, contextm=cm)

        except Exception as e:
            # Log error but continue processing other videos
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one('link[rel="next"]')
    if next_link:
        next_url = utils.safe_get_attr(next_link, 'href')
        if next_url:
            # Make absolute URL
            next_url = utils.fix_url(next_url, site.url)

            # Extract page numbers for display
            if '/video' in url:
                page_match = re.search(r'page=(\d+)', next_url)
            else:
                page_match = re.search(r'/(\d+)\??', next_url)

            np = page_match.group(1) if page_match else ''

            # Try to find last page number
            lp = ''
            pagination_links = soup.select('.pagination a, .paginationItem a')
            page_numbers = []
            for link in pagination_links:
                text = utils.safe_get_text(link)
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                lp = str(max(page_numbers))

            # Create context menu for goto page
            cm_page = (utils.addon_sys + "?mode=tnaflix.GotoPage&list_mode=tnaflix.List&url="
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
        url = url.replace('/{}?'.format(np), '/{}?'.format(pg))
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        if url.endswith('/{}'.format(np)):
            url = url.replace('/{}'.format(np), '/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('tnaflix.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    # Find all category/pornstar/channel items
    category_items = soup.select('a.thumb, .thumb-item, .category-item')

    for item in category_items:
        try:
            # Get the category URL
            caturl = utils.safe_get_attr(item, 'href')
            if not caturl:
                continue

            # Make absolute URL
            caturl = utils.fix_url(caturl, site.url)

            # Get image
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'src', ['data-original', 'data-src'])
            if img:
                img = utils.fix_url(img, site.url)

            # Get title
            title_tag = item.select_one('.thumb-title, .title')
            name = utils.safe_get_text(title_tag)
            if not name:
                name = utils.safe_get_attr(img_tag, 'alt', default='Category')
            name = utils.cleantext(name)

            # Get video count
            count_tag = item.select_one('.icon-video-camera')
            if count_tag:
                # Get the text after the icon
                count_text = ''
                if count_tag.next_sibling:
                    count_text = str(count_tag.next_sibling).strip()
                if count_text:
                    name += '[COLOR hotpink] ({} videos)[/COLOR]'.format(count_text)

            site.add_dir(name, caturl, 'List', img)

        except Exception as e:
            utils.kodilog("Error parsing category item: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one('link[rel="next"], a[rel="next"]')
    if next_link:
        next_url = utils.safe_get_attr(next_link, 'href')
        if next_url:
            # Make absolute URL
            next_url = utils.fix_url(next_url, site.url)

            # Extract page numbers for display
            if '/pornstars' in url:
                page_match = re.search(r'page=(\d+)', next_url)
            else:
                page_match = re.search(r'/(\d+)', next_url)

            np = page_match.group(1) if page_match else ''

            # Try to find last page number
            lp = ''
            pagination_links = soup.select('.pagination a, .paginationItem a')
            page_numbers = []
            for link in pagination_links:
                text = utils.safe_get_text(link)
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                lp = str(max(page_numbers))

            # Create context menu for goto page
            cm_page = (utils.addon_sys + "?mode=tnaflix.GotoPage&list_mode=tnaflix.Categories&url="
                      + urllib_parse.quote_plus(next_url) + "&np=" + str(np) + "&lp=" + str(lp))
            cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

            page_label = 'Next Page'
            if np:
                page_label += ' (' + np
                if lp:
                    page_label += '/' + lp
                page_label += ')'

            site.add_dir(page_label, next_url, 'Categories', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}&tab=".format(url, keyword.replace(' ', '+'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'"embedUrl":"([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        embedurl = match[0]
        embedurl = embedurl.replace('/video/', '/ajax/video-player/')
        embedhtml = utils.getHtml(embedurl, url)
        embedhtml = embedhtml.replace('\\/', '/').replace('\\"', '"')
        match = re.compile(r'source src="([^"]+)" type="video/mp4" size="([^"]+)">', re.IGNORECASE | re.DOTALL).findall(embedhtml)
        if match:
            sources = {x[1]: x[0] for x in match}
            if '4' in sources:
                sources['2160'] = sources.pop('4')
            videourl = utils.prefquality(sources, sort_by=lambda x: int(x), reverse=True)

            if videourl:
                videourl = videourl + '|verifypeer=false'
                vp.play_from_direct_link(videourl)

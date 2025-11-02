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
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode
from six.moves import urllib_parse

site = AdultSite('pornhat', '[COLOR hotpink]Pornhat[/COLOR]', 'https://www.pornhat.com/', 'pornhat.png', 'pornhat')
site1 = AdultSite('helloporn', '[COLOR hotpink]Hello Porn[/COLOR]', 'https://hello.porn/', 'helloporn.png', 'helloporn')
site2 = AdultSite('okporn', '[COLOR hotpink]OK Porn[/COLOR]', 'https://ok.porn/', 'okporn.png', 'okporn')
site3 = AdultSite('okxxx', '[COLOR hotpink]OK XXX[/COLOR]', 'https://ok.xxx/', 'okxxx.png', 'okxxx')
site4 = AdultSite('pornstarstube', '[COLOR hotpink]Pornstars Tube[/COLOR]', 'https://pornstars.tube/', 'pornstarstube.png', 'pornstarstube')
site5 = AdultSite('maxporn', '[COLOR hotpink]Max Porn[/COLOR]', 'https://max.porn/', 'maxporn.png', 'maxporn')
site6 = AdultSite('homoxxx', '[COLOR hotpink]Homo XXX[/COLOR]', 'https://homo.xxx/', 'homoxxx.png', 'homoxxx')
site7 = AdultSite('perfectgirls', '[COLOR hotpink]Perfect Girls[/COLOR]', 'https://www.perfectgirls.xxx/', 'https://static.perfectgirls.xxx/static/images/logo.png', 'perfectgirls')


def getSite(url):
    if 'pornhat.com' in url:
        ret = site
    elif 'hello.porn' in url:
        ret = site1
    elif 'ok.porn' in url:
        ret = site2
    elif 'ok.xxx' in url:
        ret = site3
    elif 'pornstars.tube' in url:
        ret = site4
    elif 'max.porn' in url:
        ret = site5
    elif 'homo.xxx' in url:
        ret = site6
    elif 'perfectgirls.xxx' in url:
        ret = site7
    return ret


@site.register(default_mode=True)
@site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
@site5.register(default_mode=True)
@site6.register(default_mode=True)
@site7.register(default_mode=True)
def Main(url):
    siteurl = getSite(url).url
    if 'max.porn' not in url and 'pornstars.tube' not in url:
        site.add_dir('[COLOR hotpink]Channels[/COLOR]', siteurl + 'channels/', 'Cat', site.img_cat)
        if 'hello.porn' in url or 'homo.xxx' in url or 'perfectgirls.xxx' in url:
            site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', siteurl + 'pornstars/videos/', 'Cat', site.img_cat)
        else:
            site.add_dir('[COLOR hotpink]Models[/COLOR]', siteurl + 'models/', 'Cat', site.img_cat)
    if 'pornstars.tube' in url:
        site.add_dir('[COLOR hotpink]Search Pornstars[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    else:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/', 'Search', site.img_search)
    if 'hello' in siteurl or 'homo' in siteurl:
        List(siteurl + 'new/')
    elif 'max.porn' in siteurl or 'pornstars.tube' in siteurl:
        Cat(siteurl)
    else:
        List(siteurl)


@site.register()
def List(url):
    siteurl = getSite(url).url
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Find all video items
    video_items = soup.select('.thumb.thumb-video, .thumb, .item')

    for item in video_items:
        try:
            # Get the video link
            link = item.select_one('a[href*="/video"], a[href*="/watch"]')
            if not link:
                continue

            videopage = utils.safe_get_attr(link, 'href')
            if not videopage:
                continue

            # Make absolute URL if needed
            videopage = siteurl[:-1] + videopage if videopage.startswith('/') else videopage

            # Get title
            name = utils.safe_get_attr(link, 'title')
            if not name:
                img_tag = item.select_one('img')
                name = utils.safe_get_attr(img_tag, 'alt', default='Video')
            name = utils.cleantext(name)

            # Get image
            img_tag = item.select_one('img')
            img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'src'])
            if img and img.startswith('//'):
                img = 'https:' + img

            # Get duration
            duration_tag = item.select_one('.duration_item, .fa-clock-o + span, [class*="duration"]')
            duration = utils.safe_get_text(duration_tag)

            # Create context menu for related videos
            cm_related = (utils.addon_sys + "?mode=pornhat.Related&url=" + urllib_parse.quote_plus(videopage))
            cm = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')')]

            # Add video to list
            getSite(url).add_download_link(name, videopage, 'Play', img, name, duration=duration, contextm=cm)

        except Exception as e:
            # Log error but continue processing other videos
            utils.kodilog("Error parsing video item: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one('a:-soup-contains("Next")')
    if not next_link:
        # Try alternate pagination patterns
        pagination_links = soup.select('.pagination a, .pager a')
        for plink in pagination_links:
            if 'next' in utils.safe_get_text(plink).lower():
                next_link = plink
                break

    if next_link:
        nextp = utils.safe_get_attr(next_link, 'href')
        if nextp:
            nextp = siteurl[:-1] + nextp if nextp.startswith('/') else nextp
            # Extract page number
            page_nums = re.findall(r'\d+', nextp)
            np = page_nums[-1] if page_nums else ''
            site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Cat(url):
    siteurl = getSite(url).url
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    # Check if alphabet selector is present
    alphabet = soup.select_one('.alphabet')
    if alphabet:
        site.add_dir('[COLOR violet]Alphabet[/COLOR]', siteurl, 'Letters', site.img_next)

    # Find all category items - try multiple selectors
    category_items = soup.select('[class*="thumb-bl"], .item, a.item')

    for item in category_items:
        try:
            # Get the category link
            if item.name == 'a':
                link = item
                catpage = utils.safe_get_attr(link, 'href')
            else:
                link = item.select_one('a')
                if not link:
                    continue
                catpage = utils.safe_get_attr(link, 'href')

            if not catpage:
                continue

            # Make absolute URL if needed
            catpage = siteurl[:-1] + catpage if catpage.startswith('/') else catpage

            # Get title
            name = utils.safe_get_attr(link, 'title')
            if not name:
                title_tag = item.select_one('.title, h3')
                name = utils.safe_get_text(title_tag) if title_tag else ''
            if not name:
                img_tag = item.select_one('img')
                name = utils.safe_get_attr(img_tag, 'alt', default='Category')
            name = utils.cleantext(name)

            # Get image
            img_tag = item.select_one('img')
            if 'max.porn' in url:
                img = utils.safe_get_attr(img_tag, 'data-src', ['src'])
            else:
                img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original'])
            if img and img.startswith('//'):
                img = 'https:' + img

            # Get video count
            videos = ''
            # Try to find video count in various formats
            for text in item.stripped_strings:
                if 'video' in text.lower() or text.replace(' ', '').isdigit():
                    # Clean up video count text
                    cleaned = text.strip()
                    if cleaned and ('video' in cleaned.lower() or cleaned.replace(' ', '').replace('(', '').replace(')', '').isdigit()):
                        videos = cleaned
                        break

            if videos:
                name += ' [COLOR hotpink]' + videos + '[/COLOR]'

            site.add_dir(name, catpage, 'List', img)

        except Exception as e:
            utils.kodilog("Error parsing category item: " + str(e))
            continue

    # Handle pagination
    next_link = soup.select_one('a:-soup-contains("Next")')
    if not next_link:
        # Try alternate pagination patterns
        pagination_links = soup.select('.pagination a, .pager a')
        for plink in pagination_links:
            if 'next' in utils.safe_get_text(plink).lower():
                next_link = plink
                break

    if next_link:
        nextp = utils.safe_get_attr(next_link, 'href')
        if nextp:
            nextp = siteurl[:-1] + nextp if nextp.startswith('/') else nextp
            # Extract page number
            page_nums = re.findall(r'\d+', nextp)
            np = page_nums[-1] if page_nums else ''

            # Try to find last page number
            lp = ''
            last_page_tag = soup.select_one('.pagination-last')
            if last_page_tag:
                lp_text = utils.safe_get_text(last_page_tag)
                if lp_text.isdigit():
                    lp = '/' + lp_text

            site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0}{1})'.format(np, lp), nextp, 'Cat', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}/".format(url, keyword.replace(' ', '-'))
        if 'pornstars.tube' in url:
            Cat(url)
        else:
            List(url)


@site.register()
def Play(url, name, download=None):
    siteurl = getSite(url).url
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    vpage = utils.getHtml(url, siteurl)
    sources = {}
    if 'license_code:' in vpage:
        license = re.compile(r"license_code:\s*'([^']+)", re.DOTALL | re.IGNORECASE).findall(vpage)[0]
        patterns = [r"video_url:\s*'([^']+)[^;]+?video_url_text:\s*'([^']+)",
                    r"video_alt_url:\s*'([^']+)[^;]+?video_alt_url_text:\s*'([^']+)",
                    r"video_alt_url2:\s*'([^']+)[^;]+?video_alt_url2_text:\s*'([^']+)",
                    r"video_url:\s*'([^']+)',\s*postfix:\s*'\.mp4',\s*(preview)"]
        for pattern in patterns:
            items = re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(vpage)
            for surl, qual in items:
                qual = '00' if qual == 'preview' else qual
                surl = kvs_decode(surl, license)
                sources.update({qual: surl})
    elif '<source' in vpage:
        sources = re.compile(r'<source\s*src="([^"]+)".+?label="([^"]+)', re.DOTALL | re.IGNORECASE).findall(vpage)
        sources = {quality: videourl for videourl, quality in sources if quality.lower() != 'auto'}
    else:
        vp.progress.close()
        return

    videourl = utils.selector('Select quality', sources, setting_valid='qualityask', sort_by=lambda x: 1081 if x.lower() == '4k' else int(x[:-1]), reverse=True)

    if not videourl:
        vp.progress.close()
        return
    videourl = utils.getVideoLink(videourl, siteurl)
    vp.play_from_direct_link(videourl)


@site.register()
def Letters(url):
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    letter = utils.selector('Select letter', letters)
    if letter:
        if 'hello.porn' in url:
            Cat(url + 'pornstars/' + letter + '/')
        elif 'max.porn' in url or 'pornstars.tube' in url:
            Cat(url + letter + '/')
        else:
            Cat(url + 'models/abc/?section=' + letter)


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + "pornhat.List&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')

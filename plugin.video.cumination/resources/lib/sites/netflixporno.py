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
import base64
from six.moves import urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

progress = utils.progress

site = AdultSite('netflixporno', '[COLOR hotpink]NetflixPorno[/COLOR]', 'https://netflixporno.net/', 'netflixporno.png', 'netflixporno')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]XXX Scenes[/COLOR]', site.url + 'scenes/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Parody Movies[/COLOR]', site.url + 'adult/genre/parodies/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'adult/genre/parodies/', 'Studios', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'adult/genre/parodies/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'adult')
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    if len(listhtml) == 0:
        listhtml = 'Empty'

    # Parse with BeautifulSoup
    soup = utils.parse_html(listhtml)

    # Extract video items from article elements
    articles = soup.select('article')
    for article in articles:
        try:
            # Get video link
            link = article.select_one('a')
            if not link:
                continue
            videopage = utils.safe_get_attr(link, 'href')
            if not videopage:
                continue

            # Get thumbnail image (try data-lazy-src first, then src)
            img_tag = article.select_one('img')
            img = utils.safe_get_attr(img_tag, 'data-lazy-src', ['src'])
            if img and '.jpg' not in img:
                img = utils.safe_get_attr(img_tag, 'src')

            # Get title from div with 'Title' class or containing 'Title'
            title_div = article.select_one('[class*="Title"]')
            name = utils.safe_get_text(title_div)
            if not name:
                continue

            name = utils.cleantext(name)
            site.add_download_link(name, videopage, 'Playvid', img, '')
        except Exception as e:
            utils.log('Error parsing video item: {}'.format(e))
            continue

    # Handle pagination with BeautifulSoup
    next_link = soup.select_one('a.next.page-numbers')
    if next_link:
        nextp = utils.safe_get_attr(next_link, 'href', default='').replace("&#038;", "&")
        if nextp:
            # Get current and last page numbers
            current_page = soup.select_one('.page-numbers.current')
            currpg = utils.safe_get_text(current_page, '1')

            # Find last page number (the link before the "next" button)
            page_numbers = soup.select('.page-numbers:not(.next):not(.prev):not(.current)')
            lastpg = currpg
            for page_num in page_numbers:
                page_text = utils.safe_get_text(page_num)
                if page_text.isdigit():
                    lastpg = page_text

            site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(currpg, lastpg), nextp, 'List', site.img_next)

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
def Categories(url):
    try:
        cathtml = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return

    # Parse with BeautifulSoup
    soup = utils.parse_html(cathtml)

    # Find category items (li elements with class starting with "cat-item-")
    cat_items = soup.select('li[class*="cat-item-"]')
    for cat_item in cat_items:
        try:
            link = cat_item.select_one('a')
            if not link:
                continue

            catpage = utils.safe_get_attr(link, 'href')
            name = utils.safe_get_text(link)

            if catpage and name:
                site.add_dir(name, catpage, 'List', site.img_cat)
        except Exception as e:
            utils.log('Error parsing category item: {}'.format(e))
            continue

    utils.eod()


@site.register()
def Studios(url):
    try:
        studhtml = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return

    # Parse with BeautifulSoup
    soup = utils.parse_html(studhtml)

    # Find studio/director menu items (li elements with class containing "director" and "menu-item")
    studio_items = soup.select('li[class*="director"][class*="menu-item"]')
    for studio_item in studio_items:
        try:
            link = studio_item.select_one('a')
            if not link:
                continue

            studpage = utils.safe_get_attr(link, 'href')
            name = utils.safe_get_text(link)

            if studpage and name:
                site.add_dir(name, studpage, 'List', site.img_cat)
        except Exception as e:
            utils.log('Error parsing studio item: {}'.format(e))
            continue

    utils.eod()


def url_decode(str):
    if '/goto/' not in str:
        result = str
    else:
        try:
            result = url_decode(base64.b64decode(re.search('/goto/(.+)', str).group(1)))
        except:
            result = str
    return result


@site.register()
def Playvid(url, name, download=None):
    links = {}
    videourl = None
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    try:
        html = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    srcs = re.compile(r'<a\s*title="([^"]+)"\s*href="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(html)
    for title, src in srcs:
        title = utils.cleantext(title)
        title = title.split(' on ')[-1]
        src = src.split('?link=')[-1]
        if '/goto/' in src:
            src = url_decode(src)
        if 'mangovideo' in src:
            html = utils.getHtml(src, url)
            if '=' in src:
                src = src.split('=')[-1]
            murl = re.compile(r"video_url:\s*'([^']+)'", re.DOTALL | re.IGNORECASE).findall(html)
            if murl:
                if murl[0].startswith('function/'):
                    license = re.findall(r"license_code:\s*'([^']+)", html)[0]
                    murl = kvs_decode(murl[0], license)
            else:
                murl = re.compile(r'action=[^=]+=([^\?]+)/\?download', re.DOTALL | re.IGNORECASE).findall(html)
                if murl:
                    murl = murl[0]
            if murl:
                links[title] = murl
        elif vp.resolveurl.HostedMediaFile(src).valid_url():
            links[title] = src
    if links:
        videourl = utils.selector('Select server', links, setting_valid=False)
    if not videourl:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Playable Videos found')
        return
    vp.progress.update(90, "[CR]Loading video page[CR]")
    if 'mango' in videourl:
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)

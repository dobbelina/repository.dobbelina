'''
    Cumination
    Copyright (C) 2020 Cumination

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
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite

site = AdultSite('cambro', '[COLOR hotpink]Cambro[/COLOR]', 'https://www.cambro.tv/', 'cambro.png', 'cambro')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/1/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR]', site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by=&from=01', 'Playlist', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&category_ids=&sort_by=&from_videos=01&q=', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    seen = set()
    items = soup.select('div.item')
    for item in items:
        classes = [cls.lower() for cls in item.get('class', [])]
        if any('private' in cls for cls in classes):
            continue

        link = item.select_one('a[href]')
        if not link:
            continue

        video = utils.safe_get_attr(link, 'href')
        if not video:
            continue
        video = urllib_parse.urljoin(url, video)
        if video in seen:
            continue
        seen.add(video)

        name = utils.safe_get_attr(link, 'title')
        if not name:
            title_tag = item.select_one('.title, .video-title, h3')
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_text(link)
        name = utils.cleantext(name) if name else 'Video'

        img_tag = item.select_one('img[data-original], img[data-src], img[src]')
        img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'src'])
        if img and img.startswith('//'):
            img = 'https:' + img

        duration_tag = item.select_one('.duration, .time, .video-duration, .value')
        duration = utils.safe_get_text(duration_tag)

        hd = ''
        if item.select_one('.hd, .is-hd, .label-hd, .video-hd, .quality-hd, .hd-icon'):
            hd = 'HD'
        elif ' HD' in item.get_text(' ', strip=True).upper():
            hd = 'HD'

        site.add_download_link(name, video, 'Playvid', img, name, duration=duration, quality=hd)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a, a.next, a[rel="next"]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_page = urllib_parse.urljoin(url, next_href)
                page_num = None
                match = re.search(r'/([0-9]+)/?$', next_page.rstrip('/'))
                if match:
                    page_num = match.group(1)
                else:
                    match = re.search(r'from_(?:videos|items)=([0-9]+)', next_page)
                    if match:
                        page_num = str(int(match.group(1)))

                last_link = pagination.select_one('li.last a, a.last')
                last_num = None
                if last_link:
                    last_href = utils.safe_get_attr(last_link, 'href')
                    if last_href:
                        lm = re.search(r'/([0-9]+)/?$', last_href.rstrip('/'))
                        if lm:
                            last_num = lm.group(1)

                if page_num and last_num:
                    label = 'Next Page ({}/{})'.format(page_num, last_num)
                elif page_num:
                    label = 'Next Page ({})'.format(page_num)
                else:
                    label = 'Next Page'
                site.add_dir(label, next_page, 'List', site.img_next)

    utils.eod()


@site.register()
def List2(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    seen = set()
    items = soup.select('div.item')
    for item in items:
        video = item.get('data-item')
        if not video:
            link = item.select_one('a[href]')
            video = utils.safe_get_attr(link, 'href') if link else None
        if not video:
            continue
        video = urllib_parse.urljoin(url, video)
        if video in seen:
            continue
        seen.add(video)

        img_tag = item.select_one('img[data-original], img[data-src], img[src]')
        img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'src'])
        if img and img.startswith('//'):
            img = 'https:' + img

        title_tag = item.select_one('.title, .video-title, a[title]')
        name = utils.safe_get_attr(title_tag, 'title') if title_tag else None
        if not name:
            name = utils.safe_get_text(title_tag)
        if not name:
            link = item.select_one('a[href]')
            name = utils.safe_get_attr(link, 'title') or utils.safe_get_text(link)
        name = utils.cleantext(name) if name else 'Video'

        site.add_download_link(name, video, 'Playvid', img, name)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a, a.next, a[rel="next"]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_page = urllib_parse.urljoin(url, next_href)
                page_num = None
                match = re.search(r'/([0-9]+)/?$', next_page.rstrip('/'))
                if match:
                    page_num = match.group(1)
                else:
                    match = re.search(r'from=([0-9]+)', next_page)
                    if match:
                        page_num = match.group(1)

                last_link = pagination.select_one('li.last a, a.last')
                last_num = None
                if last_link:
                    last_href = utils.safe_get_attr(last_link, 'href')
                    if last_href:
                        lm = re.search(r'/([0-9]+)/?$', last_href.rstrip('/'))
                        if lm:
                            last_num = lm.group(1)

                if page_num and last_num:
                    label = 'Next Page ({}/{})'.format(page_num, last_num)
                elif page_num:
                    label = 'Next Page ({})'.format(page_num)
                else:
                    label = 'Next Page'
                site.add_dir(label, next_page, 'List2', site.img_next)

    utils.eod()


@site.register()
def Playlist(url):
    listhtml = utils.getHtml(url)
    soup = utils.parse_html(listhtml)

    seen = set()
    items = soup.select('div.item')
    for item in items:
        link = item.select_one('a[href]')
        if not link:
            continue
        lpage = utils.safe_get_attr(link, 'href')
        if not lpage:
            continue
        lpage = urllib_parse.urljoin(url, lpage)
        if lpage in seen:
            continue
        seen.add(lpage)

        img_tag = item.select_one('img[data-original], img[data-src], img[src]')
        img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'src'])
        if img and img.startswith('//'):
            img = 'https:' + img

        title_tag = item.select_one('.title, .video-title, a[title]')
        name = utils.safe_get_attr(title_tag, 'title') if title_tag else None
        if not name:
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_attr(link, 'title') or utils.safe_get_text(link)
        name = utils.cleantext(name) if name else 'Playlist'

        count_tag = item.select_one('.videos, .totalplaylist, .count, .video-count')
        count = utils.safe_get_text(count_tag)
        if count:
            name = name + "[COLOR deeppink] {0}[/COLOR]".format(count)

        lpage = lpage + '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=&from=01'
        site.add_dir(name, lpage, 'List2', img)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a, a.next, a[rel="next"]')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_page = urllib_parse.urljoin(url, next_href)
                page_num = None
                match = re.search(r'/([0-9]+)/?$', next_page.rstrip('/'))
                if match:
                    page_num = match.group(1)
                else:
                    match = re.search(r'from=([0-9]+)', next_page)
                    if match:
                        page_num = match.group(1)

                last_link = pagination.select_one('li.last a, a.last')
                last_num = None
                if last_link:
                    last_href = utils.safe_get_attr(last_link, 'href')
                    if last_href:
                        lm = re.search(r'/([0-9]+)/?$', last_href.rstrip('/'))
                        if lm:
                            last_num = lm.group(1)

                if page_num and last_num:
                    label = 'Next Page ({}/{})'.format(page_num, last_num)
                elif page_num:
                    label = 'Next Page ({})'.format(page_num)
                else:
                    label = 'Next Page'
                site.add_dir(label, next_page, 'Playlist', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title  # + '/'
        List(searchUrl)


@site.register()
def Tags(url):
    html = utils.getHtml(url)
    soup = utils.parse_html(html)

    for anchor in soup.select('li a[href]'):
        tagpage = utils.safe_get_attr(anchor, 'href')
        if not tagpage:
            continue
        tagpage = urllib_parse.urljoin(url, tagpage)
        name = utils.safe_get_text(anchor)
        name = utils.cleantext(name)
        site.add_dir(name, tagpage, 'List')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    soup = utils.parse_html(cathtml)

    seen = set()
    for anchor in soup.select('a.item[href], div.item a[href]'):
        catpage = utils.safe_get_attr(anchor, 'href')
        if not catpage:
            continue
        catpage = urllib_parse.urljoin(url, catpage)
        if catpage in seen:
            continue
        seen.add(catpage)

        name = utils.safe_get_attr(anchor, 'title')
        if not name:
            title_tag = anchor.select_one('.title, .video-title') if hasattr(anchor, 'select_one') else None
            name = utils.safe_get_text(title_tag) if title_tag else utils.safe_get_text(anchor)
        name = utils.cleantext(name) if name else 'Category'

        parent = anchor
        if anchor.parent and hasattr(anchor.parent, 'select_one'):
            parent = anchor.parent

        img_tag = parent.select_one('img[data-original], img[data-src], img[src]')
        img = utils.safe_get_attr(img_tag, 'data-original', ['data-src', 'src']) if img_tag else None
        if img and img.startswith('//'):
            img = 'https:' + img

        count_tag = parent.select_one('.videos, .count, .totalplaylist, .video-count')
        videos = utils.safe_get_text(count_tag)
        if videos:
            name = name + " [COLOR deeppink]" + videos + "[/COLOR]"

        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Models(url):
    html = utils.getHtml(url)
    soup = utils.parse_html(html)

    seen = set()
    items = soup.select('div.item')
    for item in items:
        link = item.select_one('a[href]')
        if not link:
            continue
        murl = utils.safe_get_attr(link, 'href')
        if not murl:
            continue
        murl = urllib_parse.urljoin(url, murl)
        if murl in seen:
            continue
        seen.add(murl)

        img_tag = item.select_one('img[src], img[data-src], img[data-original]')
        img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original']) if img_tag else None
        if img and img.startswith('//'):
            img = 'https:' + img

        title_tag = item.select_one('.title, .model-name, a[title]')
        name = utils.safe_get_attr(title_tag, 'title') if title_tag else None
        if not name:
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_attr(link, 'title') or utils.safe_get_text(link)
        name = utils.cleantext(name) if name else 'Model'

        count_tag = item.select_one('.videos, .count, .video-count')
        videos = utils.safe_get_text(count_tag)
        if videos:
            name = name + " [COLOR deeppink]" + videos + "[/COLOR]"

        site.add_dir(name, murl, 'List', img)

    pagination = soup.select_one('.pagination')
    if pagination:
        next_link = pagination.select_one('li.next a, a.next, a[rel="next"]')
        last_link = pagination.select_one('li.last a, a.last')
        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_page = urllib_parse.urljoin(url, next_href)
                next_num = None
                nm = re.search(r'/([0-9]+)/?$', next_page.rstrip('/'))
                if nm:
                    next_num = nm.group(1)
                last_num = None
                if last_link:
                    last_href = utils.safe_get_attr(last_link, 'href')
                    if last_href:
                        lm = re.search(r'/([0-9]+)/?$', last_href.rstrip('/'))
                        if lm:
                            last_num = lm.group(1)
                if next_num and last_num:
                    label = 'Next Page ( {0} / {1} )'.format(next_num, last_num)
                elif next_num:
                    label = 'Next Page ({})'.format(next_num)
                else:
                    label = 'Next Page'
                site.add_dir(label, next_page, 'Models', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url)
    surl = re.search(r"video_url:\s*'([^']+)'", html)
    if surl:
        surl = surl.group(1)
        if surl.startswith('function/'):
            license = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, license)
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(surl)

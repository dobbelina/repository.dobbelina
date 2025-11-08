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
from six.moves import urllib_parse
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
    if not listhtml:
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    video_items = soup.select('div.thumb.item')
    for item in video_items:
        top_link = item.select_one('a.thumb__top')
        videopage = utils.safe_get_attr(top_link, 'href')
        if not videopage:
            continue
        videopage = urllib_parse.urljoin(site.url, videopage)

        img_tag = item.select_one('.thumb__img img') or item.select_one('img')
        title_tag = item.select_one('.thumb__title span') or item.select_one('.thumb__title')
        name = utils.safe_get_text(title_tag) or utils.safe_get_attr(img_tag, 'alt') or utils.safe_get_attr(top_link, 'title')
        name = utils.cleantext(name or '')
        if not name:
            continue

        img = utils.safe_get_attr(img_tag, 'data-src', ['data-original', 'data-lazy', 'src', 'srcset'])
        if not img:
            continue
        if ',' in img:
            img = img.split(',', 1)[0]
        if ' ' in img:
            img = img.split()[0]
        img = urllib_parse.urljoin(site.url, img.strip())

        duration = utils.safe_get_text(item.select_one('.thumb__duration'))
        qual_text = (utils.safe_get_text(item.select_one('.thumb__bage, .thumb__badge')) or '').lower()
        if qual_text == '720p':
            hd_text = 'HD '
        elif qual_text == '1080p':
            hd_text = 'FHD '
        elif qual_text == '2160p':
            hd_text = '4K '
        else:
            hd_text = ''

        site.add_download_link(name, videopage, 'Play', img, name, duration=duration, quality=hd_text)

    pagination = None
    thumbs_list = soup.select_one('div.thumbs-list')
    if thumbs_list:
        pagination = thumbs_list.find_next_sibling('div', class_='pagination')
    if not pagination:
        pagination = soup.select_one('.pagination')

    if pagination:
        next_link = None
        for anchor in pagination.select('a.pagination__link'):
            if utils.safe_get_text(anchor).lower() == 'next':
                next_link = anchor
                break

        if next_link:
            next_href = utils.safe_get_attr(next_link, 'href')
            if next_href:
                next_page = urllib_parse.urljoin(url, next_href)
                next_hint = ''
                match = re.search(r'/(\d+)/?$', next_href)
                if match:
                    next_hint = match.group(1)

                last_hint = ''
                for anchor in pagination.select('a.pagination__link'):
                    if 'last' in utils.safe_get_text(anchor).lower():
                        lp_href = utils.safe_get_attr(anchor, 'href')
                        lp_match = re.search(r'/(\d+)/?$', lp_href or '')
                        if lp_match:
                            last_hint = lp_match.group(1)
                        break

                if next_hint:
                    label_hint = '{}/{}'.format(next_hint, last_hint) if last_hint else next_hint
                    label = 'Next Page... ({})'.format(label_hint)
                else:
                    label = 'Next Page...'

                site.add_dir(label, next_page, 'List', site.img_next)

    utils.eod()


@site.register()
def Cat(url):
    listhtml = utils.getHtml(url)
    if not listhtml:
        utils.eod()
        return

    soup = utils.parse_html(listhtml)
    for anchor in soup.select('div.letter-block__item a.letter-block__link'):
        catpage = utils.safe_get_attr(anchor, 'href')
        name = utils.safe_get_text(anchor.select_one('span')) or utils.safe_get_text(anchor)
        if not catpage or not name:
            continue
        catpage = urllib_parse.urljoin(site.url, catpage)
        site.add_dir(utils.cleantext(name), catpage, 'List', '')
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
    if not html:
        vp.progress.close()
        return

    soup = utils.parse_html(html)
    sources = {}
    for link in soup.select('a.video-links__link[no-load-content]'):
        href = utils.safe_get_attr(link, 'href')
        label = utils.safe_get_text(link)
        quality = label.split()[0] if label else ''
        if not href or not quality:
            continue
        sources[quality] = urllib_parse.urljoin(url, href)

    videourl = utils.prefquality(sources, reverse=True) if sources else None
    if not videourl:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.progress.close()
    if download == 1:
        utils.downloadVideo(videourl, name)
    else:
        vp.play_from_direct_link(videourl)

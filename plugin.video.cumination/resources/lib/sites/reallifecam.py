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
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.jsunpack import unpack
from resources.lib.adultsite import AdultSite

site = AdultSite('rlc', '[COLOR hotpink]Reallifecam.to[/COLOR]', 'https://reallifecam.to/', 'https://reallifecam.to/images/logo/logo.png', 'rlc')
# site1 = AdultSite('vh', '[COLOR hotpink]Voyeur-house.to[/COLOR]', 'https://voyeur-house.to/', 'https://voyeur-house.to/images/logo/logo.png', 'vh')
site2 = AdultSite('vhlife', '[COLOR hotpink]Voyeur-house.cc[/COLOR]', 'https://www.voyeur-house.cc/', 'https://www.voyeur-house.cc/images/logo/logo.png', 'vhlife')
site3 = AdultSite('vhlife1', '[COLOR hotpink]Reallifecams.in[/COLOR]', 'https://www.reallifecams.in/', 'https://www.reallifecams.in/images/logo/logo.png', 'vhlife1')
site4 = AdultSite('camcaps', '[COLOR hotpink]Camcaps.to[/COLOR]', 'https://camcaps.to/', 'https://camcaps.to/images/logo/logo.png', 'camcapsto')


def getBaselink(url):
    if 'reallifecam.to' in url:
        siteurl = site.url
    # elif 'voyeur-house.to' in url:
    #     siteurl = site1.url
    elif 'voyeur-house.cc' in url:
        siteurl = site2.url
    elif 'reallifecams.in' in url:
        siteurl = site3.url
    elif 'camcaps.to' in url:
        siteurl = site4.url
    return siteurl


@site.register(default_mode=True)
# @site1.register(default_mode=True)
@site2.register(default_mode=True)
@site3.register(default_mode=True)
@site4.register(default_mode=True)
def Main(url):
    siteurl = getBaselink(url)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', siteurl + 'categories', 'Categories', site.img_cat)
    if 'camcaps.to' in url:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/videos/', 'Search', site.img_search)
    else:
        site.add_dir('[COLOR hotpink]Search[/COLOR]', siteurl + 'search/videos?search_query=', 'Search', site.img_search)
    List(siteurl + 'videos?o=mr')


@site.register()
def List(url):
    siteurl = getBaselink(url)
    listhtml = utils.getHtml(url, '')

    soup = utils.parse_html(listhtml)

    seen = set()
    cards = soup.select('.col-sm-6, .video-item, .item')
    for card in cards:
        link = card.select_one('a[href]')
        if not link:
            continue

        videopage = utils.safe_get_attr(link, 'href')
        if not videopage:
            continue
        videopage = urllib_parse.urljoin(siteurl, videopage)
        if videopage in seen:
            continue
        seen.add(videopage)

        name = utils.safe_get_attr(link, 'title')
        if not name:
            title_tag = card.select_one('.title-truncate, .title, h3, h4')
            name = utils.safe_get_text(title_tag)
        if not name:
            name = utils.safe_get_text(link)
        name = utils.cleantext(name)
        if not name:
            name = 'Video'

        img_tag = card.select_one('img[data-src], img[data-original], img[src]')
        img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original']) if img_tag else None
        if img and img.startswith('//'):
            img = 'https:' + img
        elif img and img.startswith('/'):
            img = urllib_parse.urljoin(siteurl, img)

        duration_tag = card.select_one('.duration, .time, .video-duration, .clock, .label-duration')
        duration = utils.safe_get_text(duration_tag)

        hd = ''
        quality_tag = card.select_one('.badge, .label, .quality, .hd, .label-hd')
        if quality_tag and 'HD' in quality_tag.get_text().upper():
            hd = 'HD'

        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration, quality=hd)

    next_link = soup.select_one('a.prevnext[href], .pagination li.next a, a[rel="next"]')
    if next_link:
        next_page = utils.safe_get_attr(next_link, 'href')
        if next_page:
            next_page = urllib_parse.urljoin(siteurl, next_page)
            page_nr = ''
            match = re.findall(r'\d+', next_page)
            if match:
                page_nr = match[-1]
            label = 'Next Page ({})'.format(page_nr) if page_nr else 'Next Page'
            site.add_dir(label, next_page, 'List', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '%20')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    siteurl = getBaselink(url)
    cathtml = utils.getHtml(url, '')
    soup = utils.parse_html(cathtml)

    seen = set()
    containers = soup.select('.col-sm, .col-sm-6, .category, .category-item, .list-group-item')
    for container in containers:
        link = container.select_one('a[href]')
        if not link:
            continue

        catpage = utils.safe_get_attr(link, 'href')
        if not catpage:
            continue
        catpage = urllib_parse.urljoin(siteurl, catpage)
        if catpage in seen:
            continue
        seen.add(catpage)

        img_tag = container.select_one('img[data-src], img[data-original], img[src]')
        img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original']) if img_tag else site.img_cat
        if img and img.startswith('//'):
            img = 'https:' + img
        elif img and img.startswith('/'):
            img = urllib_parse.urljoin(siteurl, img)

        name_tag = container.select_one('.title-truncate, .title, h4, h3, .name')
        name = utils.safe_get_text(name_tag) if name_tag else utils.safe_get_text(link)
        name = utils.cleantext(name.strip()).title()
        if not name:
            name = 'Category'

        count_tag = container.select_one('.badge, .float-right, .videos, .video-count, .count')
        videos = utils.safe_get_text(count_tag)
        if videos:
            name = name + " [COLOR deeppink]" + videos + "[/COLOR]"

        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videopage = utils.getHtml(url)

    soup = utils.parse_html(videopage)
    iframe = soup.select_one('.video-embedded iframe, iframe[src]')
    refurl = utils.safe_get_attr(iframe, 'src') if iframe else None
    if refurl:
        if '/vtplayer.net/' in refurl:
            refurl = refurl.replace('embed-', '')
        if vp.resolveurl.HostedMediaFile(refurl):
            vp.play_from_link_to_resolve(refurl)
            return
        refpage = utils.getHtml(refurl)
        if '/playerz/' in refurl:
            videourl = re.compile(r'"src":"\.([^"]+)"', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
            videourl = refurl.split('/ss.php')[0] + videourl
            videourlpage = utils.getHtml(videourl)
            vp.direct_regex = '{"file":"([^"]+)"'
            vp.play_from_html(videourlpage)
        else:
            videourl = re.compile(r'>(eval.+?)<\/script>', re.DOTALL | re.IGNORECASE).findall(refpage)[0]
            videourl = unpack(videourl)
            videolink = re.compile('(?:src|file):"([^"]+)"', re.DOTALL | re.IGNORECASE).findall(videourl)
            if match:
                videolink = videolink[0] + '|Referer=' + refurl + '&verifypeer=false'
                if videolink.startswith('/') and 'vidello' in refurl:
                    videolink = 'https://oracle.vidello.net' + videolink
                vp.play_from_direct_link(videolink)
    else:
        vp.play_from_html(videopage)

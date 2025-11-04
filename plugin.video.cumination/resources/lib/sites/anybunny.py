'''
    Cumination
    Copyright (C) 2015 Whitecream

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

site = AdultSite("anybunny", "[COLOR hotpink]Anybunny[/COLOR]", "http://anybunny.org/", "anybunny.png", "anybunny")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Top videos[/COLOR]', site.url + 'top/', 'List', '', '')
    site.add_dir('[COLOR hotpink]Categories - images[/COLOR]', site.url, 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories - all[/COLOR]', site.url, 'Categories2', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'new/', 'Search', site.img_search)
    List(site.url + 'new/?p=1')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, '')
    soup = utils.parse_html(listhtml)

    video_items = soup.select('a.nuyrfe, a[href*="/videos/"]')
    for item in video_items:
        videopage = utils.safe_get_attr(item, 'href')
        if not videopage:
            continue

        videopage = urllib_parse.urljoin(site.url, videopage)

        img_tag = item.select_one('img')
        img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-lazy', 'data-original'])

        name = utils.safe_get_attr(img_tag, 'alt')
        if not name:
            name = utils.safe_get_text(item)
        name = utils.cleantext(name)

        if not name:
            continue

        site.add_download_link(name, videopage, 'Playvid', img, '')

    next_link = (
        soup.find('a', attrs={'rel': 'next'})
        or soup.find('a', class_=lambda c: c and 'next' in c.lower())
        or soup.find('a', string=lambda s: s and 'next' in s.lower())
    )

    next_url = utils.safe_get_attr(next_link, 'href') if next_link else ''
    if next_url:
        next_url = urllib_parse.urljoin(site.url, next_url)
        site.add_dir('Next Page', next_url, 'List', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, direct_regex=r"source src=\\'([^']+)\\'")
    vp.play_from_site_link(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url, '')
    soup = utils.parse_html(cathtml)

    categories = []
    for anchor in soup.select("a[href*='/top/']"):
        img_tag = anchor.select_one('img')
        if not img_tag:
            continue

        href = utils.safe_get_attr(anchor, 'href')
        if '/top/' not in href:
            continue

        try:
            catid = href.split('/top/', 1)[1]
        except IndexError:
            continue

        name = utils.safe_get_attr(img_tag, 'alt')
        if not name:
            name = utils.safe_get_text(anchor)
        name = utils.cleantext(name)
        if not name:
            continue

        img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-lazy', 'data-original'])
        catpage = urllib_parse.urljoin(site.url, 'new/' + catid.lstrip('/'))
        categories.append((name.lower(), name, catpage, img))

    seen = set()
    for _, display_name, catpage, img in sorted(categories):
        if catpage in seen:
            continue
        seen.add(catpage)
        site.add_dir(display_name, catpage, 'List', img)
    utils.eod()


@site.register()
def Categories2(url):
    cathtml = utils.getHtml(url, '')
    soup = utils.parse_html(cathtml)

    entries = []
    for anchor in soup.select("a[href*='/top/']"):
        href = utils.safe_get_attr(anchor, 'href')
        if '/top/' not in href:
            continue

        try:
            catid = href.split('/top/', 1)[1]
        except IndexError:
            continue

        name = utils.cleantext(utils.safe_get_text(anchor))
        if not name:
            continue

        videos = ''
        for sibling in anchor.next_siblings:
            if isinstance(sibling, str):
                text = sibling.strip()
            else:
                text = utils.safe_get_text(sibling)

            if not text:
                continue

            match = re.search(r'\(([^)]+)\)', text)
            if match:
                videos = match.group(1)
                break

        label = name
        if videos:
            label = f"{name} [COLOR deeppink]({videos})[/COLOR]"

        catpage = urllib_parse.urljoin(site.url, 'new/' + catid.lstrip('/'))
        entries.append((name.lower(), label, catpage))

    seen = set()
    for _, label, catpage in sorted(entries):
        if catpage in seen:
            continue
        seen.add(catpage)
        site.add_dir(label, catpage, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '_')
        searchUrl = searchUrl + title
        List(searchUrl)

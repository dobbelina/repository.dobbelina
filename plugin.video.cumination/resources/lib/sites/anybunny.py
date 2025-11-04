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

    selectors = {
        'items': ['a.nuyrfe', 'a[href*="/videos/"]'],
        'url': {'attr': 'href'},
        'title': {
            'selector': 'img',
            'attr': 'alt',
            'text': True,
            'clean': True,
            'fallback_selectors': [None]
        },
        'thumbnail': {
            'selector': 'img',
            'attr': 'src',
            'fallback_attrs': ['data-src', 'data-lazy', 'data-original']
        },
        'pagination': {
            'selectors': [
                {'query': 'a[rel="next"]', 'scope': 'soup'},
                {'query': 'a.next', 'scope': 'soup'}
            ],
            'text_matches': ['next'],
            'attr': 'href',
            'label': 'Next Page',
            'mode': 'List'
        }
    }

    utils.soup_videos_list(site, soup, selectors, play_mode='Playvid', description='')

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

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

site = AdultSite('justporn', "[COLOR hotpink]JustPorn[/COLOR]", 'https://justporn.com/', 'justporn.png', 'justporn')


def _extract_meta_text(item):
    """Extract metadata text such as duration or quality from ``item``.

    The helper walks through a series of CSS selectors looking for child
    elements that expose duration/quality text or ``data-duration`` attributes.
    If no child element matches, it falls back to reading the
    ``data-duration``/``data-length`` attributes directly from the item.

    Args:
        item: A BeautifulSoup tag (or tag-like object) representing a video
            entry. Expected to support ``select_one`` for CSS lookups and
            ``get`` for attribute access.

    Returns:
        str: Extracted metadata text, or an empty string when unavailable.
    """
    meta_selectors = [
        '.thumb-info',
        '.thumb__meta',
        '.content__meta',
        '.content-info',
        '.video-info',
        '.meta',
        '.time',
        '.thumb .time',
        '[data-duration]'
    ]

    for selector in meta_selectors:
        tag = item.select_one(selector) if hasattr(item, 'select_one') else None
        if tag:
            text = utils.safe_get_text(tag, default='', strip=True)
            if text:
                return text
            data_duration = utils.safe_get_attr(tag, 'data-duration', default='')
            if data_duration:
                return data_duration

    if hasattr(item, 'get'):
        for attr_name in ('data-duration', 'data-length'):
            data_attr = item.get(attr_name) or ''
            if data_attr:
                return data_attr

    return ''


def _duration_transform(value, item):
    """Normalize duration strings extracted from a video ``item``.

    Args:
        value (str): Initial duration value provided by upstream extraction (may be empty).
        item: BeautifulSoup tag (or tag-like object) for the video entry.

    Returns:
        str: A ``MM:SS`` duration string when detected, otherwise ``''``.
    """

    candidates = [value or '']
    meta_text = _extract_meta_text(item)
    if meta_text:
        candidates.insert(0, meta_text)

    for text in candidates:
        if not text:
            continue
        match = re.search(r'(\d{1,2}:\d{2})', text)
        if match:
            return match.group(1)
    return ''


def _quality_transform(value, item):
    """Return ``'HD'`` when high-definition metadata is detected for ``item``.

    Args:
        value (str): Initial quality indicator extracted by selectors (may be empty).
        item: BeautifulSoup tag (or tag-like object) for the video entry.

    Returns:
        str: ``'HD'`` when HD keywords are detected, otherwise ``''``.

    The helper inspects both the provided value and any metadata text discovered
    via :func:`_extract_meta_text` for an ``hd`` substring.
    """

    candidates = [value or '', _extract_meta_text(item)]
    for text in candidates:
        if not text:
            continue
        if 'hd' in text.lower():
            return 'HD'
    return ''


def _is_video_item(item):
    """Return ``True`` when ``item`` contains a playable video link.

    Args:
        item: BeautifulSoup tag (or tag-like object) representing a candidate
            video entry.

    Returns:
        bool: ``True`` if the item has a hyperlink with an ``href`` attribute;
        ``False`` otherwise.
    """

    if not hasattr(item, 'select_one'):
        return False
    link = item.select_one('a[href]')
    if not link:
        return False
    href = utils.safe_get_attr(link, 'href', default='')
    return bool(href)


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Categories', site.img_search)
    # site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'video-list?lang=en&page=1')
    utils.eod()


@site.register()
def List(url):
    url = site.url[:-1] + url if url.startswith('/') else url
    url = url if 'page=' in url else url + '?page=1'

    listhtml = utils.getHtml(url, site.url)
    soup = utils.parse_html(listhtml)

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('justporn.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('justporn.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))
    selectors = {
        'base_url': site.url,
        'items': [
            'div.content',
            'div.video-item',
            'article.video-item'
        ],
        'filter': _is_video_item,
        'url': {'selector': 'a', 'attr': 'href'},
        'title': {
            'selector': 'h2 a',
            'fallback_selectors': ['a[title]', 'a'],
            'text': True,
            'clean': True
        },
        'thumbnail': {
            'selector': 'img',
            'attr': 'data-src',
            'fallback_attrs': ['src', 'data-lazy', 'data-original']
        },
        'duration': {
            'transform': _duration_transform
        },
        'quality': {
            'transform': _quality_transform
        }
    }
    utils.soup_videos_list(site, soup, selectors, play_mode='justporn.Playvid', contextm=cm)

    match = re.search(r'page=(\d+)', url, re.IGNORECASE)
    if match:
        cp = match.group(1)
        np = int(cp) + 1
        npurl = url.replace('page={}'.format(cp), 'page={}'.format(np))

        cm_page = (utils.addon_sys + "?mode=justporn.GotoPage&list_mode=justporn.List&url=" + urllib_parse.quote_plus(npurl) + "&np=" + str(np))
        cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]
        site.add_dir('[COLOR hotpink]Next Page...[/COLOR] ({0})'.format(np), npurl, 'List', site.img_next, contextm=cm)

    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp=0):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('justporn.List') + "&url=" + urllib_parse.quote_plus(url))
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
    soup = utils.parse_html(cathtml)

    categories = []
    if soup:
        for node in soup.select('div.filter.featured-category[data-val]'):
            data_val = utils.safe_get_attr(node, 'data-val', default='')
            if not data_val:
                continue
            name = utils.safe_get_text(node, default='', strip=True)
            name = utils.cleantext(name)
            if not name:
                continue
            categories.append((name, data_val))

    categories.sort(key=lambda item: item[0].lower())

    for name, data_val in categories:
        caturl = '{0}?page=1&category[]={1}'.format(site.url, data_val)
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)

    match = re.compile(r'<source src="([^"]+)" title="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        sources = {m[1]: site.url[:-1] + m[0].replace('&amp;', '&') for m in match}
        videourl = utils.prefquality(sources, reverse=True)
        if videourl:
            vp.play_from_direct_link(videourl)
    else:
        utils.notify('Oh Oh', 'No Videos found')


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", r'href="(/category/[^"]+)" style="cursor: pointer">\s*([^<]+)\s*</a', ''),
        ("Tag", r'href="(/tag/[^"]+)" style="cursor: pointer">\s*<i>#</i>([^<]+)\s*</a', '')
    ]

    lookupinfo = utils.LookupInfo('', url, 'justporn.List', lookup_list)
    lookupinfo.getinfo()
